import json
import sys
import os
from typing import Any, Dict
from decimal import Decimal

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
messages_table = dynamodb.Table('quickfix_messages')


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
    List all messages in a conversation.
    
    Endpoint: GET /messages/{conversationId}
    
    Authentication: JWT required
    
    Path Parameters:
    - conversationId: The conversation ID
    
    Query Parameters:
    - limit (optional): Max messages to return (default 50, max 100)
    - before (optional): Timestamp to get messages before (for pagination)
    
    Response:
    {
        "messages": [
            {
                "messageId": 1704384000000,
                "senderId": "2",
                "senderName": "KunPeng Yang",
                "senderType": "customer",
                "text": "Hello, when can you start?",
                "timestamp": 1704384000000,
                "readBy": ["2"],
                "createdAt": "2026-01-04T14:00:00Z"
            }
        ],
        "total": 10,
        "hasMore": false
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

    # 2. Get path parameters
    path_params = event.get("pathParameters") or {}
    conversation_id = path_params.get("conversationId")
    
    if not conversation_id:
        return _response(400, {"message": "conversationId is required"})

    # 3. Get query parameters
    query_params = event.get("queryStringParameters") or {}
    limit = int(query_params.get("limit", 50))
    before = query_params.get("before")  # Timestamp to get messages before
    
    # Validate limit
    if limit < 1:
        limit = 50
    elif limit > 100:
        limit = 100

    # 4. Get user ID from MySQL
    mysql_conn = get_connection()
    if not mysql_conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with mysql_conn.cursor() as cur:
            # Check if customer
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            user_row = cur.fetchone()
            
            if user_row:
                user_id = str(user_row["customer_id"])
            else:
                # Check if provider
                cur.execute(
                    "SELECT provider_id FROM service_providers WHERE cognito_sub = %s",
                    (cognito_sub,)
                )
                user_row = cur.fetchone()
                
                if not user_row:
                    return _response(404, {"message": "User not found"})
                
                user_id = user_row["provider_id"]

    except Exception as e:
        print(f"Database error: {e}")
        return _response(500, {"message": "Database query failed"})
    finally:
        mysql_conn.close()

    # 5. Verify user is part of this conversation
    try:
        conv_response = conversations_table.get_item(
            Key={
                'userId': user_id,
                'conversationId': conversation_id
            }
        )
        
        if 'Item' not in conv_response:
            return _response(403, {"message": "You are not part of this conversation"})
        
    except Exception as e:
        print(f"DynamoDB error checking conversation: {e}")
        return _response(500, {"message": "Failed to verify conversation"})

    # 6. Query messages
    try:
        # Build query
        if before:
            # Get messages before a specific timestamp (pagination)
            response = messages_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('conversation_id').eq(conversation_id) & 
                                      boto3.dynamodb.conditions.Key('ts').lt(int(before)),
                ScanIndexForward=False,  # Newest first
                Limit=limit + 1  # Get one extra to check if there are more
            )
        else:
            # Get latest messages
            response = messages_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('conversation_id').eq(conversation_id),
                ScanIndexForward=False,  # Newest first
                Limit=limit + 1  # Get one extra to check if there are more
            )
        
        messages = response.get('Items', [])
        
        # Check if there are more messages
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]  # Remove the extra message
        
        # Format response - convert Decimal to int
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "messageId": int(msg.get('ts')),
                "senderId": msg.get('senderId'),
                "senderName": msg.get('senderName'),
                "senderType": msg.get('senderType'),
                "text": msg.get('text'),
                "timestamp": int(msg.get('ts')),
                "readBy": msg.get('readBy', []),
                "createdAt": msg.get('createdAt')
            }
            
            # Add attachments if present
            if msg.get('attachments'):
                formatted_msg['attachments'] = msg.get('attachments')
            
            formatted_messages.append(formatted_msg)

    except Exception as e:
        print(f"DynamoDB query error: {e}")
        return _response(500, {"message": "Failed to retrieve messages"})

    # 7. Return response
    return _response(200, {
        "messages": formatted_messages,
        "total": len(formatted_messages),
        "hasMore": has_more
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
        "pathParameters": {
            "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd"
        },
        "queryStringParameters": {
            "limit": "50"
        }
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
