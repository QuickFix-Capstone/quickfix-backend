import json
import os
import sys
import logging
import base64
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------
# Make sure we can import from src/ (db, s3, etc.)
# This assumes final zip has:
#   /var/task/handler.py
#   /var/task/src/...
# --------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Now we can import shared modules
from db.service_providers import create_service_provider_in_db
from db.provider_certifications import add_provider_certification
from s3.upload import upload_file


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support both:
    - API Gateway event: event["body"] is JSON string
    - Direct dict usage for local testing
    """
    body = event.get("body")
    if body is None:
        # Maybe event itself is already the data
        if isinstance(event, dict):
            return event
        return {}

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

    raise ValueError("Unsupported body format")


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


# --------------------------------------------------------------------
# Lambda handler
# --------------------------------------------------------------------
def handler(event, context):
    """
    Create a new service provider and (optionally) one certification.

    Expected body includes provider fields like:
      email, first_name, last_name, phone, business_name, bio,
      category, city, state, postal_code

    For certificate, supports either:
      - cert_url               (already uploaded to S3)
      - OR cert_file_base64 + cert_filename (upload via this Lambda)
    And optional:
      - cert_type
    """

    logger.info("Received event: %s", json.dumps(event))

    # 1) Parse body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"success": False, "message": str(e)})

    # 2) Validate required provider fields
    required_fields = ["email", "first_name", "last_name", "category"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return _response(
            400,
            {
                "success": False,
                "message": "Missing required fields",
                "missing": missing,
            },
        )

    # 3) Create service provider in DB
    provider_result = create_service_provider_in_db(data)
    if not provider_result.get("success"):
        error_msg = provider_result.get("error", "Failed to create service provider")
        logger.error("create_service_provider_in_db failed: %s", error_msg)
        return _response(
            500,
            {
                "success": False,
                "message": "Failed to create service provider",
                "error": error_msg,
            },
        )

    provider_id = provider_result["provider_id"]

    # ----------------------------------------------------------------
    # 4) Handle certification (optional)
    # ----------------------------------------------------------------
    cert_url = data.get("cert_url")
    cert_type = data.get("cert_type")
    cert_file_base64 = data.get("cert_file_base64")
    cert_filename = data.get("cert_filename") or "certificate.jpg"

    # Option B: if no cert_url but a base64 file is provided, upload to S3
    if not cert_url and cert_file_base64:
        try:
            file_bytes = base64.b64decode(cert_file_base64)
        except Exception:
            return _response(
                400,
                {
                    "success": False,
                    "message": "Invalid cert_file_base64; cannot decode.",
                },
            )

        upload_result = upload_file(file_bytes, cert_filename, folder="certifications")
        if not upload_result.get("success"):
            logger.error("S3 upload failed: %s", upload_result.get("error"))
            # You could also roll back the provider here if you want strict consistency
            return _response(
                500,
                {
                    "success": False,
                    "message": "Provider created but failed to upload certification to S3",
                    "provider_id": provider_id,
                    "error": upload_result.get("error"),
                },
            )

        cert_url = upload_result["url"]

    cert_id = None
    if cert_url:
        cert_result = add_provider_certification(
            provider_id=provider_id,
            cert_url=cert_url,
            cert_type=cert_type,
        )

        if not cert_result.get("success"):
            logger.error("add_provider_certification failed: %s", cert_result.get("error"))
            # Provider exists, but cert failed
            return _response(
                500,
                {
                    "success": False,
                    "message": "Provider created but failed to save certification record",
                    "provider_id": provider_id,
                    "error": cert_result.get("error"),
                },
            )

        cert_id = cert_result["cert_id"]

    # ----------------------------------------------------------------
    # 5) Final success response
    # ----------------------------------------------------------------
    return _response(
        201,
        {
            "success": True,
            "message": "Service provider created successfully",
            "provider_id": provider_id,
            "certification": {
                "cert_id": cert_id,
                "cert_url": cert_url,
                "cert_type": cert_type,
            }
            if cert_url
            else None,
        },
    )


# --------------------------------------------------------------------
# Optional: local test
# --------------------------------------------------------------------
if __name__ == "__main__":
    # Local test: provider with base64 cert -> Lambda uploads to S3
    # Base64 for a 1x1 white PNG
    dummy_base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAAAgABKlx+MAAAAABJRU5ErkJggg=="
    
    test_event = {
        "body": json.dumps(
            {
                "email": "pro2@test.com",
                "first_name": "Jack",
                "last_name": "Lee",
                "category": "electrician",

                # force S3 path by not using cert_url
                "cert_url": None,
                "cert_file_base64": dummy_base64_image,
                "cert_filename": "license.jpg",
                "cert_type": "electrical license"
            }
        )
    }

    print("🔍 Running local test for create_service_provider.handler()...")
    resp = handler(test_event, None)
    print("Response:")
    print(json.dumps(resp, indent=2))
