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
messages_table = dynamodb.Table("quickfix_messages")


def handler(event, context):
    payload = parse_ws_payload(event)
    action = payload.get("action") or "getMessages"
    request_id = payload.get("requestId")
    data = payload.get("data", {})

    cognito_sub = get_cognito_sub_from_connection(payload.get("connectionId"))
    if not cognito_sub:
        return ws_response(action, request_id, False, error_code="UNAUTHORIZED", error_message="Unauthorized")

    identity = get_user_identity(cognito_sub)
    if not identity:
        return ws_response(action, request_id, False, error_code="USER_NOT_FOUND", error_message="User not found")

    conversation_id = data.get("conversationId")
    if not conversation_id:
        return ws_response(
            action,
            request_id,
            False,
            error_code="VALIDATION_ERROR",
            error_message="conversationId is required",
        )

    try:
        limit = int(data.get("limit", 50))
    except Exception:
        limit = 50
    limit = max(1, min(limit, 100))

    before = data.get("before")
    before_ts = None
    if before is not None:
        try:
            before_ts = int(before)
        except Exception:
            return ws_response(
                action,
                request_id,
                False,
                error_code="VALIDATION_ERROR",
                error_message="before must be a timestamp",
            )

    try:
        conv_response = conversations_table.get_item(
            Key={"userId": identity["app_user_id"], "conversationId": conversation_id}
        )
        if "Item" not in conv_response:
            return ws_response(
                action,
                request_id,
                False,
                error_code="FORBIDDEN",
                error_message="You are not part of this conversation",
            )
    except Exception:
        return ws_response(
            action,
            request_id,
            False,
            error_code="DDB_ERROR",
            error_message="Failed to verify conversation",
        )

    try:
        query_args = {
            "KeyConditionExpression": Key("conversation_id").eq(conversation_id),
            "ScanIndexForward": False,
            "Limit": limit + 1,
        }
        if before_ts is not None:
            query_args["KeyConditionExpression"] = Key("conversation_id").eq(conversation_id) & Key("ts").lt(before_ts)

        response = messages_table.query(**query_args)
        messages = response.get("Items", [])
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        formatted_messages = []
        for msg in messages:
            formatted = {
                "messageId": int(msg.get("ts")),
                "senderId": msg.get("senderId"),
                "senderName": msg.get("senderName"),
                "senderType": msg.get("senderType"),
                "text": msg.get("text"),
                "timestamp": int(msg.get("ts")),
                "readBy": msg.get("readBy", []),
                "createdAt": msg.get("createdAt"),
            }
            if msg.get("attachments"):
                formatted["attachments"] = msg.get("attachments")
            formatted_messages.append(formatted)
    except Exception:
        return ws_response(
            action,
            request_id,
            False,
            error_code="DDB_ERROR",
            error_message="Failed to retrieve messages",
        )

    return ws_response(
        action,
        request_id,
        True,
        data={"messages": formatted_messages, "total": len(formatted_messages), "hasMore": has_more},
    )
