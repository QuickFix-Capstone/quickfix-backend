import json


def handler(event, context):
    request_context = event.get("requestContext") or {}
    body_raw = event.get("body") or "{}"

    try:
        body = json.loads(body_raw) if isinstance(body_raw, str) else (body_raw or {})
    except json.JSONDecodeError:
        body = {}

    action = body.get("action") or request_context.get("routeKey") or "$default"
    request_id = body.get("requestId")

    return {
        "statusCode": 400,
        "body": json.dumps(
            {
                "type": "response",
                "action": action,
                "requestId": request_id,
                "success": False,
                "error": {
                    "code": "UNKNOWN_ROUTE",
                    "message": f"Unsupported action: {action}",
                },
            }
        ),
    }
