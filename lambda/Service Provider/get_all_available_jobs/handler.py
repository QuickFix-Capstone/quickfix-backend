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
    Get all jobs.
    Optional:
    - Public listing (OPEN jobs)
    - Later: filter by provider, category, city
    """

    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    job_id,
                    customer_id,
                    title,
                    description,
                    category,
                    location_address,
                    location_city,
                    location_state,
                    location_zip,
                    preferred_date,
                    preferred_time,
                    budget_min,
                    budget_max,
                    status,
                    assigned_provider_id,
                    created_at,
                    updated_at
                FROM jobs
                WHERE status = 'OPEN'
                ORDER BY created_at DESC
            """)

            rows = cur.fetchall()

        jobs = []
        for row in rows:
            jobs.append({
                "job_id": row["job_id"],
                "customer_id": row["customer_id"],
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
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
            })

        return _response(200, {
            "count": len(jobs),
            "jobs": jobs
        })

    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass
