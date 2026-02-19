import json
import os
import sys
from typing import Any, Dict, List

try:
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import (
        calculate_customer_stats,
        can_provider_view_customer,
        get_provider_id_from_sub,
        is_stats_stale,
        upsert_customer_stats,
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import (
        calculate_customer_stats,
        can_provider_view_customer,
        get_provider_id_from_sub,
        is_stats_stale,
        upsert_customer_stats,
    )


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def _is_new_customer(created_at) -> bool:
    if not created_at:
        return False
    from datetime import datetime, timedelta

    return created_at > (datetime.utcnow() - timedelta(days=90))


def _generate_badges(stats: Dict[str, Any], created_at, avg_rating: float) -> List[Dict[str, str]]:
    badges: List[Dict[str, str]] = []

    if _is_new_customer(created_at):
        badges.append({"type": "new_customer", "label": "New Customer"})

    if (stats.get("jobs_posted_6mo") or 0) >= 10:
        badges.append({"type": "frequent_poster", "label": "Frequent Poster"})

    completion_rate = stats.get("completion_rate")
    if completion_rate is not None and float(completion_rate) >= 90:
        badges.append({"type": "reliable", "label": "Reliable"})

    if avg_rating >= 4.5:
        badges.append({"type": "highly_rated", "label": "Highly Rated"})

    return badges


def handler(event, context):
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        provider_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not provider_sub:
        return _response(401, {"message": "Unauthorized: Missing provider identity"})

    try:
        customer_id = int(str(event["pathParameters"]["customer_id"]))
        if customer_id <= 0:
            raise ValueError
    except Exception:
        return _response(400, {"message": "Invalid customer_id"})

    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        provider_id = get_provider_id_from_sub(conn, provider_sub)
        if not provider_id:
            return _response(403, {"message": "Provider profile not found"})

        allowed, reason = can_provider_view_customer(conn, provider_id, customer_id)
        if not allowed:
            if reason == "Customer not found":
                return _response(404, {"message": reason})
            return _response(403, {"message": reason or "Access denied"})

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    customer_id,
                    display_name,
                    first_name,
                    last_name,
                    avatar_url,
                    created_at,
                    average_rating
                FROM customers
                WHERE customer_id = %s
                LIMIT 1
                """,
                (customer_id,),
            )
            customer_row = cur.fetchone()

        if not customer_row:
            return _response(404, {"message": "Customer not found"})

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT customer_id, review_count, jobs_posted_6mo, jobs_completed,
                       jobs_cancelled, completion_rate, cancellation_rate,
                       avg_response_time_minutes, last_updated
                FROM customer_profile_stats
                WHERE customer_id = %s
                LIMIT 1
                """,
                (customer_id,),
            )
            cached_stats = cur.fetchone()

        if not cached_stats or is_stats_stale(cached_stats.get("last_updated")):
            fresh_stats = calculate_customer_stats(conn, customer_id)
            if fresh_stats:
                upsert_customer_stats(conn, customer_id, fresh_stats)
                stats = {
                    "customer_id": customer_id,
                    "review_count": fresh_stats.get("review_count") or 0,
                    "jobs_posted_6mo": fresh_stats.get("jobs_posted_6mo") or 0,
                    "jobs_completed": fresh_stats.get("jobs_completed") or 0,
                    "jobs_cancelled": fresh_stats.get("jobs_cancelled") or 0,
                    "completion_rate": fresh_stats.get("completion_rate"),
                    "cancellation_rate": fresh_stats.get("cancellation_rate"),
                    "avg_response_time_minutes": None,
                }
            else:
                stats = {
                    "customer_id": customer_id,
                    "review_count": 0,
                    "jobs_posted_6mo": 0,
                    "jobs_completed": 0,
                    "jobs_cancelled": 0,
                    "completion_rate": None,
                    "cancellation_rate": None,
                    "avg_response_time_minutes": None,
                }
        else:
            stats = cached_stats

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.review_id,
                    r.rating,
                    r.comment,
                    r.created_at,
                    j.category AS job_category,
                    DATE_FORMAT(r.created_at, '%%M %%Y') AS review_date
                FROM provider_customer_reviews r
                LEFT JOIN jobs j ON r.job_id = j.job_id
                WHERE r.customer_id = %s
                  AND r.is_visible = TRUE
                ORDER BY r.created_at DESC
                LIMIT 5
                """,
                (customer_id,),
            )
            recent_reviews = cur.fetchall()

            cur.execute(
                """
                SELECT category, COUNT(*) AS count
                FROM jobs
                WHERE customer_id = %s
                  AND category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
                """,
                (customer_id,),
            )
            job_categories = cur.fetchall()

        avg_rating = float(customer_row["average_rating"] or 0)
        display_name = customer_row["display_name"]
        if not display_name:
            last_initial = ((customer_row["last_name"] or "")[:1] + ".") if customer_row["last_name"] else ""
            display_name = f"{customer_row['first_name'] or ''} {last_initial}".strip()

        badges = _generate_badges(stats, customer_row.get("created_at"), avg_rating)

        return _response(
            200,
            {
                "customer": {
                    "customer_id": customer_row["customer_id"],
                    "display_name": display_name,
                    "avatar_url": customer_row["avatar_url"],
                    "member_since": customer_row["created_at"],
                    "is_new": _is_new_customer(customer_row["created_at"]),
                },
                "stats": {
                    "avg_rating": avg_rating,
                    "review_count": stats.get("review_count") or 0,
                    "jobs_posted_6mo": stats.get("jobs_posted_6mo") or 0,
                    "jobs_completed": stats.get("jobs_completed") or 0,
                    "jobs_cancelled": stats.get("jobs_cancelled") or 0,
                    "completion_rate": float(stats["completion_rate"]) if stats.get("completion_rate") is not None else None,
                    "cancellation_rate": float(stats["cancellation_rate"]) if stats.get("cancellation_rate") is not None else None,
                    "avg_response_time_minutes": stats.get("avg_response_time_minutes"),
                },
                "recent_reviews": recent_reviews,
                "job_categories": job_categories,
                "badges": badges,
            },
        )
    except Exception as exc:
        print(f"Error in get_customer_public_profile: {exc}")
        return _response(500, {"message": "Internal server error"})
    finally:
        try:
            conn.close()
        except Exception:
            pass
