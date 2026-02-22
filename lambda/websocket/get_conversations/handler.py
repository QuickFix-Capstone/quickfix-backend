import os
import sys

import boto3
from boto3.dynamodb.conditions import Key

try:
    from src.utils.websocket_context import (
        get_cognito_sub_from_connection,
        get_user_identity,
        parse_ws_payload,
        ws_response,
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.utils.websocket_context import (
        get_cognito_sub_from_connection,
        get_user_identity,
        parse_ws_payload,
        ws_response,
    )


dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
conversations_table = dynamodb.Table("quickfix_conversations")


def handler(event, context):
    payload = parse_ws_payload(event)
    action = payload.get("action") or "getConversations"
    request_id = payload.get("requestId")
    data = payload.get("data", {})

    cognito_sub = get_cognito_sub_from_connection(payload.get("connectionId"))
    if not cognito_sub:
        return ws_response(action, request_id, False, error_code="UNAUTHORIZED", error_message="Unauthorized")

    identity = get_user_identity(cognito_sub)
    if not identity:
        return ws_response(action, request_id, False, error_code="USER_NOT_FOUND", error_message="User not found")

    try:
        limit = int(data.get("limit", 20))
    except Exception:
        limit = 20
    limit = max(1, min(limit, 50))

    try:
        response = conversations_table.query(
            KeyConditionExpression=Key("userId").eq(identity["app_user_id"])
        )
        conversations = response.get("Items", [])
        conversations.sort(key=lambda x: x.get("lastMessageAt", 0), reverse=True)
        conversations = conversations[:limit]

        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append(
                {
                    "conversationId": conv.get("conversationId"),
                    "otherUser": {
                        "userId": conv.get("otherUserId"),
                        "name": conv.get("otherUserName"),
                        "type": conv.get("otherUserType"),
                    },
                    "jobId": conv.get("jobId"),
                    "jobTitle": conv.get("jobTitle"),
                    "lastMessage": {
                        "preview": conv.get("lastMessagePreview", ""),
                        "timestamp": int(conv.get("lastMessageAt", 0)),
                    },
                    "unreadCount": int(conv.get("unreadCount", 0)),
                    "createdAt": int(conv.get("createdAt", 0)),
                }
            )
    except Exception:
        return ws_response(
            action,
            request_id,
            False,
            error_code="DDB_ERROR",
            error_message="Failed to retrieve conversations",
        )

    return ws_response(
        action,
        request_id,
        True,
        data={"conversations": formatted_conversations, "total": len(formatted_conversations)},
    )
