<<<<<<< HEAD
=======
import json
import logging
import base64
import os
import sys
from typing import Any, Dict

# Ensure src is in path for imports
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))

# Add ROOT_DIR to sys.path so we can do 'from src.X import Y'
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.db.rds_main import get_connection
from src.s3.upload import upload_file
from pymysql.err import IntegrityError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support both:
    - API Gateway event: event["body"] is JSON string
    - Direct dict usage for local testing
    """
    body = event.get("body")
    if body is None:
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


def handler(event, context):
    """
    Create a new service provider and (optionally) one certification.
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

    # 3) Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"success": False, "message": "Database connection failed"})

    provider_id = None
    cert_id = None
    cert_url = data.get("cert_url")
    cert_type = data.get("cert_type")
    cert_file_base64 = data.get("cert_file_base64")
    cert_filename = data.get("cert_filename") or "certificate.jpg"
    
    try:
        # Handle S3 upload if needed (before DB or after? strict logic might imply transaction, 
        # but S3 isn't transactional. Let's do S3 first or after? create_customer doesn't have this.
        # I'll keep the order: DB insert first to get ID, then S3, then Cert insert.)
        
        with conn.cursor() as cur:
            # A) Insert Service Provider
            sql_provider = """
                INSERT INTO service_providers
                    (email, first_name, last_name, phone, business_name, 
                     bio, category, city, state, postal_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(
                sql_provider,
                (
                    data.get("email"),
                    data.get("first_name"),
                    data.get("last_name"),
                    data.get("phone"),
                    data.get("business_name"),
                    data.get("bio"),
                    data.get("category"),
                    data.get("city"),
                    data.get("state"),
                    data.get("postal_code"),
                ),
            )
            provider_id = cur.lastrowid
            
            # B) Handle Certification
            # If base64 provided, upload to S3 now
            if not cert_url and cert_file_base64:
                try:
                    file_bytes = base64.b64decode(cert_file_base64)
                    upload_result = upload_file(file_bytes, cert_filename, folder="certifications")
                    if upload_result.get("success"):
                        cert_url = upload_result["url"]
                    else:
                        logger.error("S3 upload failed: %s", upload_result.get("error"))
                        # We could raise an exception to rollback provider, strict preference?
                        # For now, let's just log and continue or fail?
                        # If S3 fails, maybe we shouldn't fail the provider creation? 
                        # But the user might expect a cert.
                        # I'll assume soft fail on cert for now or throw to rollback.
                        raise Exception(f"S3 Upload failed: {upload_result.get('error')}")
                except Exception as e:
                    # Reraise to trigger rollback
                    raise e
            
            # If we have a cert_url (either passed in or uploaded), insert cert record
            if cert_url:
                sql_cert = """
                    INSERT INTO provider_certifications (provider_id, cert_url, cert_type)
                    VALUES (%s, %s, %s)
                """
                cur.execute(sql_cert, (provider_id, cert_url, cert_type))
                cert_id = cur.lastrowid

            conn.commit()

        # 4) Success Response
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
                } if cert_url else None,
            },
        )

    except IntegrityError as e:
        # Check for duplicate email
        if "Duplicate entry" in str(e):
             return _response(
                409,
                {"success": False, "message": "A service provider with this email already exists."},
            )
        return _response(
            400,
            {"success": False, "message": "Failed to create service provider due to data constraint.", "error": str(e)},
        )
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        # Rollback is automatic on exception exit of 'with conn.cursor()' block? 
        # Actually in pymysql, if commit() isn't called, it rolls back on close.
        # But we should be careful. 
        # The 'with conn.cursor()' only closes cursor. Connection rollback is needed if commit wasn't reached.
        try:
            conn.rollback()
        except:
            pass
            
        return _response(
            500,
            {"success": False, "message": "Internal server error.", "error": str(e)},
        )
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Local test
    dummy_base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAAAgABKlx+MAAAAABJRU5ErkJggg=="
    test_event = {
        "body": json.dumps(
            {
                "email": "pro3@test.com",
                "first_name": "Jack",
                "last_name": "Lee",
                "category": "electrician",
                "cert_url": None,
                "cert_file_base64": dummy_base64_image,
                "cert_filename": "license.jpg",
                "cert_type": "electrical license"
            }
        )
    }

    print("Running local test...")
    # Mocking environment or assuming DB is reachable
    resp = handler(test_event, None)
    print(json.dumps(resp, indent=2))
>>>>>>> kunpeng/lambda-db-setup
