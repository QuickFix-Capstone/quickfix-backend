import json
import os
from typing import Any, Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key

from src.db.rds_main import get_connection


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def parse_ws_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    body_raw = event.get("body") or "{}"
    if isinstance(body_raw, dict):
        body = body_raw
    else:
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            body = {}

    return {
        "action": body.get("action"),
        "requestId": body.get("requestId"),
        "data": body.get("data") or {},
        "connectionId": event.get("requestContext", {}).get("connectionId"),
    }


def ws_response(
    action: str,
    request_id: Optional[str],
    success: bool,
    data: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "type": "response",
        "action": action,
        "requestId": request_id,
        "success": success,
    }
    if success:
        payload["data"] = data or {}
    else:
        payload["error"] = {
            "code": error_code or "REQUEST_FAILED",
            "message": error_message or "Request failed",
        }
    return {"statusCode": 200, "body": json.dumps(payload)}


def get_cognito_sub_from_connection(connection_id: Optional[str]) -> Optional[str]:
    if not connection_id:
        return None

    table_name = _get_env("WS_CONNECTIONS_TABLE", "quickfix-ws-connections")
    table = boto3.resource("dynamodb").Table(table_name)

    try:
        resp = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("connectionId").eq(connection_id),
        )
        items = resp.get("Items", [])
        if not items:
            return None
        return items[0].get("userId")
    except Exception:
        return None


def get_user_identity(cognito_sub: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT customer_id, first_name, last_name FROM customers WHERE cognito_sub = %s",
                (cognito_sub,),
            )
            customer = cur.fetchone()
            if customer:
                return {
                    "cognito_sub": cognito_sub,
                    "app_user_id": str(customer["customer_id"]),
                    "user_type": "customer",
                    "user_name": f"{customer['first_name']} {customer['last_name']}".strip(),
                }

            cur.execute(
                "SELECT provider_id, name FROM service_providers WHERE cognito_sub = %s",
                (cognito_sub,),
            )
            provider = cur.fetchone()
            if provider:
                return {
                    "cognito_sub": cognito_sub,
                    "app_user_id": provider["provider_id"],
                    "user_type": "provider",
                    "user_name": provider["name"],
                }
    except Exception:
        return None
    finally:
        conn.close()

    return None


def get_user_cognito_sub_by_app_id(user_id: str, user_type: str) -> Optional[str]:
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            if user_type == "provider":
                cur.execute(
                    "SELECT cognito_sub FROM service_providers WHERE provider_id = %s",
                    (user_id,),
                )
            else:
                cur.execute(
                    "SELECT cognito_sub FROM customers WHERE customer_id = %s",
                    (user_id,),
                )

            row = cur.fetchone()
            return row.get("cognito_sub") if row else None
    except Exception:
        return None
    finally:
        conn.close()
