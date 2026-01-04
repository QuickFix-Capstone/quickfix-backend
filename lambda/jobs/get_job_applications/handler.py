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
    Get all applications for a specific job (customer view).
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    - Only the job owner (customer) can view applications
    
    Path Parameter:
    - job_id: ID of the job to retrieve applications for
    
    Authorization:
    - Customer can only view applications for their own jobs
    
    Returns:
    - 200: List of applications with provider details
    - 401: Unauthorized
    - 403: Forbidden (not customer's job)
    - 404: Job not found or customer not found
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

            # 5. Verify customer owns this job
            cur.execute(
                "SELECT customer_id FROM jobs WHERE job_id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()
            
            if not job_row:
                return _response(404, {"message": "Job not found"})
            
            if job_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You can only view applications for your own jobs"})

            # 6. Get all applications for this job with provider details
            cur.execute(
                """
                SELECT 
                    ja.application_id, ja.job_id, ja.provider_id, ja.proposed_price,
                    ja.message, ja.status, ja.created_at,
                    sp.name, sp.business_name, sp.rating, sp.phone_number,
                    COUNT(DISTINCT b.booking_id) as completed_jobs
                FROM job_applications ja
                JOIN service_providers sp ON ja.provider_id COLLATE utf8mb4_0900_ai_ci = sp.provider_id
                LEFT JOIN bookings b ON sp.provider_id = b.provider_id AND b.status = 'completed'
                WHERE ja.job_id = %s
                GROUP BY ja.application_id, ja.job_id, ja.provider_id, ja.proposed_price,
                         ja.message, ja.status, ja.created_at,
                         sp.name, sp.business_name, sp.rating, sp.phone_number
                ORDER BY 
                    CASE ja.status 
                        WHEN 'pending' THEN 1 
                        WHEN 'accepted' THEN 2 
                        WHEN 'rejected' THEN 3 
                    END,
                    ja.created_at ASC
                """,
                (job_id,)
            )
            applications_rows = cur.fetchall()

        # 7. Format response
        applications = []
        for row in applications_rows:
            application = {
                "application_id": row["application_id"],
                "provider": {
                    "provider_id": row["provider_id"],
                    "name": row["name"],
                    "business_name": row["business_name"],
                    "rating": float(row["rating"]) if row["rating"] is not None else 0.0,
                    "phone": row["phone_number"],
                    "completed_jobs": row["completed_jobs"]
                },
                "proposed_price": float(row["proposed_price"]) if row["proposed_price"] else None,
                "message": row["message"],
                "status": row["status"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            applications.append(application)

        return _response(200, {
            "job_id": int(job_id),
            "application_count": len(applications),
            "applications": applications
        })

    except Exception as e:
        print(f"Error fetching job applications: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    # Test event with mock JWT claims
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

    print("🔍 Running local test for get_job_applications.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
