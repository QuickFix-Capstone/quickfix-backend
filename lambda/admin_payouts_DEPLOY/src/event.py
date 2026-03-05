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
    for k, v in headers.items():
        if str(k).lower() == name.lower():
            return v
    return None

def _b64url_decode(s: str) -> bytes:
    s = str(s).strip()
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)

def _decode_jwt_payload_no_verify(token: str) -> dict:
    """Decode JWT payload WITHOUT verifying signature (fallback)."""
    try:
        parts = str(token).split(".")
        if len(parts) < 2:
            return {}
        payload_json = _b64url_decode(parts[1]).decode("utf-8")
        return json.loads(payload_json)
    except Exception:
        return {}

def _get_bearer_claims(event) -> dict:
    auth = get_header(event, "Authorization") or get_header(event, "authorization")
    if not auth:
        return {}
    s = str(auth).strip()
    if not s.lower().startswith("bearer "):
        return {}
    token = s.split(" ", 1)[1].strip()
    return _decode_jwt_payload_no_verify(token)

def _get_jwt_claims(event):
    # HTTP API JWT authorizer
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        if claims:
            return claims
    except Exception:
        pass
    # REST API custom authorizer
    try:
        claims = event["requestContext"]["authorizer"]["claims"]
        if claims:
            return claims
    except Exception:
        pass
    # Fallback: decode Authorization: Bearer <jwt>
    return _get_bearer_claims(event) or {}

def get_jwt_sub(event):
    claims = _get_jwt_claims(event) or {}
    sub = claims.get("sub") if isinstance(claims, dict) else None
    if sub:
        return sub
    # Local dev fallback
    return os.getenv("DEV_COGNITO_SUB")

def get_jwt_groups(event):
    """
    Returns list of Cognito groups from JWT claims.
    Supports:
      - HTTP API JWT authorizer (claims as dict)
      - REST API authorizer (claims as dict)
      - Fallback: decode Authorization Bearer token payload
    """
    claims = _get_jwt_claims(event) or {}
    if not isinstance(claims, dict):
        return []

    val = claims.get("cognito:groups") or claims.get("groups") or claims.get("cognito:group")

    if val is None:
        return []

    # Sometimes it's already a list (rare)
    if isinstance(val, list):
        return [str(x) for x in val]

    # Usually it's a string
    s = str(val).strip()
    if s == "":
        return []

    # Could be JSON array string: ["Admin","Manager"]
    if s.startswith("[") and s.endswith("]"):
        try:
            arr = json.loads(s)
            if isinstance(arr, list):
                return [str(x) for x in arr]
        except Exception:
            pass

    # Could be comma-separated
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]

    # Single group
    return [s]
