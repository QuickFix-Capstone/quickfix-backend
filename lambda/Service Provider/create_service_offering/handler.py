import json
import boto3
import os
from domain import ServiceOffering, ServiceCategory, PricingType
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

        # Require key claims
        required_claims = ["sub"]
        missing_claims = [c for c in required_claims if c not in claims]
        if missing_claims:
            return response(401, {"error": f"Invalid token. Missing: {missing_claims}"})

        cognito_sub = claims["sub"]

        # ==============================
        # 1️⃣ ROLE CHECK: COGNITO GROUP
        # ==============================
        provider_repo = ServiceProviderRepository()

        provider = provider_repo.get_by_cognito_sub(cognito_sub)
        if not provider:
            return response(403, {"error": "Service provider profile not found"})


        # ==============================
        # 2️⃣ DB CHECK: SERVICE PROVIDER EXISTS
        # ==============================
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            return response(403, {"error": "Service provider profile not found"})

        # Your DB may return dict keys differently:
        # adjust these to match your schema
        provider_id = provider.get("provider_id") or provider.get("id")

        if not provider_id:
            return response(500, {"error": "Provider record missing provider_id"})

        # ==============================
        # 3️⃣ ENFORCE VERIFICATION
        # ==============================
        if provider.get("verification_status") != "VERIFIED":
            return response(
                403,
                {"error": "Your account must be verified before creating a service offering"}
            )

        # ==============================
        # 4️⃣ PARSE REQUEST BODY
        # ==============================
        body = json.loads(event.get("body", "{}"))

        required_fields = ["title", "description", "category", "price", "pricing_type"]
        for field in required_fields:
            if field not in body or body[field] in (None, ""):
                return response(400, {"error": f"Missing required field: {field}"})

        # ==============================
        # 5️⃣ CREATE DOMAIN OBJECT
        # ==============================
        offering = ServiceOffering(
            provider_id=provider_id,  # ✅ derived from DB, not client input
            title=body["title"],
            description=body["description"],
            category=ServiceCategory(body["category"]),
            price=float(body["price"]),
            pricing_type=PricingType(body["pricing_type"]),
            main_image_url=body.get("main_image_url"),
            is_active=True,
        )

        # ==============================
        # 6️⃣ SAVE TO DATABASE
        # ==============================
        repo = ServiceOfferingRepository()
        repo.create(offering)

        return response(201, {
            "message": "Service offering created successfully",
            "service_offering_id": offering.service_offering_id
        })

    except ValueError as e:
        # Enum conversion or casting errors
        return response(400, {"error": str(e)})

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {"error": "Internal server error", "details": str(e)})


def response(status_code: int, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
