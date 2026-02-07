import json
import os
import time
import urllib.request

import boto3
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError


_JWKS_CACHE = {}
_JWKS_CACHE_TS = 0
_JWKS_CACHE_TTL_SECONDS = 3600


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def _get_jwks():
    global _JWKS_CACHE, _JWKS_CACHE_TS
    now = int(time.time())
    if _JWKS_CACHE and now - _JWKS_CACHE_TS < _JWKS_CACHE_TTL_SECONDS:
        return _JWKS_CACHE

    region = _get_env("COGNITO_REGION", _get_env("AWS_REGION", "us-east-2"))
    user_pool_id = _get_env("COGNITO_USERPOOL_ID")
    if not user_pool_id:
        raise RuntimeError("Missing COGNITO_USERPOOL_ID")

    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    with urllib.request.urlopen(jwks_url, timeout=5) as resp:
        jwks = json.loads(resp.read().decode("utf-8"))

    _JWKS_CACHE = jwks
    _JWKS_CACHE_TS = now
    return jwks


def _verify_jwt(token: str) -> dict:
    client_id = _get_env("COGNITO_CLIENT_ID")
    region = _get_env("COGNITO_REGION", _get_env("AWS_REGION", "us-east-2"))
    user_pool_id = _get_env("COGNITO_USERPOOL_ID")
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    jwks = _get_jwks()
    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key = k
            break
    if not key:
        raise JWTError("JWK not found for token")

    options = {
        "verify_aud": bool(client_id),
        "verify_iss": True,
    }
    decoded = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=client_id if client_id else None,
        issuer=issuer,
        options=options,
    )
    return decoded


def handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        token = params.get("token")
        if not token:
            return {"statusCode": 401, "body": json.dumps({"message": "Missing token"})}

        claims = _verify_jwt(token)
        user_id = claims.get("sub")
        if not user_id:
            return {"statusCode": 401, "body": json.dumps({"message": "Invalid token"})}

        connection_id = event["requestContext"]["connectionId"]
        now = int(time.time())
        ttl = now + 7200  # 2 hours
        role = None
        groups = claims.get("cognito:groups") or []
        if isinstance(groups, list) and groups:
            role = groups[0]

        table_name = _get_env("WS_CONNECTIONS_TABLE", "quickfix-ws-connections")
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        table.put_item(
            Item={
                "userId": user_id,
                "connectionId": connection_id,
                "connectedAt": now,
                "ttl": ttl,
                "role": role,
                "stage": event.get("requestContext", {}).get("stage"),
            }
        )

        return {"statusCode": 200, "body": json.dumps({"message": "connected"})}
    except ExpiredSignatureError:
        return {"statusCode": 401, "body": json.dumps({"message": "Token expired"})}
    except Exception as exc:
        return {"statusCode": 401, "body": json.dumps({"message": "Unauthorized", "error": str(exc)})}
