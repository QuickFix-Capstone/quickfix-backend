import json
import sys
import os
from typing import Any, Dict
from datetime import datetime, date
from pymysql.err import IntegrityError

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


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
    Update job details.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Path Parameter:
    - job_id: ID of the job to update
    
    Authorization:
    - Customer can only update their own jobs
    - Job must be in "open" status
    
    Updatable Fields:
    - title, description, category
    - location_address, location_city, location_state, location_zip
    - preferred_date, preferred_time
    - budget_min, budget_max
    
    Returns:
    - 200: Job updated successfully
    - 400: Invalid input or job not in open status
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

    # 3. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    if not data:
        return _response(400, {"message": "Request body cannot be empty"})

    # 4. Validate budget range if provided
    budget_min = data.get("budget_min")
    budget_max = data.get("budget_max")
    
    if budget_min is not None and budget_max is not None:
        if budget_min > budget_max:
            return _response(400, {"message": "budget_min cannot be greater than budget_max"})

    # 5. Validate preferred date if provided
    if data.get("preferred_date"):
        try:
            preferred_date = datetime.strptime(data["preferred_date"], "%Y-%m-%d").date()
            if preferred_date < date.today():
                return _response(400, {"message": "Preferred date must be in the future"})
        except ValueError:
            return _response(400, {"message": "Invalid date format. Use YYYY-MM-DD"})

    # 6. Validate preferred time format if provided
    if data.get("preferred_time"):
        try:
            datetime.strptime(data["preferred_time"], "%H:%M")
        except ValueError:
            return _response(400, {"message": "Invalid time format. Use HH:MM"})

    # 7. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 8. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 9. Check if job exists and belongs to customer
            cur.execute(
                "SELECT customer_id, status FROM jobs WHERE job_id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()
            
            if not job_row:
                return _response(404, {"message": "Job not found"})
            
            # 10. Authorization check
            if job_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You can only update your own jobs"})
            
            # 11. Status check - can only update open jobs
            if job_row["status"] != "open":
                return _response(400, {"message": f"Cannot update job with status '{job_row['status']}'. Only 'open' jobs can be updated."})

            # 12. Build UPDATE query dynamically
            updatable_fields = {
                "title": data.get("title"),
                "description": data.get("description"),
                "category": data.get("category"),
                "location_address": data.get("location_address"),
                "location_city": data.get("location_city"),
                "location_state": data.get("location_state"),
                "location_zip": data.get("location_zip"),
                "preferred_date": data.get("preferred_date"),
                "preferred_time": data.get("preferred_time"),
                "budget_min": budget_min,
                "budget_max": budget_max
            }
            
            # Filter out None values
            fields_to_update = {k: v for k, v in updatable_fields.items() if v is not None}
            
            if not fields_to_update:
                return _response(400, {"message": "No fields to update"})
            
            # Build SET clause
            set_clause = ", ".join([f"{field} = %s" for field in fields_to_update.keys()])
            values = list(fields_to_update.values())
            values.append(job_id)
            
            # 13. Update job
            update_sql = f"UPDATE jobs SET {set_clause} WHERE job_id = %s"
            cur.execute(update_sql, values)
            conn.commit()

            # 14. Fetch updated job
            cur.execute(
                """
                SELECT job_id, customer_id, title, description, category,
                       location_address, location_city, location_state, location_zip,
                       preferred_date, preferred_time, budget_min, budget_max,
                       status, assigned_provider_id, created_at, updated_at
                FROM jobs
                WHERE job_id = %s
                """,
                (job_id,)
            )
            updated_job = cur.fetchone()

        # 15. Format response
        job = {
            "job_id": updated_job["job_id"],
            "title": updated_job["title"],
            "description": updated_job["description"],
            "category": updated_job["category"],
            "location": {
                "address": updated_job["location_address"],
                "city": updated_job["location_city"],
                "state": updated_job["location_state"],
                "zip": updated_job["location_zip"]
            },
            "preferred_date": str(updated_job["preferred_date"]) if updated_job["preferred_date"] else None,
            "preferred_time": str(updated_job["preferred_time"]) if updated_job["preferred_time"] else None,
            "budget": {
                "min": float(updated_job["budget_min"]) if updated_job["budget_min"] else None,
                "max": float(updated_job["budget_max"]) if updated_job["budget_max"] else None
            },
            "status": updated_job["status"],
            "assigned_provider_id": updated_job["assigned_provider_id"],
            "created_at": updated_job["created_at"].isoformat() if updated_job["created_at"] else None,
            "updated_at": updated_job["updated_at"].isoformat() if updated_job["updated_at"] else None
        }

        return _response(200, {
            "message": "Job updated successfully",
            "job": job
        })

    except Exception as e:
        print(f"Error updating job: {e}")
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
        },
        "body": json.dumps({
            "title": "Fix leaking kitchen sink - UPDATED",
            "budget_max": 200.00
        })
    }

    print("🔍 Running local test for update_job.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
