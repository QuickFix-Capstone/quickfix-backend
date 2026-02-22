import os
import sys

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


def handler(event, context):
    payload = parse_ws_payload(event)
    action = payload.get("action") or "typing"
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

    is_typing = bool(data.get("isTyping", True))

    try:
        conv_response = conversations_table.get_item(
            Key={"userId": identity["app_user_id"], "conversationId": conversation_id}
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
    recipient_sub = get_user_cognito_sub_by_app_id(str(other_user_id), other_user_type or "customer")
    if recipient_sub:
        try:
            NotificationService().notify_typing(
                recipient_id=recipient_sub,
                sender_id=identity["app_user_id"],
                sender_name=identity["user_name"],
                conversation_id=conversation_id,
                is_typing=is_typing,
            )
        except Exception as exc:
            print(f"Failed to push typing event: {exc}")

    return ws_response(
        action,
        request_id,
        True,
        data={"conversationId": conversation_id, "isTyping": is_typing},
    )
