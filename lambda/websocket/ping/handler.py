import json
import os
import time

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
    if connection_id:
        try:
            resp = table.query(
                IndexName="GSI1",
                KeyConditionExpression=Key("connectionId").eq(connection_id),
            )
            items = resp.get("Items", [])
            if items:
                item = items[0]
                ttl = int(time.time()) + 7200
                table.update_item(
                    Key={
                        "userId": item["userId"],
                        "connectionId": item["connectionId"],
                    },
                    UpdateExpression="SET ttl = :ttl",
                    ExpressionAttributeValues={":ttl": ttl},
                )
        except Exception:
            pass

    return {"statusCode": 200, "body": json.dumps({"type": "PONG", "ts": int(time.time())})}
