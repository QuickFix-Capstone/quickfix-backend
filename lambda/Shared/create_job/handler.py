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
    Create a new job posting.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Expected JSON input:
    {
      "title": "Fix leaking kitchen sink",
      "description": "Sink has been leaking for 2 days...",
      "category": "plumber",
      "location_address": "123 Main St",
      "location_city": "Toronto",
      "location_state": "ON",
      "location_zip": "M5H 1J9",
      "preferred_date": "2026-01-15",  # optional
      "preferred_time": "14:00",  # optional
      "budget_min": 100.00,  # optional
      "budget_max": 150.00  # optional
    }
    
    Returns:
    - 201: Job created successfully
    - 400: Invalid input
    - 401: Unauthorized
    - 404: Customer not found
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

    # 2. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 3. Validate required fields
    required_fields = ["title", "description", "location_address"]
    
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return _response(400, {
            "message": "Missing required fields",
            "missing": missing
        })

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

            # 9. Create job
            sql = """
                INSERT INTO jobs
                    (customer_id, title, description, category, location_address,
                     location_city, location_state, location_zip, preferred_date,
                     preferred_time, budget_min, budget_max)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(sql, (
                customer_id,
                data["title"],
                data["description"],
                data.get("category"),
                data["location_address"],
                data.get("location_city"),
                data.get("location_state"),
                data.get("location_zip"),
                data.get("preferred_date"),
                data.get("preferred_time"),
                budget_min,
                budget_max
            ))
            
            conn.commit()
            job_id = cur.lastrowid

            # 10. Fetch created job
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
            job_row = cur.fetchone()

        job = {
            "job_id": job_row["job_id"],
            "customer_id": job_row["customer_id"],
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
            "assigned_provider_id": job_row["assigned_provider_id"],
            "created_at": job_row["created_at"].isoformat() if job_row["created_at"] else None,
            "updated_at": job_row["updated_at"].isoformat() if job_row["updated_at"] else None
        }

        return _response(201, {
            "message": "Job created successfully",
            "job": job
        })

    except IntegrityError as e:
        print(f"Integrity error: {e}")
        return _response(400, {"message": "Failed to create job due to data constraint"})

    except Exception as e:
        print(f"Error creating job: {e}")
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
        "body": json.dumps({
            "title": "Fix leaking kitchen sink",
            "description": "Sink has been leaking for 2 days, need urgent repair",
            "category": "plumber",
            "location_address": "123 Main St",
            "location_city": "Toronto",
            "location_state": "ON",
            "location_zip": "M5H 1J9",
            "preferred_date": "2026-01-15",
            "preferred_time": "14:00",
            "budget_min": 100.00,
            "budget_max": 150.00
        })
    }

    print("🔍 Running local test for create_job.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
