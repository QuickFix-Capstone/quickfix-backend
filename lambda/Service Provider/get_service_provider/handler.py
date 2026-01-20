import json
from infrastructure.repository.service_provider_repo import ServiceProviderRepository


def lambda_handler(event, context):
    try:
        # ==============================
        # 🔐 JWT Authorizer (HTTP API)
        # ==============================
        authorizer = event.get("requestContext", {}).get("authorizer")
        if not authorizer or "jwt" not in authorizer:
            return _response(401, {"error": "Unauthorized"})

        claims = authorizer["jwt"].get("claims")
        if not claims or "sub" not in claims:
            return _response(401, {"error": "Invalid token"})

        cognito_sub = claims["sub"]

        # ==============================
        # 🧠 Fetch Service Provider
        # ==============================
        repo = ServiceProviderRepository()
        provider = repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            # 🚫 Onboarding not completed
            return _response(404, {
                "error": "Service Provider profile not found",
                "onboarded": False
            })

        # ==============================
        # ✅ Return Provider Profile
        # ==============================
        return _response(200, {
            "onboarded": True,
            "service_provider": {
                "provider_id": provider["provider_id"],
                "name": provider["name"],
                "business_name": provider["business_name"],
                "email": provider["email"],
                "address_line": provider["address_line"],
                "city": provider["city"],
                "province": provider["province"],
                "postal_code": provider["postal_code"],
                "bio": provider["bio"],
                "rating": provider["rating"],
                "certification_url": provider["certification_url"],
                "verification_status": provider["verification_status"],
                "is_active": provider["is_active"],
                "created_at": str(provider["created_at"]),
            }
        })

    except Exception as e:
        print("❌ Lambda error:", str(e))
        return _response(500, {
            "error": "Failed to fetch Service Provider",
            "details": str(e)
        })


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
