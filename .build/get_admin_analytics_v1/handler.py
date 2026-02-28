import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.utils.auth import extract_jwt_claims, is_cognito_administrator
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.auth import extract_jwt_claims, is_cognito_administrator


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body, default=_json_default),
    }


def _count(cur, table_name: str) -> int:
    cur.execute(f"SELECT COUNT(*) AS total_count FROM {table_name}")
    row = cur.fetchone() or {}
    return int(row.get("total_count", 0))


def _status_distribution(cur, table_name: str):
    cur.execute(
        f"""
        SELECT status, COUNT(*) AS count
        FROM {table_name}
        GROUP BY status
        ORDER BY status
        """
    )
    rows = cur.fetchall() or []
    return [{"status": row.get("status"), "count": int(row.get("count", 0))} for row in rows]


def _monthly_growth(cur, table_name: str):
    cur.execute(
        f"""
        SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS count
        FROM {table_name}
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY month
        ORDER BY month
        """
    )
    rows = cur.fetchall() or []
    return [{"month": row.get("month"), "count": int(row.get("count", 0))} for row in rows]


def handler(event, context):
    claims = extract_jwt_claims(event)
    cognito_sub = claims.get("sub")
    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not is_cognito_administrator(claims):
        return _response(403, {"message": "Forbidden: Admin access required"})

    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            customers_total = _count(cur, "customers")
            providers_total = _count(cur, "service_providers")
            jobs_total = _count(cur, "jobs")
            bookings_total = _count(cur, "bookings")
            reviews_total = _count(cur, "customer_provider_reviews")

            # Track commitment metrics now that jobs.assigned_at is available.
            cur.execute(
                """
                SELECT
                    COUNT(*) AS committed_jobs,
                    AVG(TIMESTAMPDIFF(MINUTE, created_at, assigned_at)) AS avg_minutes_to_commitment
                FROM jobs
                WHERE assigned_at IS NOT NULL
                  AND status IN ('assigned', 'in_progress', 'completed')
                """
            )
            commitment = cur.fetchone() or {}

            cur.execute(
                """
                SELECT
                    COUNT(*) AS direct_jobs_committed,
                    AVG(TIMESTAMPDIFF(MINUTE, created_at, assigned_at)) AS avg_minutes_direct
                FROM jobs
                WHERE assigned_at IS NOT NULL
                  AND booking_id IS NULL
                  AND status IN ('assigned', 'in_progress', 'completed')
                """
            )
            direct_commitment = cur.fetchone() or {}

            cur.execute(
                """
                SELECT
                    COUNT(*) AS booking_jobs_committed,
                    AVG(TIMESTAMPDIFF(MINUTE, created_at, assigned_at)) AS avg_minutes_booking
                FROM jobs
                WHERE assigned_at IS NOT NULL
                  AND booking_id IS NOT NULL
                  AND status IN ('assigned', 'in_progress', 'completed')
                """
            )
            booking_commitment = cur.fetchone() or {}

            job_status_distribution = _status_distribution(cur, "jobs")
            booking_status_distribution = _status_distribution(cur, "bookings")

            monthly_growth = {
                "jobs": _monthly_growth(cur, "jobs"),
                "customers": _monthly_growth(cur, "customers"),
                "bookings": _monthly_growth(cur, "bookings"),
                "providers": _monthly_growth(cur, "service_providers"),
            }

        return _response(
            200,
            {
                "message": "Admin analytics retrieved successfully",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "admin_sub": cognito_sub,
                "metrics": {
                    "customers_total": customers_total,
                    "providers_total": providers_total,
                    "jobs_total": jobs_total,
                    "bookings_total": bookings_total,
                    "reviews_total": reviews_total,
                    "commitment": {
                        "committed_jobs": int(commitment.get("committed_jobs", 0)),
                        "avg_minutes_to_commitment": commitment.get("avg_minutes_to_commitment"),
                        "direct_jobs_committed": int(direct_commitment.get("direct_jobs_committed", 0)),
                        "avg_minutes_direct": direct_commitment.get("avg_minutes_direct"),
                        "booking_jobs_committed": int(booking_commitment.get("booking_jobs_committed", 0)),
                        "avg_minutes_booking": booking_commitment.get("avg_minutes_booking"),
                    },
                    "job_status_distribution": job_status_distribution,
                    "booking_status_distribution": booking_status_distribution,
                    "monthly_growth": monthly_growth,
                },
            },
        )
    except Exception as exc:
        print(f"Error in get_admin_analytics_v1: {exc}")
        return _response(500, {"message": "Internal server error while retrieving admin analytics"})
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "test-admin-sub",
                        "cognito:groups": ["Administrator"],
                    }
                }
            }
        }
    }
    print(handler(test_event, None))
