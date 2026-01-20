import json
import os
import uuid
import boto3
from shared.response import response
from shared.auth import get_cognito_sub
from infrastructure.provider_certification_repo import ProviderCertificationRepository
from infrastructure.service_provider_repo import ServiceProviderRepository


s3 = boto3.client("s3")
BUCKET_NAME = os.environ["CERT_BUCKET"]  # e.g. quickfix-app-files


def lambda_handler(event, context):
    try:
        # ==============================
        # 1️⃣ AUTH – Get Cognito user
        # ==============================
        cognito_sub = get_cognito_sub(event)
        if not cognito_sub:
            return response(401, {"error": "Unauthorized"})

        # ==============================
        # 2️⃣ Check if provider exists
        # ==============================
        provider_repo = ServiceProviderRepository()
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        # ==============================
        # 3️⃣ Parse request body
        # ==============================
        body = json.loads(event.get("body", "{}"))
        filename = body.get("filename")

        if not filename:
            return response(400, {"error": "filename is required"})

        if not filename.lower().endswith(".pdf"):
            return response(400, {"error": "Only PDF files are allowed"})

        # ==============================
        # 4️⃣ Decide S3 folder (KEY PART)
        # ==============================
        if provider:
            # Existing provider
            folder = f"certifications/{provider['provider_id']}"
        else:
            # Onboarding (provider not in DB yet)
            folder = f"certifications/pending/{cognito_sub}"

        s3_key = f"{folder}/{uuid.uuid4()}.pdf"

        # ==============================
        # 5️⃣ Generate pre-signed PUT URL
        # ==============================
        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": "application/pdf",
            },
            ExpiresIn=300,  # 5 minutes
        )

        # ==============================
        # 6️⃣ Return response
        # ==============================
        return response(
            200,
            {
                "uploadUrl": upload_url,
                "s3Key": s3_key,
                "mode": "EXISTING_PROVIDER" if provider else "ONBOARDING",
            },
        )

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {"error": "Internal server error"})
