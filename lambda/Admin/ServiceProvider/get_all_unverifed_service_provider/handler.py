import json
from infrastrucuture.service_provider_repo import ServiceProviderRepository


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
        # 1️⃣ OPTIONAL QUERY PARAMS
        # ==============================
        query = event.get("queryStringParameters") or {}
        limit = int(query.get("limit", 50))
        offset = int(query.get("offset", 0))

        # ==============================
        # 2️⃣ FETCH UNVERIFIED PROVIDERS
        # ==============================
        repo = ServiceProviderRepository()
        providers = repo.get_unverified(limit=limit, offset=offset)

        # ==============================
        # 3️⃣ SUCCESS RESPONSE
        # ==============================
        return response(200, {
            "count": len(providers),
            "providers": providers
        })

    except Exception as e:
        print("ERROR:", repr(e))
        return response(500, {
            "error": "Internal server error"
        })


# ==============================
# RESPONSE HELPER
# ==============================
def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
