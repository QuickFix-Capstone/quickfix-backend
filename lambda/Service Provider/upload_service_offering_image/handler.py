import json
from shared.response import response
from shared.auth import get_cognito_sub
from infrastructure.service_provider_repo import ServiceProviderRepository
from infrastructure.s3_presigner import S3Presigner
from domain.upload_request import UploadImageRequest


def lambda_handler(event, context):
    try:
        # ==============================
        # 🔐 AUTH: Cognito JWT
        # ==============================
        cognito_sub = get_cognito_sub(event)
        if not cognito_sub:
            return response(401, {"error": "Unauthorized"})

        # ==============================
        # 📦 REQUEST BODY
        # ==============================
        if not event.get("body"):
            return response(400, {"error": "Missing request body"})

        body = json.loads(event["body"])

        title = body.get("title")
        content_type = body.get("content_type")

        if not title or not content_type:
            return response(
                400,
                {
                    "error": "Both 'title' and 'content_type' are required"
                },
            )

        upload_request = UploadImageRequest(
            title=title,
            content_type=content_type,
        )

        # ==============================
        # 🧑‍🔧 GET SERVICE PROVIDER
        # ==============================
        provider_repo = ServiceProviderRepository()
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            return response(
                403,
                {"error": "Service provider profile not found"},
            )

        provider_id = provider["provider_id"]

        # ==============================
        # ☁️ GENERATE UPLOAD URL
        # ==============================
        presigner = S3Presigner()
        result = presigner.generate_upload_url(
            provider_id=provider_id,
            service_title=upload_request.title,
            content_type=upload_request.content_type,
        )

        # ==============================
        # ✅ SUCCESS
        # ==============================
        return response(
            200,
            {
                "uploadUrl": result["upload_url"],
                "s3Key": result["s3_key"],
                "imageUrl": result["image_url"],
            },
        )

    except ValueError as e:
        # Validation errors (content type, etc.)
        return response(400, {"error": str(e)})

    except Exception as e:
        print("❌ Upload URL Lambda Error:", str(e))
        return response(
            500,
            {"error": "Internal server error"},
        )
