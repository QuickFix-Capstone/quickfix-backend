import json
import sys
import os
from typing import Any, Dict

try:
    from shared.db import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from shared.db import get_connection


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Create an application for a specific job (service provider view).

    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims

    Path Parameter:
    - job_id: ID of the job to apply to

    Body:
    - proposed_price (required)
    - message (optional)

    Returns:
    - 201: Application created
    - 400: Validation error
    - 401: Unauthorized
    - 403: Forbidden
    - 404: Job or provider not found
    - 409: Already applied
    - 500: Server error
    """

    # 1️⃣ Extract Cognito JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2️⃣ Extract job_id
    try:
        job_id = event["pathParameters"]["job_id"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing job_id in path"})

    # 3️⃣ Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return _response(400, {"message": "Invalid JSON body"})

    proposed_price = body.get("proposed_price")
    message = body.get("message")

    if proposed_price is None:
        return _response(400, {"message": "proposed_price is required"})

    # 4️⃣ Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:

            # 5️⃣ Get provider_id from cognito_sub
            cur.execute(
                "SELECT provider_id FROM service_providers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            provider_row = cur.fetchone()

            if not provider_row:
                return _response(403, {"message": "Service provider profile not found"})

            provider_id = provider_row["provider_id"]

            # 6️⃣ Validate job exists and is open
            cur.execute(
                "SELECT status FROM jobs WHERE job_id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()

            if not job_row:
                return _response(404, {"message": "Job not found"})

            if job_row["status"] != "open":
                return _response(400, {"message": "Job is not open for applications"})

            # 7️⃣ Check if provider already applied
            cur.execute(
                """
                SELECT application_id
                FROM job_applications
                WHERE job_id = %s AND provider_id = %s
                """,
                (job_id, provider_id)
            )
            if cur.fetchone():
                return _response(409, {"message": "You have already applied to this job"})

            # 8️⃣ Insert application
            cur.execute(
                """
                INSERT INTO job_applications
                (job_id, provider_id, proposed_price, message, status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (job_id, provider_id, proposed_price, message)
            )

            conn.commit()

        return _response(201, {
            "message": "Application created successfully",
            "job_id": int(job_id),
            "provider_id": provider_id,
            "status": "pending"
        })

    except Exception as e:
        print(f"Error creating job application: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass
