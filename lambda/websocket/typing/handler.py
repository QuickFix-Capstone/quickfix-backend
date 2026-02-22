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
    data = payload.get("data") or {}

    if not data.get("conversationId"):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "type": "response",
                    "action": "typing",
                    "requestId": payload.get("requestId"),
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "conversationId is required",
                    },
                }
            ),
        }

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "type": "response",
                "action": "typing",
                "requestId": payload.get("requestId"),
                "success": True,
                "data": {
                    "conversationId": data.get("conversationId"),
                    "isTyping": bool(data.get("isTyping", True)),
                    "phase": "phase1_infrastructure",
                    "status": "route_configured",
                },
            }
        ),
    }
