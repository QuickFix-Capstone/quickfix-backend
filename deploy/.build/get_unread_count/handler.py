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
    Get count of unread notifications for user.
    
    Endpoint: GET /notifications/unread-count
    
    Authentication: JWT required
    
    Response:
    {
        "unreadCount": 5
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

    # 2. Query all notifications for this user and count unread
    try:
        # Query all notifications for this user
        response = notifications_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_sub').eq(user_sub),
            FilterExpression=boto3.dynamodb.conditions.Attr('is_read').eq(False),
            Select='COUNT'  # Only return count, not items
        )
        
        unread_count = response.get('Count', 0)
        
        # Handle pagination if there are many notifications
        while 'LastEvaluatedKey' in response:
            response = notifications_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_sub').eq(user_sub),
                FilterExpression=boto3.dynamodb.conditions.Attr('is_read').eq(False),
                Select='COUNT',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            unread_count += response.get('Count', 0)
        
        return _response(200, {
            "unreadCount": unread_count
        })
        
    except Exception as e:
        print(f"Error counting unread notifications: {e}")
        import traceback
        traceback.print_exc()
        return _response(500, {"message": "Failed to count unread notifications"})


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
        }
    }
    
    result = handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
