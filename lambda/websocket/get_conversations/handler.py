import json


def _parse_event(event):
    body_raw = event.get("body") or "{}"
    if isinstance(body_raw, dict):
        return body_raw
    try:
        return json.loads(body_raw)
    except json.JSONDecodeError:
        return {}


def handler(event, context):
    payload = _parse_event(event)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "type": "response",
                "action": "getConversations",
                "requestId": payload.get("requestId"),
                "success": True,
                "data": {
                    "conversations": [],
                    "phase": "phase1_infrastructure",
                    "status": "route_configured",
                },
            }
        ),
    }
