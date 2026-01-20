import json
from datetime import datetime

from shared.response import response
from infrastructure.repository.service_provider_repo import ServiceProviderRepository


def lambda_handler(event, context):
    try:
        # ==============================
        # 🔐 AUTH (HTTP API v2)
        # ==============================
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
        )

        cognito_sub = claims.get("sub")

        if not cognito_sub:
            return response(401, {"error": "Unauthorized"})

        # ==============================
        # 📦 BODY
        # ==============================
        body = json.loads(event.get("body") or "{}")

        if not body:
            return response(400, {"error": "No update data provided"})

        provider_repo = ServiceProviderRepository()

        # ==============================
        # 🔍 FETCH PROVIDER
        # ==============================
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            return response(404, {"error": "Service provider not found"})

        # ==============================
        # 🧠 UPDATE FIELDS (PATCH STYLE)
        # ==============================
        updatable_fields = [
            "name",
            "business_name",
            "address_line",
            "city",
            "province",
            "postal_code",
            "bio",
            "phone_number",
        ]

        for field in updatable_fields:
            if field in body:
                setattr(provider, field, body[field])

        provider.updated_at = datetime.utcnow()

        # ==============================
        # 💾 SAVE
        # ==============================
        provider_repo.update(provider)

        return response(200, {
            "message": "Service provider updated successfully",
            "provider_id": provider.provider_id,
        })

    except Exception as e:
        print("❌ Lambda error:", str(e))
        return response(500, {"error": "Internal server error"})
