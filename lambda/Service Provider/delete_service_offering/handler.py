import json
from infrastructure.service_offering_repo import ServiceOfferingRepository
from infrastructure.service_provider_repo import ServiceProviderRepository


def lambda_handler(event, context):
    try:
        # ==============================
        # 0️⃣ AUTH: JWT CLAIMS (HTTP API)
        # ==============================
        authorizer = event.get("requestContext", {}).get("authorizer")
        if not authorizer or "jwt" not in authorizer:
            return response(401, {"error": "Unauthorized"})

        claims = authorizer["jwt"].get("claims")
        if not claims:
            return response(401, {"error": "Unauthorized"})

        required_claims = ["sub", "cognito:username"]
        missing_claims = [c for c in required_claims if c not in claims]
        if missing_claims:
            return response(401, {"error": f"Invalid token. Missing: {missing_claims}"})

        cognito_sub = claims["sub"]

        # ==============================
        # 1️⃣ ROLE CHECK: ServiceProvider
        # ==============================
        groups = claims.get("cognito:groups", [])
        if isinstance(groups, str):
            groups = [groups]

        if "ServiceProvider" not in groups:
            return response(403, {"error": "Forbidden: must be a ServiceProvider"})

        # ==============================
        # 2️⃣ DB CHECK: PROVIDER EXISTS
        # ==============================
        provider_repo = ServiceProviderRepository()
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            return response(403, {"error": "Service provider profile not found"})

        provider_id = provider.get("provider_id")
        if not provider_id:
            return response(500, {"error": "Provider record missing provider_id"})

        # ==============================
        # 3️⃣ ENFORCE VERIFICATION
        # ==============================
        if provider.get("verification_status") != "VERIFIED":
            return response(
                403,
                {"error": "Your account must be verified before deleting service offerings"}
            )

        # ==============================
        # 4️⃣ GET SERVICE OFFERING ID
        # ==============================
        service_offering_id = event.get("pathParameters", {}).get("service_offering_id")
        if not service_offering_id:
            return response(400, {"error": "Missing service_offering_id"})

        offering_repo = ServiceOfferingRepository()
        existing = offering_repo.get_by_id(service_offering_id)

        if not existing:
            return response(404, {"error": "Service offering not found"})

        # ==============================
        # 5️⃣ OWNERSHIP CHECK
        # ==============================
        if existing["provider_id"] != provider_id:
            return response(403, {"error": "Forbidden: not your service offering"})

        # ==============================
        # 6️⃣ DELETE (SOFT DELETE)
        # ==============================
        offering_repo.soft_delete(service_offering_id)

        return response(200, {
            "message": "Service offering deleted successfully",
            "service_offering_id": service_offering_id
        })

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {"error": "Internal server error"})


# ==============================
# 🔧 RESPONSE HELPER
# ==============================
def response(status_code: int, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
