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
    Get detailed information about a specific job.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Path Parameter:
    - job_id: ID of the job to retrieve
    
    Authorization:
    - Customer can only view their own jobs
    
    Returns:
    - 200: Job details with provider info if assigned
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

            # 5. Get job details with provider info and application count
            cur.execute(
                """
                SELECT 
                    j.job_id, j.customer_id, j.title, j.description, j.category,
                    j.location_address, j.location_city, j.location_state, j.location_zip,
                    j.preferred_date, j.preferred_time, j.budget_min, j.budget_max,
                    j.status, j.assigned_provider_id, j.created_at, j.updated_at,
                    sp.name as provider_name,
                    sp.rating as provider_rating,
                    sp.phone_number as provider_phone,
                    COUNT(ja.application_id) as application_count
                FROM jobs j
                LEFT JOIN service_providers sp ON j.assigned_provider_id COLLATE utf8mb4_0900_ai_ci = sp.provider_id
                LEFT JOIN job_applications ja ON j.job_id = ja.job_id
                WHERE j.job_id = %s
                GROUP BY j.job_id
                """,
                (job_id,)
            )
            job_row = cur.fetchone()
            
            if not job_row:
                return _response(404, {"message": "Job not found"})
            
            # 6. Authorization check - customer can only view their own jobs
            if job_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You can only view your own jobs"})

        # 7. Format response
        job = {
            "job_id": job_row["job_id"],
            "title": job_row["title"],
            "description": job_row["description"],
            "category": job_row["category"],
            "location": {
                "address": job_row["location_address"],
                "city": job_row["location_city"],
                "state": job_row["location_state"],
                "zip": job_row["location_zip"]
            },
            "preferred_date": str(job_row["preferred_date"]) if job_row["preferred_date"] else None,
            "preferred_time": str(job_row["preferred_time"]) if job_row["preferred_time"] else None,
            "budget": {
                "min": float(job_row["budget_min"]) if job_row["budget_min"] else None,
                "max": float(job_row["budget_max"]) if job_row["budget_max"] else None
            },
            "status": job_row["status"],
            "application_count": job_row["application_count"],
            "created_at": job_row["created_at"].isoformat() if job_row["created_at"] else None,
            "updated_at": job_row["updated_at"].isoformat() if job_row["updated_at"] else None
        }

        # 8. Add provider details if job is assigned
        if job_row["assigned_provider_id"]:
            job["assigned_provider"] = {
                "provider_id": job_row["assigned_provider_id"],
                "name": job_row["provider_name"],
                "rating": float(job_row["provider_rating"]) if job_row["provider_rating"] else None,
                "phone": job_row["provider_phone"]
            }
        else:
            job["assigned_provider"] = None

        return _response(200, {
            "job": job
        })

    except Exception as e:
        print(f"Error fetching job details: {e}")
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

    print("🔍 Running local test for get_job_details.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
