import json
import sys
import os
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.utils.ws_notification_service import NotificationService
    from src.utils.websocket_context import get_user_cognito_sub_by_app_id
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.ws_notification_service import NotificationService
    from src.utils.websocket_context import get_user_cognito_sub_by_app_id

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
    Mark a conversation as read (reset unread count to 0).
    
    Endpoint: PUT /messages/conversations/{conversationId}/read
    
    Authentication: JWT required
    
    Path Parameters:
    - conversationId: The conversation ID
    
    Response:
    {
        "conversationId": "550e8400-e29b-41d4-a716-446655440000",
        "unreadCount": 0,
        "message": "Conversation marked as read"
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

    # 3. Get user ID from MySQL
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

    # 4. Verify user is part of this conversation and mark as read
    try:
        # Update conversation to reset unread count
        response = conversations_table.update_item(
            Key={
                'userId': user_id,
                'conversationId': conversation_id
            },
            UpdateExpression='SET unreadCount = :zero',
            ExpressionAttributeValues={
                ':zero': 0
            },
            ConditionExpression='attribute_exists(userId)',  # Ensure conversation exists
            ReturnValues='ALL_NEW'
        )
        
        updated_conversation = response.get('Attributes', {})
        
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _response(403, {"message": "You are not part of this conversation"})
    except Exception as e:
        print(f"DynamoDB error: {e}")
        return _response(500, {"message": "Failed to mark conversation as read"})

    other_user_id = updated_conversation.get("otherUserId")
    other_user_type = updated_conversation.get("otherUserType")
    recipient_sub = get_user_cognito_sub_by_app_id(str(other_user_id), other_user_type or "customer")
    if recipient_sub:
        try:
            NotificationService().notify_read_receipt(
                recipient_sub,
                conversation_id=conversation_id,
                read_by_user_id=user_id,
            )
        except Exception as exc:
            print(f"Failed to send conversationRead websocket notification: {exc}")

    # 5. Return success response
    return _response(200, {
        "conversationId": conversation_id,
        "unreadCount": 0,
        "message": "Conversation marked as read"
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
        }
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
