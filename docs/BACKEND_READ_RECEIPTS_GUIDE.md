# Backend: Message Read Receipts Implementation Guide

> **Goal**: When a user opens a conversation, mark individual messages as "read" in DynamoDB and notify the sender in real-time so the UI shows **"Read"** status.

---

## Current State

| What works | What's missing |
|---|---|
| `send_message` stores `readBy: [senderId]` per message | `mark_read` does NOT update `readBy` on messages |
| `get_messages` returns `readBy` array | Notification payload missing `lastReadMessageId` & `readAt` |
| `mark_read` resets `unreadCount` on conversation | Frontend `onReadReceipt` handler gets no `messageId` → exits early |

---

## Files to Modify

### 1. `lambda/websocket/mark_read/handler.py`

**Current behavior**: Only resets `unreadCount = 0` on `quickfix_conversations`.

**New behavior**: Also update `readBy` on each unread message in `quickfix_messages`, then pass the latest message ID and timestamp in the notification.

#### Full updated handler:

```python
import os
import sys
import time

import boto3
from boto3.dynamodb.conditions import Key, Attr

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
    action = payload.get("action") or "markRead"
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

    reader_user_id = identity["app_user_id"]

    # ── Step 1: Reset unreadCount on the conversation (existing) ──
    try:
        response = conversations_table.update_item(
            Key={"userId": reader_user_id, "conversationId": conversation_id},
            UpdateExpression="SET unreadCount = :zero",
            ExpressionAttributeValues={":zero": 0},
            ConditionExpression="attribute_exists(userId)",
            ReturnValues="ALL_NEW",
        )
        updated = response.get("Attributes", {})
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
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
            error_message="Failed to mark conversation as read",
        )

    # ── Step 2 (NEW): Update readBy on individual messages ──
    read_at = int(time.time() * 1000)
    last_read_message_id = None

    try:
        # Query messages in this conversation that the reader hasn't read yet
        msg_response = messages_table.query(
            KeyConditionExpression=Key("conversation_id").eq(conversation_id),
            ScanIndexForward=False,  # newest first
        )
        unread_messages = [
            msg for msg in msg_response.get("Items", [])
            if reader_user_id not in (msg.get("readBy") or [])
        ]

        # Add reader to readBy for each unread message
        for msg in unread_messages:
            messages_table.update_item(
                Key={
                    "conversation_id": conversation_id,
                    "ts": msg["ts"],
                },
                UpdateExpression="SET readBy = list_append(if_not_exists(readBy, :empty), :reader), readAt = :readAt",
                ExpressionAttributeValues={
                    ":reader": [reader_user_id],
                    ":empty": [],
                    ":readAt": read_at,
                },
            )

        # Track the newest message that was marked as read
        if unread_messages:
            last_read_message_id = str(max(int(msg["ts"]) for msg in unread_messages))

    except Exception as exc:
        # Log but don't fail — unreadCount was already reset
        print(f"Warning: failed to update readBy on messages: {exc}")

    # ── Step 3 (UPDATED): Notify the other user with messageId + readAt ──
    other_user_id = updated.get("otherUserId")
    other_user_type = updated.get("otherUserType")
    recipient_sub = get_user_cognito_sub_by_app_id(str(other_user_id), other_user_type or "customer")
    if recipient_sub:
        try:
            NotificationService().notify_read_receipt(
                recipient_sub,
                conversation_id=conversation_id,
                read_by_user_id=reader_user_id,
                last_read_message_id=last_read_message_id,
                read_at=read_at,
            )
        except Exception as exc:
            print(f"Failed to push read receipt: {exc}")

    return ws_response(
        action,
        request_id,
        True,
        data={
            "conversationId": conversation_id,
            "unreadCount": 0,
            "lastReadMessageId": last_read_message_id,
            "readAt": read_at,
        },
    )
```

---

### 2. `src/utils/ws_notification_service.py`

**Change**: Add `last_read_message_id` and `read_at` parameters to `notify_read_receipt`.

#### Updated method:

```python
def notify_read_receipt(
    self,
    recipient_id: str,
    conversation_id: str,
    read_by_user_id: str,
    last_read_message_id: str = None,
    read_at: int = None,
) -> None:
    payload = {
        "type": "event",
        "event": "conversationRead",
        "data": {
            "conversationId": conversation_id,
            "readByUserId": read_by_user_id,
            "lastReadMessageId": last_read_message_id,
            "readAt": read_at,
        },
    }
    self.notify_users([recipient_id], payload)
```

---

## DynamoDB Schema Reference

### `quickfix_messages` table

| Attribute | Type | Description |
|---|---|---|
| `conversation_id` | String (PK) | Conversation this message belongs to |
| `ts` | Number (SK) | Timestamp in milliseconds (also used as messageId) |
| `senderId` | String | User who sent the message |
| `senderName` | String | Display name of sender |
| `senderType` | String | `"customer"` or `"provider"` |
| `text` | String | Message content |
| `readBy` | List | Array of user IDs who have read this message |
| `readAt` | Number | *(NEW)* Timestamp (ms) when conversation was last marked read |
| `createdAt` | String | ISO 8601 creation time |

### `quickfix_conversations` table

| Attribute | Type | Description |
|---|---|---|
| `userId` | String (PK) | Owner of this conversation record |
| `conversationId` | String (SK) | Unique conversation identifier |
| `otherUserId` | String | The other participant's user ID |
| `otherUserType` | String | `"customer"` or `"provider"` |
| `unreadCount` | Number | Number of unread messages (reset to 0 on read) |

---

## WebSocket Notification Payload (Updated)

When a user reads a conversation, the **other user** receives:

```json
{
  "type": "event",
  "event": "conversationRead",
  "data": {
    "conversationId": "conv-abc-123",
    "readByUserId": "user-456",
    "lastReadMessageId": "1710799200000",
    "readAt": 1710799300000
  }
}
```

The frontend uses `lastReadMessageId` to mark all sent messages up to that point as **"Read"** in the UI.

---

## Deployment

After making changes, redeploy the two affected Lambdas:

```bash
# 1. Deploy mark_read Lambda
./deploy/deploy_websocket_mark_read.sh

# 2. Redeploy the notification service layer (if packaged separately)
#    Otherwise it's bundled with the Lambda above via src/utils import
```

---

## Testing Checklist

- [ ] Customer sends a message → message saved with `readBy: [customerId]`
- [ ] Provider opens conversation → `mark_read` fires → message `readBy` now includes `[customerId, providerId]`
- [ ] Customer receives `conversationRead` WebSocket event with `lastReadMessageId` and `readAt`
- [ ] Customer UI updates message status from "Sent" → "Read"
- [ ] On page refresh, `get_messages` returns correct `readBy` array (persistence check)
- [ ] Read receipts work bidirectionally (provider → customer and customer → provider)
