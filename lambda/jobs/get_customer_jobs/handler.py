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
    Get all jobs for the authenticated customer.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Query Parameters:
    - status (optional): Filter by job status (open, assigned, in_progress, completed, cancelled)
    - limit (optional): Number of results per page (default 20, max 100)
    - offset (optional): Pagination offset (default 0)
    
    Returns:
    - 200: List of jobs with application counts
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

    # 2. Parse query parameters
    query_params = event.get("queryStringParameters") or {}
    status_filter = query_params.get("status")
    
    try:
        limit = int(query_params.get("limit", 20))
        offset = int(query_params.get("offset", 0))
        
        # Enforce limits
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        if offset < 0:
            offset = 0
            
    except ValueError:
        return _response(400, {"message": "Invalid limit or offset parameter"})

    # 3. Validate status filter if provided
    valid_statuses = ['open', 'assigned', 'in_progress', 'completed', 'cancelled']
    if status_filter and status_filter not in valid_statuses:
        return _response(400, {
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        })

    # 4. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 5. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 6. Build query with optional status filter
            base_query = """
                SELECT 
                    j.job_id, j.title, j.description, j.category,
                    j.location_address, j.location_city, j.location_state, j.location_zip,
                    j.preferred_date, j.preferred_time, j.budget_min, j.budget_max,
                    j.status, j.assigned_provider_id, j.created_at, j.updated_at,
                    COUNT(ja.application_id) as application_count
                FROM jobs j
                LEFT JOIN job_applications ja ON j.job_id = ja.job_id
                WHERE j.customer_id = %s
            """
            
            params = [customer_id]
            
            if status_filter:
                base_query += " AND j.status = %s"
                params.append(status_filter)
            
            base_query += """
                GROUP BY j.job_id
                ORDER BY j.created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            cur.execute(base_query, params)
            job_rows = cur.fetchall()

            # 7. Get total count
            count_query = "SELECT COUNT(*) as total FROM jobs WHERE customer_id = %s"
            count_params = [customer_id]
            
            if status_filter:
                count_query += " AND status = %s"
                count_params.append(status_filter)
            
            cur.execute(count_query, count_params)
            total_count = cur.fetchone()["total"]

        # 8. Format response
        jobs = []
        for row in job_rows:
            job = {
                "job_id": row["job_id"],
                "title": row["title"],
                "description": row["description"],
                "category": row["category"],
                "location": {
                    "address": row["location_address"],
                    "city": row["location_city"],
                    "state": row["location_state"],
                    "zip": row["location_zip"]
                },
                "preferred_date": str(row["preferred_date"]) if row["preferred_date"] else None,
                "preferred_time": str(row["preferred_time"]) if row["preferred_time"] else None,
                "budget": {
                    "min": float(row["budget_min"]) if row["budget_min"] else None,
                    "max": float(row["budget_max"]) if row["budget_max"] else None
                },
                "status": row["status"],
                "assigned_provider_id": row["assigned_provider_id"],
                "application_count": row["application_count"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            }
            jobs.append(job)

        return _response(200, {
            "jobs": jobs,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        print(f"Error fetching jobs: {e}")
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
        "queryStringParameters": {
            "limit": "10",
            "offset": "0"
        }
    }

    print("🔍 Running local test for get_customer_jobs.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
