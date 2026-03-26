import time
from decimal import Decimal
from typing import Optional

from boto3.dynamodb.conditions import Key


def mark_messages_read(messages_table, conversation_id: str, reader_user_id: str) -> tuple[Optional[str], int]:
    """
    Mark all unread messages in a conversation as read by the given user.

    Returns the newest message ID marked as read and the read timestamp in ms.
    """
    read_at = int(time.time() * 1000)
    unread_messages = []

    query_kwargs = {
        "KeyConditionExpression": Key("conversation_id").eq(conversation_id),
        "ScanIndexForward": False,
    }

    while True:
        response = messages_table.query(**query_kwargs)
        items = response.get("Items", [])
        unread_messages.extend(
            msg for msg in items
            if reader_user_id not in (msg.get("readBy") or [])
        )

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break
        query_kwargs["ExclusiveStartKey"] = last_evaluated_key

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

    if not unread_messages:
        return None, read_at

    last_read_message_id = str(
        max(
            int(msg["ts"]) if isinstance(msg["ts"], Decimal) else int(msg["ts"])
            for msg in unread_messages
        )
    )
    return last_read_message_id, read_at
