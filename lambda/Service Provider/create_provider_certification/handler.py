import json
import os
import uuid
import boto3
from shared.response import response
from shared.auth import get_cognito_sub
from infrastructure.provider_certification_repo import ProviderCertificationRepository
from infrastructure.service_provider_repo import ServiceProviderRepository

def lambda_handler(event, context):
    try:
        # ==============================
        # 1️⃣ AUTH
        # ==============================
        cognito_sub = get_cognito_sub(event)
        if not cognito_sub:
            return response(401, {"error": "Unauthorized"})

        # ==============================
        # 2️⃣ GET PROVIDER
        # ==============================
        provider_repo = ServiceProviderRepository()
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            return response(400, {"error": "Service provider not found"})

        provider_id = provider["provider_id"]

        # ==============================
        # 3️⃣ PARSE BODY
        # ==============================
        body = json.loads(event.get("body", "{}"))
        s3_key = body.get("certification_s3_key")

        if not s3_key:
            return response(400, {"error": "certification_s3_key is required"})

        # ==============================
        # 4️⃣ CREATE DOMAIN OBJECT
        # ==============================
        certification = ProviderCertification(
            certification_id=f"CERT-{uuid.uuid4()}",
            provider_id=provider_id,
            certification_s3_key=s3_key,
            certification_type="LICENSE",          # or whatever enum you use
            verification_status="APPROVED",        # auto-verified for now
            uploaded_at=datetime.utcnow(),
        )

        # ==============================
        # 5️⃣ SAVE TO DB
        # ==============================
        cert_repo = ProviderCertificationRepository()
        cert_repo.create(certification)

        return response(201, {"message": "Certification saved successfully"})

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {"error": "Internal server error"})
