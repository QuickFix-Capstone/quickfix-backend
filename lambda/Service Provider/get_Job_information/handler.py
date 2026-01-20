import json
import sys
import os

try:
    from shared.db import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        },
        "body": json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    """
    Service Provider – Get Job Details

    Access rules:
    - Job is OPEN
    - OR provider has applied
    - OR provider is assigned
    """

    # 1️⃣ Auth – get provider identity
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized"})

    # 2️⃣ Get job_id
    try:
        job_id = event["pathParameters"]["job_id"]
    except Exception:
        return _response(400, {"message": "Missing job_id in path"})

    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 3️⃣ Resolve provider
            cur.execute(
                "SELECT provider_id FROM service_providers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            provider = cur.fetchone()

            if not provider:
                return _response(403, {"message": "Service provider profile not found"})

            provider_id = provider["provider_id"]

            # 4️⃣ Fetch job + application status
            cur.execute("""
                SELECT
                    j.job_id,
                    j.title,
                    j.description,
                    j.category,
                    j.location_address,
                    j.location_city,
                    j.location_state,
                    j.location_zip,
                    j.preferred_date,
                    j.preferred_time,
                    j.budget_min,
                    j.budget_max,
                    j.status,
                    j.assigned_provider_id,
                    j.created_at,
                    MAX(CASE WHEN ja.provider_id = %s THEN 1 ELSE 0 END) AS has_applied
                FROM jobs j
                LEFT JOIN job_applications ja ON j.job_id = ja.job_id
                WHERE j.job_id = %s
                GROUP BY j.job_id
            """, (provider_id, job_id))

            job = cur.fetchone()

            if not job:
                return _response(404, {"message": "Job not found"})

            # 5️⃣ Authorization
            is_open = job["status"] == "OPEN"
            is_assigned = job["assigned_provider_id"] == provider_id
            has_applied = job["has_applied"] == 1

            if not (is_open or is_assigned or has_applied):
                return _response(403, {"message": "You are not allowed to view this job"})

        # 6️⃣ Build response
        response_job = {
            "job_id": job["job_id"],
            "title": job["title"],
            "description": job["description"],
            "category": job["category"],
            "preferred_date": str(job["preferred_date"]) if job["preferred_date"] else None,
            "preferred_time": str(job["preferred_time"]) if job["preferred_time"] else None,
            "budget": {
                "min": float(job["budget_min"]) if job["budget_min"] else None,
                "max": float(job["budget_max"]) if job["budget_max"] else None
            },
            "status": job["status"],
            "has_applied": has_applied,
            "is_assigned": is_assigned,
            "created_at": job["created_at"].isoformat() if job["created_at"] else None
        }

        # 🔐 Full address ONLY if assigned
        if is_assigned:
            response_job["location"] = {
                "address": job["location_address"],
                "city": job["location_city"],
                "state": job["location_state"],
                "zip": job["location_zip"]
            }
        else:
            response_job["location"] = {
                "city": job["location_city"],
                "state": job["location_state"]
            }

        return _response(200, {"job": response_job})

    except Exception as e:
        print(f"Provider job details error: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass
