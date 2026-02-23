import json
import sys
import os
import traceback
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
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
conversations_table = dynamodb.Table('quickfix_conversations')


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway response with CORS headers."""
    def _json_default(value: Any):
        if isinstance(value, Decimal):
            if value % 1 == 0:
                return int(value)
            return float(value)
        return str(value)

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body, default=_json_default),
    }

def _safe_int(value: Any, default: int = 0) -> int:
    """Convert DynamoDB/JSON values to int safely."""
    if value is None:
        return default
    try:
        if isinstance(value, str) and value.strip() == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

def _extract_cognito_sub(event: Dict[str, Any]) -> str:
    """
    Support both HTTP API JWT authorizer payload and REST API custom authorizer payloads.
    """
    request_context = event.get("requestContext", {}) or {}
    authorizer = request_context.get("authorizer", {}) or {}

    # HTTP API v2 JWT authorizer shape
    jwt_claims = (authorizer.get("jwt") or {}).get("claims") or {}
    if jwt_claims.get("sub"):
        return jwt_claims.get("sub")

    # REST API / Lambda authorizer shape
    legacy_claims = authorizer.get("claims") or {}
    if legacy_claims.get("sub"):
        return legacy_claims.get("sub")

    return ""


def handler(event, context):
    """
    List all conversations for the authenticated user.
    
    Endpoint: GET /messages/conversations
    
    Authentication: JWT required
    
    Query Parameters:
    - limit (optional): Max conversations to return (default 20, max 50)
    
    Response:
    {
        "conversations": [
            {
                "conversationId": "550e8400-e29b-41d4-a716-446655440000",
                "otherUser": {
                    "userId": "SP-ad86b044-9f9b-49b6-a53d-d3847afabe3c",
                    "name": "John Smith",
                    "type": "provider"
                },
                "jobId": "1001",
                "jobTitle": "Fix Kitchen Sink",
                "lastMessage": {
                    "preview": "I can start tomorrow at 9 AM",
                    "timestamp": 1704384000000
                },
                "unreadCount": 2,
                "createdAt": 1704380000000
            }
        ],
        "total": 5
    }
    """
    
    # 1. Extract JWT claims
    cognito_sub = _extract_cognito_sub(event)

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2. Get query parameters
    query_params = event.get("queryStringParameters") or {}
    try:
        limit = int(query_params.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    
    # Validate limit
    if limit < 1:
        limit = 20
    elif limit > 50:
        limit = 50

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
                
                user_id = str(user_row["provider_id"])

    except Exception as e:
        print(f"Database error: {e}")
        print(traceback.format_exc())
        return _response(500, {"message": "Database query failed"})
    finally:
        mysql_conn.close()

    # 4. Query DynamoDB for user's conversations
    try:
        response = conversations_table.query(
            KeyConditionExpression=Key('userId').eq(str(user_id))
        )
        
        conversations = response.get('Items', [])
        
        # Sort by lastMessageAt (most recent first)
        conversations.sort(key=lambda x: x.get('lastMessageAt', 0), reverse=True)
        
        # Limit results
        conversations = conversations[:limit]
        
        # Format response
        formatted_conversations = []
        for conv in conversations:
            formatted_conv = {
                "conversationId": conv.get('conversationId'),
                "otherUser": {
                    "userId": conv.get('otherUserId'),
                    "name": conv.get('otherUserName'),
                    "type": conv.get('otherUserType')
                },
                "jobId": conv.get('jobId'),
                "jobTitle": conv.get('jobTitle'),
                "lastMessage": {
                    "preview": conv.get('lastMessagePreview', ''),
                    "timestamp": _safe_int(conv.get('lastMessageAt'), 0)
                },
                "unreadCount": _safe_int(conv.get('unreadCount'), 0),
                "createdAt": _safe_int(conv.get('createdAt'), 0)
            }
            formatted_conversations.append(formatted_conv)

    except Exception as e:
        print(f"DynamoDB query error: {e}")
        print(f"user_id={user_id}, cognito_sub={cognito_sub}, query_params={query_params}")
        print(traceback.format_exc())
        return _response(500, {"message": "Failed to retrieve conversations"})

    # 5. Return response
    return _response(200, {
        "conversations": formatted_conversations,
        "total": len(formatted_conversations)
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
        "queryStringParameters": {
            "limit": "10"
        }
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
