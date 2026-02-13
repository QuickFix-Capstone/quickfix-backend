import json
import os
import sys
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body),
    }


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body from API Gateway event."""
    if "body" not in event:
        return event

    body = event["body"]
    if isinstance(body, dict):
        return body
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

    raise ValueError("Unsupported body format")


def _parse_updates(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and return updatable fields."""
    updates: Dict[str, Any] = {}

    if "proposed_price" in data:
        raw_price = data.get("proposed_price")
        try:
            proposed_price = float(raw_price)
        except (TypeError, ValueError):
            raise ValueError("proposed_price must be a number greater than 0")

        if proposed_price <= 0:
            raise ValueError("proposed_price must be greater than 0")

        updates["proposed_price"] = proposed_price

    if "message" in data:
        raw_message = data.get("message")
        if not isinstance(raw_message, str) or not raw_message.strip():
            raise ValueError("message must be a non-empty string")
        updates["message"] = raw_message.strip()

    if not updates:
        raise ValueError("No valid fields to update. Provide proposed_price and/or message")

    return updates


def handler(event, context):
    """
    Update a provider's own pending job application.

    Endpoint:
    - PUT /job/{job_id}/applications/{application_id}/update

    Rules:
    - Provider must be authenticated
    - Provider can only update their own application
    - Only pending applications can be updated
    - Job must be open
    """
    # 1. Extract Cognito JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2. Extract path parameters
    try:
        job_id = event["pathParameters"]["job_id"]
        application_id = event["pathParameters"]["application_id"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing job_id or application_id in path"})

    # 3. Parse body
    try:
        data = _parse_body(event)
        updates = _parse_updates(data)
    except ValueError as exc:
        return _response(400, {"message": str(exc)})

    # 4. Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 5. Resolve provider from JWT
            cur.execute(
                "SELECT provider_id FROM service_providers WHERE cognito_sub = %s",
                (cognito_sub,),
            )
            provider_row = cur.fetchone()
            if not provider_row:
                return _response(404, {"message": "Provider profile not found"})
            provider_id = provider_row["provider_id"]

            # 6. Verify job exists and is open
            cur.execute(
                "SELECT job_id, status FROM jobs WHERE job_id = %s",
                (job_id,),
            )
            job_row = cur.fetchone()
            if not job_row:
                return _response(404, {"message": "Job not found"})

            if job_row["status"] != "open":
                return _response(409, {"message": "Job is not open. Applications can only be updated for open jobs"})

            # 7. Verify application exists for this job
            cur.execute(
                """
                SELECT application_id, job_id, provider_id, proposed_price, message, status, created_at
                FROM job_applications
                WHERE application_id = %s AND job_id = %s
                """,
                (application_id, job_id),
            )
            app_row = cur.fetchone()
            if not app_row:
                return _response(404, {"message": "Application not found"})

            # 8. Provider ownership check
            if app_row["provider_id"] != provider_id:
                return _response(403, {"message": "Forbidden: You can only update your own application"})

            # 9. Status check
            if app_row["status"] != "pending":
                return _response(409, {"message": f"Application is {app_row['status']}. Only pending applications can be updated"})

            # 10. Build dynamic update query
            set_sql = ", ".join([f"{field} = %s" for field in updates.keys()])
            params = list(updates.values()) + [application_id, job_id]
            cur.execute(
                f"""
                UPDATE job_applications
                SET {set_sql}
                WHERE application_id = %s AND job_id = %s
                """,
                params,
            )
            conn.commit()

            # 11. Fetch updated row
            cur.execute(
                """
                SELECT application_id, job_id, provider_id, proposed_price, message, status, created_at
                FROM job_applications
                WHERE application_id = %s AND job_id = %s
                """,
                (application_id, job_id),
            )
            updated_row = cur.fetchone()

        # 12. Format response
        return _response(
            200,
            {
                "message": "Application updated successfully",
                "application": {
                    "application_id": updated_row["application_id"],
                    "job_id": updated_row["job_id"],
                    "provider_id": updated_row["provider_id"],
                    "proposed_price": float(updated_row["proposed_price"]) if updated_row["proposed_price"] is not None else None,
                    "message": updated_row["message"],
                    "status": updated_row["status"],
                    "created_at": updated_row["created_at"].isoformat() if updated_row["created_at"] else None,
                },
            },
        )

    except Exception as exc:
        print(f"Error updating job application: {exc}")
        return _response(500, {"message": "Internal server error"})
    finally:
        try:
            conn.close()
        except Exception:
            pass

