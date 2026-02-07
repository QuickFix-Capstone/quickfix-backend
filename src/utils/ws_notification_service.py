import json
import os

import boto3
from boto3.dynamodb.conditions import Key


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


class NotificationService:
    def __init__(self, table_name: str | None = None, endpoint: str | None = None):
        self.table_name = table_name or _get_env("WS_CONNECTIONS_TABLE", "quickfix-ws-connections")
        self.endpoint = endpoint or _get_env("WS_MANAGEMENT_ENDPOINT")
        if not self.endpoint:
            raise RuntimeError("Missing WS_MANAGEMENT_ENDPOINT")

        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(self.table_name)
        self._ws_client = boto3.client("apigatewaymanagementapi", endpoint_url=self.endpoint)

    def notify_users(self, user_ids: list[str], payload: dict) -> None:
        message = json.dumps(payload)
        for user_id in user_ids:
            self._notify_user(user_id, message)

    def _notify_user(self, user_id: str, message: str) -> None:
        resp = self._table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
        )
        items = resp.get("Items", [])
        for item in items:
            connection_id = item["connectionId"]
            try:
                self._ws_client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=message.encode("utf-8"),
                )
            except self._ws_client.exceptions.GoneException:
                self._delete_connection(item)
            except Exception:
                # Fail soft: do not break caller flow.
                continue

    def _delete_connection(self, item: dict) -> None:
        try:
            self._table.delete_item(
                Key={
                    "userId": item["userId"],
                    "connectionId": item["connectionId"],
                }
            )
        except Exception:
            pass
