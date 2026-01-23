import json
import sys
import os
from typing import Any, Dict

import boto3
import base64

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
notifications_table = dynamodb.Table('quickfix_notifications')



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
    List user's notifications with pagination.
    
    Endpoint: GET /notifications/my?limit=20&nextToken=...
    
    Authentication: JWT required
    
    Query Parameters:
    - limit (optional): Max notifications to return (default 20, max 50)
    - nextToken (optional): Pagination token from previous response
    
    Response:
    {
        "notifications": [
            {
                "notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206",
                "type": "NEW_MESSAGE",
                "conversation_id": "a103818f-ed02-4f47-9dd3-def9e2a5bfcd",
                "from_name": "walter",
                "preview": "Hello, when can you start?",
                "created_at": "2026-01-05T10:00:00Z",
                "is_read": false,
                "message_id": 1767581062206
            }
        ],
        "nextToken": "eyJ...",
        "total": 1
    }
    """
    
    # 1. Extract JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        user_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not user_sub:
        return _response(401, {"message": "Unauthorized: Missing user_sub"})

    # 2. Get query parameters
    query_params = event.get("queryStringParameters") or {}
    limit = int(query_params.get("limit", 20))
    next_token = query_params.get("nextToken")
    
    # Validate limit
    if limit < 1:
        limit = 20
    elif limit > 50:
        limit = 50

    # 3. Query notifications for this user
    try:
        query_params = {
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('user_sub').eq(user_sub),
            'ScanIndexForward': False,  # Sort by SK descending (newest first)
            'Limit': limit
        }
        
        # Add pagination token if provided
        if next_token:
            try:
                # Decode the nextToken (it's base64 encoded LastEvaluatedKey)
                decoded_token = base64.b64decode(next_token).decode('utf-8')
                exclusive_start_key = json.loads(decoded_token)
                query_params['ExclusiveStartKey'] = exclusive_start_key
            except Exception as e:
                print(f"Invalid nextToken: {e}")
                return _response(400, {"message": "Invalid nextToken"})
        
        response = notifications_table.query(**query_params)
        
        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        # Format notifications
        notifications = []
        for item in items:
            notification = {
                "notif_sort": item.get('notif_sort'),
                "type": item.get('type'),
                "conversation_id": item.get('conversation_id'),
                "from_name": item.get('from_name'),
                "preview": item.get('preview'),
                "created_at": item.get('created_at'),
                "is_read": item.get('is_read', False),
                "message_id": int(item.get('message_id', 0))
            }
            
            # Add optional fields if present
            if item.get('from_sub'):
                notification['from_sub'] = item.get('from_sub')
            
            notifications.append(notification)
        
        # Create response
        result = {
            "notifications": notifications,
            "total": len(notifications)
        }
        
        # Add nextToken if there are more results
        if last_evaluated_key:
            # Encode the LastEvaluatedKey as base64
            token_str = json.dumps(last_evaluated_key)
            encoded_token = base64.b64encode(token_str.encode('utf-8')).decode('utf-8')
            result['nextToken'] = encoded_token
        
        return _response(200, result)
        
    except Exception as e:
        print(f"Error querying notifications: {e}")
        import traceback
        traceback.print_exc()
        return _response(500, {"message": "Failed to retrieve notifications"})


# Local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "510ba500-c021-70c2-f03e-590fd18ca5ad"
                    }
                }
            }
        },
        "queryStringParameters": {
            "limit": "20"
        }
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
