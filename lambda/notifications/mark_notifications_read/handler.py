import json
from typing import Any, Dict

import boto3

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
    Mark notifications as read.
    
    Endpoint: POST /notifications/mark-read
    
    Authentication: JWT required
    
    Request Body:
    {
        "items": [
            {"notif_sort": "NOTIF#2026-01-05T10:00:00Z#MSG#1767581062206"},
            {"notif_sort": "NOTIF#2026-01-05T09:55:00Z#MSG#1767580900000"}
        ]
    }
    
    Response:
    {
        "updated": 2,
        "message": "Notifications marked as read"
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

    # 2. Parse request body
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
    except json.JSONDecodeError:
        return _response(400, {"message": "Invalid JSON body"})

    # 3. Validate required fields
    items = body.get("items", [])
    
    if not items:
        return _response(400, {"message": "items array is required"})
    
    if not isinstance(items, list):
        return _response(400, {"message": "items must be an array"})

    # 4. Update each notification
    updated_count = 0
    errors = []
    
    for item in items:
        notif_sort = item.get("notif_sort")
        
        if not notif_sort:
            errors.append({"error": "Missing notif_sort", "item": item})
            continue
        
        try:
            # Update the notification
            # Use ConditionExpression to ensure user owns this notification
            notifications_table.update_item(
                Key={
                    'user_sub': user_sub,
                    'notif_sort': notif_sort
                },
                UpdateExpression='SET is_read = :true',
                ExpressionAttributeValues={
                    ':true': True
                },
                ConditionExpression='attribute_exists(user_sub)'  # Ensure notification exists
            )
            
            updated_count += 1
            
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # Notification doesn't exist or doesn't belong to user
            errors.append({
                "error": "Notification not found or access denied",
                "notif_sort": notif_sort
            })
        except Exception as e:
            print(f"Error updating notification {notif_sort}: {e}")
            errors.append({
                "error": str(e),
                "notif_sort": notif_sort
            })

    # 5. Return response
    response = {
        "updated": updated_count,
        "message": f"{updated_count} notification(s) marked as read"
    }
    
    if errors:
        response["errors"] = errors
    
    return _response(200, response)


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
        "body": json.dumps({
            "items": [
                {"notif_sort": "NOTIF#2026-01-06T00:39:49.241538Z#MSG#1767659987428"}
            ]
        })
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
