import json
import sys
import os
import uuid
import time
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection

import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
conversations_table = dynamodb.Table('quickfix_conversations')


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Create a new conversation between two users.
    
    Endpoint: POST /messages/conversations
    
    Authentication: JWT required
    
    Request Body:
    {
        "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
        "jobId": "1001"  // optional
    }
    
    Response:
    {
        "conversationId": "550e8400-e29b-41d4-a716-446655440000",
        "otherUser": {
            "userId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
            "name": "John Smith",
            "type": "provider"
        },
        "jobId": "1001",
        "createdAt": 1704380000000
    }
    """
    
    # 1. Extract JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2. Parse request body
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
    except json.JSONDecodeError:
        return _response(400, {"message": "Invalid JSON body"})

    # 3. Validate required fields
    other_user_id = body.get("otherUserId")
    if not other_user_id:
        return _response(400, {"message": "otherUserId is required"})

    job_id = body.get("jobId")  # Optional

    # 4. Connect to MySQL to get user information
    mysql_conn = get_connection()
    if not mysql_conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with mysql_conn.cursor() as cur:
            # Get current user info
            cur.execute(
                "SELECT customer_id, first_name, last_name FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            current_user_row = cur.fetchone()
            
            if not current_user_row:
                # Try service providers table
                cur.execute(
                    "SELECT provider_id, name FROM service_providers WHERE cognito_sub = %s",
                    (cognito_sub,)
                )
                current_user_row = cur.fetchone()
                
                if not current_user_row:
                    return _response(404, {"message": "Current user not found"})
                
                current_user_type = "provider"
                current_user_name = current_user_row["name"]
                user_id = current_user_row["provider_id"]
            else:
                current_user_type = "customer"
                current_user_name = f"{current_user_row['first_name']} {current_user_row['last_name']}"
                user_id = str(current_user_row["customer_id"])

            # Get other user info
            # Check if it's a customer ID (numeric) or provider ID (SP-xxx)
            if other_user_id.startswith("SP-"):
                # It's a provider
                cur.execute(
                    "SELECT provider_id, name FROM service_providers WHERE provider_id = %s",
                    (other_user_id,)
                )
                other_user_row = cur.fetchone()
                
                if not other_user_row:
                    return _response(404, {"message": f"Provider {other_user_id} not found"})
                
                other_user_type = "provider"
                other_user_name = other_user_row["name"]
            else:
                # It's a customer
                cur.execute(
                    "SELECT customer_id, first_name, last_name FROM customers WHERE customer_id = %s",
                    (other_user_id,)
                )
                other_user_row = cur.fetchone()
                
                if not other_user_row:
                    return _response(404, {"message": f"Customer {other_user_id} not found"})
                
                other_user_type = "customer"
                other_user_name = f"{other_user_row['first_name']} {other_user_row['last_name']}"

            # Get job info if provided
            job_title = None
            if job_id:
                cur.execute(
                    "SELECT title FROM jobs WHERE job_id = %s",
                    (job_id,)
                )
                job_row = cur.fetchone()
                if job_row:
                    job_title = job_row["title"]

    except Exception as e:
        print(f"Database error: {e}")
        return _response(500, {"message": "Database query failed"})
    finally:
        mysql_conn.close()

    # 5. Check if conversation already exists
    try:
        # Query current user's conversations to see if one exists with other user
        response = conversations_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id)
        )
        
        existing_conv = None
        for item in response.get('Items', []):
            if item.get('otherUserId') == other_user_id:
                # Check if job matches (if provided)
                if job_id:
                    if item.get('jobId') == job_id:
                        existing_conv = item
                        break
                else:
                    # No job specified, return first conversation with this user
                    existing_conv = item
                    break
        
        if existing_conv:
            # Conversation already exists, return it
            return _response(200, {
                "conversationId": existing_conv['conversationId'],
                "otherUser": {
                    "userId": other_user_id,
                    "name": other_user_name,
                    "type": other_user_type
                },
                "jobId": existing_conv.get('jobId'),
                "jobTitle": existing_conv.get('jobTitle'),
                "createdAt": existing_conv.get('createdAt'),
                "message": "Conversation already exists"
            })

    except Exception as e:
        print(f"DynamoDB query error: {e}")
        # Continue to create new conversation

    # 6. Create new conversation
    conversation_id = str(uuid.uuid4())
    created_at = int(time.time() * 1000)  # Current timestamp in milliseconds

    try:
        # Create row for current user
        conversations_table.put_item(
            Item={
                'userId': user_id,
                'conversationId': conversation_id,
                'otherUserId': other_user_id,
                'otherUserName': other_user_name,
                'otherUserType': other_user_type,
                'jobId': job_id if job_id else None,
                'jobTitle': job_title if job_title else None,
                'lastMessageAt': 0,
                'lastMessagePreview': '',
                'unreadCount': 0,
                'createdAt': created_at
            }
        )

        # Create row for other user
        conversations_table.put_item(
            Item={
                'userId': other_user_id,
                'conversationId': conversation_id,
                'otherUserId': user_id,
                'otherUserName': current_user_name,
                'otherUserType': current_user_type,
                'jobId': job_id if job_id else None,
                'jobTitle': job_title if job_title else None,
                'lastMessageAt': 0,
                'lastMessagePreview': '',
                'unreadCount': 0,
                'createdAt': created_at
            }
        )

    except Exception as e:
        print(f"DynamoDB write error: {e}")
        return _response(500, {"message": "Failed to create conversation"})

    # 7. Return success response
    return _response(201, {
        "conversationId": conversation_id,
        "otherUser": {
            "userId": other_user_id,
            "name": other_user_name,
            "type": other_user_type
        },
        "jobId": job_id,
        "jobTitle": job_title,
        "createdAt": created_at
    })


# Local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "body": json.dumps({
            "otherUserId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
            "jobId": "1001"
        })
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
