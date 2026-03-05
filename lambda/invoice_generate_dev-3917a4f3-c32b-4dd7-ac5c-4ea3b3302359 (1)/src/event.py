import base64
import json
import os

def get_json_body(event):
    body = event.get("body")
    if body is None or body == "":
        return {}
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body)
    except Exception:
        # sometimes Stripe sends raw JSON string already; still try
        return json.loads(body)

def get_header(event, name):
    headers = event.get("headers") or {}
    # API GW may lowercase keys
    for k,v in headers.items():
        if k.lower() == name.lower():
            return v
    return None

def get_jwt_sub(event):
    # HTTP API JWT authorizer
    try:
        return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except Exception:
        pass
    # REST API custom authorizer
    try:
        return event["requestContext"]["authorizer"]["claims"]["sub"]
    except Exception:
        pass
    # Local dev fallback
    return os.getenv("DEV_COGNITO_SUB")
