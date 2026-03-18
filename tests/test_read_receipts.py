import importlib.util
import os
import sys
from pathlib import Path


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


from src.utils.read_receipts import mark_messages_read
from src.utils.ws_notification_service import NotificationService


def _load_module(module_name: str, relative_path: str):
    module_path = Path(PROJECT_ROOT) / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeMessagesTable:
    def __init__(self, items):
        self._items = items
        self.updated = []

    def query(self, **kwargs):
        return {"Items": list(self._items)}

    def update_item(self, **kwargs):
        self.updated.append(kwargs)


def test_mark_messages_read_updates_only_unread_messages():
    table = FakeMessagesTable(
        [
            {"conversation_id": "conv-1", "ts": 1001, "readBy": ["sender-1"]},
            {"conversation_id": "conv-1", "ts": 1002, "readBy": ["sender-1", "reader-1"]},
            {"conversation_id": "conv-1", "ts": 1003},
        ]
    )

    last_read_message_id, read_at = mark_messages_read(table, "conv-1", "reader-1")

    assert last_read_message_id == "1003"
    assert isinstance(read_at, int)
    assert len(table.updated) == 2
    assert table.updated[0]["ExpressionAttributeValues"][":reader"] == ["reader-1"]
    assert table.updated[1]["ExpressionAttributeValues"][":reader"] == ["reader-1"]


def test_notify_read_receipt_includes_message_and_timestamp(monkeypatch):
    captured = {}

    def fake_notify_users(self, user_ids, payload):
        captured["user_ids"] = user_ids
        captured["payload"] = payload

    monkeypatch.setenv("WS_MANAGEMENT_ENDPOINT", "https://example.com")
    monkeypatch.setattr(NotificationService, "__init__", lambda self, table_name=None, endpoint=None: None)
    monkeypatch.setattr(NotificationService, "notify_users", fake_notify_users)

    service = NotificationService()
    service.notify_read_receipt(
        "recipient-sub",
        conversation_id="conv-1",
        read_by_user_id="reader-1",
        last_read_message_id="1003",
        read_at=1234567890,
    )

    assert captured["user_ids"] == ["recipient-sub"]
    assert captured["payload"]["event"] == "conversationRead"
    assert captured["payload"]["data"] == {
        "conversationId": "conv-1",
        "readByUserId": "reader-1",
        "lastReadMessageId": "1003",
        "readAt": 1234567890,
    }


def test_websocket_mark_read_returns_enriched_payload(monkeypatch):
    module = _load_module("ws_mark_read_handler", "lambda/websocket/mark_read/handler.py")

    monkeypatch.setattr(module, "get_cognito_sub_from_connection", lambda connection_id: "cognito-1")
    monkeypatch.setattr(
        module,
        "get_user_identity",
        lambda cognito_sub: {"app_user_id": "reader-1", "user_type": "customer", "user_name": "Reader"},
    )
    monkeypatch.setattr(module, "get_user_cognito_sub_by_app_id", lambda user_id, user_type: "recipient-sub")

    class FakeConversationsTable:
        def update_item(self, **kwargs):
            return {"Attributes": {"otherUserId": "sender-1", "otherUserType": "provider"}}

    notifications = {}

    class FakeNotificationService:
        def notify_read_receipt(self, recipient_id, **kwargs):
            notifications["recipient_id"] = recipient_id
            notifications["kwargs"] = kwargs

    monkeypatch.setattr(module, "conversations_table", FakeConversationsTable())
    monkeypatch.setattr(module, "messages_table", object())
    monkeypatch.setattr(module, "mark_messages_read", lambda *args, **kwargs: ("1003", 1234567890))
    monkeypatch.setattr(module, "NotificationService", lambda: FakeNotificationService())

    event = {
        "requestContext": {"connectionId": "conn-1"},
        "body": '{"action":"markRead","requestId":"req-1","data":{"conversationId":"conv-1"}}',
    }

    response = module.handler(event, None)

    assert response["statusCode"] == 200
    assert '"lastReadMessageId": "1003"' in response["body"]
    assert '"readAt": 1234567890' in response["body"]
    assert notifications["recipient_id"] == "recipient-sub"
    assert notifications["kwargs"]["conversation_id"] == "conv-1"
    assert notifications["kwargs"]["last_read_message_id"] == "1003"
    assert notifications["kwargs"]["read_at"] == 1234567890
