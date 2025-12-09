import json
import sys
import os
from typing import Any, Dict

# --------------------------------------------------------------------
# Make sure we can import from src/ (db, s3, etc.)
# --------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))

# Add ROOT_DIR to sys.path so we can do 'from src.X import Y'
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.db.rds_main import get_connection


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Get the current service provider's profile.

    Authentication:
    - Expects JWT authorizer (Cognito)
    - Email/Sub from event["requestContext"]["authorizer"]["jwt"]["claims"]
    """

    # 1. Extract Cognito JWT claims
    try:
        if "requestContext" in event:
            claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
            email = claims.get("email")
            cognito_sub = claims.get("sub")
        else:
            # Fallback for local testing if passing specific dict
            email = event.get("email")
            cognito_sub = event.get("cognito_sub")
            
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not email and not cognito_sub:
        return _response(400, {"message": "Invalid token: email/sub missing"})

    # 2. Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # Query service_providers
            sql = """
                SELECT provider_id, email, first_name, last_name, phone, business_name, 
                       bio, category, rating, city, state, postal_code, is_verified, cognito_sub
                FROM service_providers
                WHERE cognito_sub = %s OR email = %s
                LIMIT 1
            """
            cur.execute(sql, (cognito_sub, email))
            row = cur.fetchone()

        if not row:
            return _response(404, {"message": "Service provider profile not found"})

        # Build response
        provider = {
            "provider_id": row["provider_id"],
            "email": row["email"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "phone": row["phone"],
            "business_name": row["business_name"],
            "bio": row["bio"],
            "category": row["category"],
            "rating": float(row["rating"]) if row["rating"] is not None else 0.0,
            "city": row["city"],
            "state": row["state"],
            "postal_code": row["postal_code"],
            "is_verified": bool(row["is_verified"]),
            "cognito_sub": row["cognito_sub"],
        }

        return _response(200, {"service_provider": provider})

    except Exception as e:
        print("Error in get_service_provider:", e)
        return _response(500, {"message": "Internal server error", "error": str(e)})

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Local test
    # Usage: Provide an email that exists in your DB.
    test_email = "pro3@test.com" 
    
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "email": test_email,
                        "sub": "mock-sub-unused-for-now"
                    }
                }
            }
        }
    }
    
    print("Running local test for get_service_provider...")
    resp = handler(test_event, None)
    print(json.dumps(resp, indent=2))
