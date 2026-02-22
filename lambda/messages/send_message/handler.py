import json
import sys
import os
import time
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import track_provider_interaction
    from src.utils.ws_notification_service import NotificationService
    from src.utils.websocket_context import get_user_cognito_sub_by_app_id
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import track_provider_interaction
    from src.utils.ws_notification_service import NotificationService
    from src.utils.websocket_context import get_user_cognito_sub_by_app_id

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
    Send a message in a conversation.
    
    Endpoint: POST /messages
    
    Authentication: JWT required
    
    Request Body:
    {
        "conversationId": "550e8400-e29b-41d4-a716-446655440000",
        "text": "Hello, when can you start?"
    }
    
    Response:
    {
        "messageId": 1704384000000,
        "conversationId": "550e8400-e29b-41d4-a716-446655440000",
        "senderId": "2",
        "senderName": "KunPeng Yang",
        "senderType": "customer",
        "text": "Hello, when can you start?",
        "timestamp": 1704384000000,
        "createdAt": "2026-01-04T14:00:00Z"
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
    conversation_id = body.get("conversationId")
    text = body.get("text")
    
    if not conversation_id:
        return _response(400, {"message": "conversationId is required"})
    
    if not text or not text.strip():
        return _response(400, {"message": "text is required and cannot be empty"})

    # 4. Get user info from MySQL
    mysql_conn = get_connection()
    if not mysql_conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with mysql_conn.cursor() as cur:
            # Check if customer
            cur.execute(
                "SELECT customer_id, first_name, last_name FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            user_row = cur.fetchone()
            
            if user_row:
                user_id = str(user_row["customer_id"])
                user_name = f"{user_row['first_name']} {user_row['last_name']}"
                user_type = "customer"
            else:
                # Check if provider
                cur.execute(
                    "SELECT provider_id, name FROM service_providers WHERE cognito_sub = %s",
                    (cognito_sub,)
                )
                user_row = cur.fetchone()
                
                if not user_row:
                    return _response(404, {"message": "User not found"})
                
                user_id = user_row["provider_id"]
                user_name = user_row["name"]
                user_type = "provider"

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
        
        conversation = conv_response['Item']
        other_user_id = conversation.get('otherUserId')
        other_user_type = conversation.get("otherUserType")

    except Exception as e:
        print(f"DynamoDB error checking conversation: {e}")
        return _response(500, {"message": "Failed to verify conversation"})

    if user_type == "provider":
        try:
            customer_id = int(str(other_user_id))
            track_conn = get_connection()
            if track_conn:
                try:
                    track_provider_interaction(
                        conn=track_conn,
                        provider_id=user_id,
                        customer_id=customer_id,
                        interaction_type="message",
                    )
                finally:
                    track_conn.close()
        except Exception:
            pass

    # 6. Create message
    timestamp = int(time.time() * 1000)
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # Truncate preview to 100 characters
    preview = text[:100] if len(text) > 100 else text
    
    try:
        # Add message to messages table
        messages_table.put_item(
            Item={
                'conversation_id': conversation_id,
                'ts': timestamp,
                'senderId': user_id,
                'senderName': user_name,
                'senderType': user_type,
                'text': text,
                'attachments': [],
                'readBy': [user_id],  # Sender has read it
                'createdAt': created_at
            }
        )
        
        # Update sender's conversation (no unread count change)
        conversations_table.update_item(
            Key={
                'userId': user_id,
                'conversationId': conversation_id
            },
            UpdateExpression='SET lastMessageAt = :ts, lastMessagePreview = :preview',
            ExpressionAttributeValues={
                ':ts': timestamp,
                ':preview': preview
            }
        )
        
        # Update recipient's conversation (increment unread count)
        conversations_table.update_item(
            Key={
                'userId': other_user_id,
                'conversationId': conversation_id
            },
            UpdateExpression='SET lastMessageAt = :ts, lastMessagePreview = :preview, unreadCount = unreadCount + :inc',
            ExpressionAttributeValues={
                ':ts': timestamp,
                ':preview': preview,
                ':inc': 1
            }
        )
        
    except Exception as e:
        print(f"DynamoDB error sending message: {e}")
        return _response(500, {"message": "Failed to send message"})

    # 7. Return success response
    recipient_sub = get_user_cognito_sub_by_app_id(str(other_user_id), other_user_type or "customer")
    if recipient_sub:
        try:
            NotificationService().notify_new_message(
                recipient_sub,
                {
                    "conversationId": conversation_id,
                    "messageId": timestamp,
                    "senderId": user_id,
                    "senderName": user_name,
                    "senderType": user_type,
                    "text": text,
                    "timestamp": timestamp,
                    "createdAt": created_at,
                },
            )
        except Exception as exc:
            print(f"Failed to send newMessage websocket notification: {exc}")

    return _response(201, {
        "messageId": timestamp,
        "conversationId": conversation_id,
        "senderId": user_id,
        "senderName": user_name,
        "senderType": user_type,
        "text": text,
        "timestamp": timestamp,
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
            "conversationId": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
            "text": "Hello, when can you start?"
        })
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
