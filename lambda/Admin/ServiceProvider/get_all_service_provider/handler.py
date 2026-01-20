import json
from datetime import datetime
from decimal import Decimal
from infrastructure.service_provider_repo import ServiceProviderRepository


def lambda_handler(event, context):
    try:
        # ==============================
        # 0️⃣ AUTH: JWT + ADMIN GROUP
        # ==============================
        authorizer = event.get("requestContext", {}).get("authorizer")
        if not authorizer or "jwt" not in authorizer:
            return response(401, {"error": "Unauthorized"})

        claims = authorizer["jwt"].get("claims")
        if not claims:
            return response(401, {"error": "Unauthorized"})

        groups = claims.get("cognito:groups", [])
        if isinstance(groups, str):
            groups = [groups]

        if "Administrator" not in groups:
            return response(403, {"error": "Admin access required"})

        # ==============================
        # 1️⃣ PAGINATION PARAMS
        # ==============================
        query = event.get("queryStringParameters") or {}
        limit = int(query.get("limit", 50))
        offset = int(query.get("offset", 0))

        # ==============================
        # 2️⃣ FETCH SERVICE PROVIDERS
        # ==============================
        repo = ServiceProviderRepository()
        providers = repo.get_all(limit=limit, offset=offset) or []

        # ==============================
        # 3️⃣ RESPONSE
        # ==============================
        return response(200, {
            "count": len(providers),
            "items": providers,
            "limit": limit,
            "offset": offset,
        })

    except Exception as e:
        print("ERROR TYPE:", type(e))
        print("ERROR MESSAGE:", repr(e))

        return response(500, {
            "error": "Internal server error",
            "details": repr(e),
        })


# ==============================
# JSON SERIALIZATION
# ==============================
def json_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, datetime):
        return obj.isoformat()

    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def response(status_code: int, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=json_serializer),
    }
