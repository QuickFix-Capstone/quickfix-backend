import json
import os

import boto3
from boto3.dynamodb.conditions import Key


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def handler(event, context):
    table_name = _get_env("WS_CONNECTIONS_TABLE", "quickfix-ws-connections")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    connection_id = event.get("requestContext", {}).get("connectionId")
    if not connection_id:
        return {"statusCode": 200, "body": json.dumps({"message": "no connectionId"})}

    try:
        resp = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("connectionId").eq(connection_id),
        )
        items = resp.get("Items", [])
        for item in items:
            table.delete_item(
                Key={
                    "userId": item["userId"],
                    "connectionId": item["connectionId"],
                }
            )
    except Exception as exc:
        return {"statusCode": 200, "body": json.dumps({"message": "disconnect error", "error": str(exc)})}

    return {"statusCode": 200, "body": json.dumps({"message": "disconnected"})}
