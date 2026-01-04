import json
import sys
import os
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
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Unassign a provider from a job.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Path Parameter:
    - job_id: ID of the job to unassign
    
    Authorization:
    - Customer can only unassign providers from their own jobs
    - Job must be in "assigned" status
    
    Business Logic:
    - Sets job status back to "open"
    - Clears assigned_provider_id
    - Keeps all job applications in their current state (rejected stay rejected)
    
    Returns:
    - 200: Provider unassigned successfully
    - 400: Invalid request or job not in assigned status
    - 401: Unauthorized
    - 403: Forbidden (not customer's job)
    - 404: Job not found
    - 500: Server error
    """
    
    # 1. Extract Cognito JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2. Extract job_id from path parameters
    try:
        job_id = event["pathParameters"]["job_id"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing job_id in path"})

    # 3. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 4. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 5. Check if job exists and get current state
            cur.execute(
                "SELECT customer_id, status, assigned_provider_id FROM jobs WHERE job_id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()
            
            if not job_row:
                return _response(404, {"message": "Job not found"})
            
            # 6. Authorization check - must be job owner
            if job_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You can only unassign providers from your own jobs"})
            
            # 7. Validate job status - must be "assigned"
            if job_row["status"] != "assigned":
                return _response(400, {
                    "message": f"Cannot unassign provider from job with status '{job_row['status']}'. Only jobs with status 'assigned' can be unassigned."
                })
            
            # 8. Validate that a provider is actually assigned
            if not job_row["assigned_provider_id"]:
                return _response(400, {"message": "Job is not currently assigned to a provider"})

            # 9. Unassign provider - set status to open and clear assigned_provider_id
            cur.execute(
                """
                UPDATE jobs 
                SET status = 'open', assigned_provider_id = NULL
                WHERE job_id = %s AND customer_id = %s
                """,
                (job_id, customer_id)
            )
            conn.commit()

            # 10. Fetch updated job details
            cur.execute(
                """
                SELECT job_id, customer_id, title, status, assigned_provider_id, 
                       created_at, updated_at
                FROM jobs
                WHERE job_id = %s
                """,
                (job_id,)
            )
            updated_job = cur.fetchone()

        # 11. Format response
        job = {
            "job_id": updated_job["job_id"],
            "title": updated_job["title"],
            "status": updated_job["status"],
            "assigned_provider_id": updated_job["assigned_provider_id"],
            "created_at": updated_job["created_at"].isoformat() if updated_job["created_at"] else None,
            "updated_at": updated_job["updated_at"].isoformat() if updated_job["updated_at"] else None
        }

        return _response(200, {
            "message": "Provider unassigned successfully",
            "job": job
        })

    except Exception as e:
        print(f"Error unassigning provider: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "pathParameters": {
            "job_id": "1"
        }
    }

    print("🔍 Running local test for unassign_job.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
