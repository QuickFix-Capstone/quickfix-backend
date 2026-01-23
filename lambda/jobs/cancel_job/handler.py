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
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Cancel a job posting.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Path Parameter:
    - job_id: ID of the job to cancel
    
    Authorization:
    - Customer can only cancel their own jobs
    
    Logic:
    - Set job status to "cancelled"
    - Reject all pending applications for this job
    
    Returns:
    - 200: Job cancelled successfully
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

            # 5. Check if job exists and belongs to customer
            cur.execute(
                "SELECT customer_id, status, title FROM jobs WHERE job_id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()
            
            if not job_row:
                return _response(404, {"message": "Job not found"})
            
            # 6. Authorization check
            if job_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You can only cancel your own jobs"})

            # 7. Update job status to cancelled
            cur.execute(
                "UPDATE jobs SET status = 'cancelled' WHERE job_id = %s",
                (job_id,)
            )

            # 8. Reject all pending applications for this job
            cur.execute(
                """
                UPDATE job_applications 
                SET status = 'rejected' 
                WHERE job_id = %s AND status = 'pending'
                """,
                (job_id,)
            )
            
            rejected_count = cur.rowcount
            
            conn.commit()

        return _response(200, {
            "message": "Job cancelled successfully",
            "job_id": int(job_id),
            "title": job_row["title"],
            "previous_status": job_row["status"],
            "applications_rejected": rejected_count
        })

    except Exception as e:
        print(f"Error cancelling job: {e}")
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
            "job_id": "2"
        }
    }

    print("🔍 Running local test for cancel_job.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
