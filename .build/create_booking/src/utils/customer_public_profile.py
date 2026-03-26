from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple


VALID_INTERACTION_TYPES = {
    "job_view",
    "job_application",
    "booking",
    "message",
    "job_completed",
}


def get_provider_id_from_sub(conn, cognito_sub: str) -> Optional[str]:
    """Resolve provider_id from Cognito sub."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT provider_id FROM service_providers WHERE cognito_sub = %s LIMIT 1",
            (cognito_sub,),
        )
        row = cur.fetchone()
    return row["provider_id"] if row else None


def can_provider_view_customer(conn, provider_id: str, customer_id: int) -> Tuple[bool, str]:
    """
    Check provider access based on customer profile_visibility and prior interactions.
    Returns tuple: (allowed, reason)
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT profile_visibility FROM customers WHERE customer_id = %s",
            (customer_id,),
        )
        customer_row = cur.fetchone()

        if not customer_row:
            return False, "Customer not found"

        visibility = customer_row.get("profile_visibility") or "restricted"

        if visibility == "public":
            return True, ""

        if visibility == "private":
            return False, "Profile is private"

        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM provider_customer_interactions
            WHERE provider_id = %s AND customer_id = %s
            """,
            (provider_id, customer_id),
        )
        interactions = cur.fetchone()
        has_access = bool(interactions and interactions["count"] > 0)
        if has_access:
            return True, ""
        return False, "No prior interaction with this customer"


def calculate_customer_stats(conn, customer_id: int) -> Optional[Dict[str, Any]]:
    """Calculate fresh customer statistics from source tables."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COALESCE(c.total_review_count, 0) AS review_count,
                COALESCE(COUNT(DISTINCT CASE
                    WHEN j.created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                    THEN j.job_id
                END), 0) AS jobs_posted_6mo,
                COALESCE(COUNT(DISTINCT CASE
                    WHEN j.status = 'completed'
                    THEN j.job_id
                END), 0) AS jobs_completed,
                COALESCE(COUNT(DISTINCT CASE
                    WHEN j.status = 'cancelled'
                    THEN j.job_id
                END), 0) AS jobs_cancelled,
                CASE
                    WHEN COUNT(DISTINCT j.job_id) > 0
                    THEN ROUND(
                        COUNT(DISTINCT CASE WHEN j.status = 'completed' THEN j.job_id END) * 100.0
                        / COUNT(DISTINCT j.job_id), 2
                    )
                    ELSE NULL
                END AS completion_rate,
                CASE
                    WHEN COUNT(DISTINCT j.job_id) > 0
                    THEN ROUND(
                        COUNT(DISTINCT CASE WHEN j.status = 'cancelled' THEN j.job_id END) * 100.0
                        / COUNT(DISTINCT j.job_id), 2
                    )
                    ELSE NULL
                END AS cancellation_rate
            FROM customers c
            LEFT JOIN jobs j ON c.customer_id = j.customer_id
            WHERE c.customer_id = %s
            GROUP BY c.customer_id, c.total_review_count
            """,
            (customer_id,),
        )
        return cur.fetchone()


def upsert_customer_stats(conn, customer_id: int, stats: Dict[str, Any]) -> None:
    """Store/rewrite cached stats row."""
    if not stats:
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO customer_profile_stats
            (customer_id, review_count, jobs_posted_6mo, jobs_completed,
             jobs_cancelled, completion_rate, cancellation_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              review_count = VALUES(review_count),
              jobs_posted_6mo = VALUES(jobs_posted_6mo),
              jobs_completed = VALUES(jobs_completed),
              jobs_cancelled = VALUES(jobs_cancelled),
              completion_rate = VALUES(completion_rate),
              cancellation_rate = VALUES(cancellation_rate),
              last_updated = CURRENT_TIMESTAMP
            """,
            (
                customer_id,
                stats.get("review_count") or 0,
                stats.get("jobs_posted_6mo") or 0,
                stats.get("jobs_completed") or 0,
                stats.get("jobs_cancelled") or 0,
                stats.get("completion_rate"),
                stats.get("cancellation_rate"),
            ),
        )
    conn.commit()


def is_stats_stale(last_updated: Optional[datetime], ttl_minutes: int = 60) -> bool:
    if not last_updated:
        return True
    return last_updated < (datetime.utcnow() - timedelta(minutes=ttl_minutes))


def track_provider_interaction(
    conn,
    provider_id: str,
    customer_id: int,
    interaction_type: str,
    job_id: Optional[int] = None,
    booking_id: Optional[int] = None,
) -> None:
    """
    Record provider-customer interaction for profile access control.
    Never raises to caller.
    """
    if interaction_type not in VALID_INTERACTION_TYPES:
        return

    if not provider_id or not customer_id:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO provider_customer_interactions
                    (provider_id, customer_id, interaction_type, job_id, booking_id)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
                """,
                (provider_id, customer_id, interaction_type, job_id, booking_id),
            )
        conn.commit()
    except Exception as exc:
        print(f"Failed to track provider interaction: {exc}")
