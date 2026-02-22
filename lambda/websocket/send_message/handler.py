import json
import os
import sys
import time

import boto3

try:
    from src.utils.websocket_context import (
        get_cognito_sub_from_connection,
        get_user_cognito_sub_by_app_id,
        get_user_identity,
        parse_ws_payload,
        ws_response,
    )
    from src.utils.ws_notification_service import NotificationService
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.utils.websocket_context import (
        get_cognito_sub_from_connection,
        get_user_cognito_sub_by_app_id,
        get_user_identity,
        parse_ws_payload,
        ws_response,
    )
    from src.utils.ws_notification_service import NotificationService


dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
conversations_table = dynamodb.Table("quickfix_conversations")
messages_table = dynamodb.Table("quickfix_messages")


def handler(event, context):
    payload = parse_ws_payload(event)
    action = payload.get("action") or "sendMessage"
    request_id = payload.get("requestId")
    data = payload.get("data", {})

    connection_id = payload.get("connectionId")
    cognito_sub = get_cognito_sub_from_connection(connection_id)
    if not cognito_sub:
        return ws_response(action, request_id, False, error_code="UNAUTHORIZED", error_message="Unauthorized")

    identity = get_user_identity(cognito_sub)
    if not identity:
        return ws_response(action, request_id, False, error_code="USER_NOT_FOUND", error_message="User not found")

    conversation_id = data.get("conversationId")
    text = (data.get("text") or "").strip()
    if not conversation_id or not text:
        return ws_response(
            action,
            request_id,
            False,
            error_code="VALIDATION_ERROR",
            error_message="conversationId and text are required",
        )

    user_id = identity["app_user_id"]
    user_name = identity["user_name"]
    user_type = identity["user_type"]

    try:
        conv_response = conversations_table.get_item(
            Key={"userId": user_id, "conversationId": conversation_id}
        )
        conversation = conv_response.get("Item")
        if not conversation:
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

    other_user_id = conversation.get("otherUserId")
    other_user_type = conversation.get("otherUserType")

    timestamp = int(time.time() * 1000)
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    preview = text[:100] if len(text) > 100 else text

    try:
        messages_table.put_item(
            Item={
                "conversation_id": conversation_id,
                "ts": timestamp,
                "senderId": user_id,
                "senderName": user_name,
                "senderType": user_type,
                "text": text,
                "attachments": [],
                "readBy": [user_id],
                "createdAt": created_at,
            }
        )

        conversations_table.update_item(
            Key={"userId": user_id, "conversationId": conversation_id},
            UpdateExpression="SET lastMessageAt = :ts, lastMessagePreview = :preview",
            ExpressionAttributeValues={":ts": timestamp, ":preview": preview},
        )

        conversations_table.update_item(
            Key={"userId": other_user_id, "conversationId": conversation_id},
            UpdateExpression="SET lastMessageAt = :ts, lastMessagePreview = :preview, unreadCount = if_not_exists(unreadCount, :zero) + :inc",
            ExpressionAttributeValues={
                ":ts": timestamp,
                ":preview": preview,
                ":inc": 1,
                ":zero": 0,
            },
        )
    except Exception:
        return ws_response(
            action,
            request_id,
            False,
            error_code="DDB_ERROR",
            error_message="Failed to send message",
        )

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
            print(f"Failed to push newMessage notification: {exc}")

    return ws_response(
        action,
        request_id,
        True,
        data={
            "messageId": timestamp,
            "conversationId": conversation_id,
            "senderId": user_id,
            "senderName": user_name,
            "senderType": user_type,
            "text": text,
            "timestamp": timestamp,
            "createdAt": created_at,
        },
    )
