import json
import os
import sys
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import (
        can_provider_view_customer,
        get_provider_id_from_sub,
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import (
        can_provider_view_customer,
        get_provider_id_from_sub,
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


def _parse_limit(raw_limit: Any) -> int:
    try:
        limit = int(str(raw_limit))
    except Exception:
        return 10
    return max(1, min(50, limit))


def _parse_cursor(raw_cursor: Any):
    if raw_cursor in (None, ""):
        return None
    try:
        cursor = int(str(raw_cursor))
    except Exception:
        return None
    return cursor if cursor > 0 else None


def _sort_clause(sort_key: str) -> str:
    if sort_key == "highest":
        return "r.rating DESC, r.created_at DESC, r.review_id DESC"
    if sort_key == "lowest":
        return "r.rating ASC, r.created_at DESC, r.review_id DESC"
    return "r.created_at DESC, r.review_id DESC"


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

    query_params = event.get("queryStringParameters") or {}
    limit = _parse_limit(query_params.get("limit", 10))
    cursor = _parse_cursor(query_params.get("cursor"))
    sort = str(query_params.get("sort", "recent")).strip().lower()
    if sort not in {"recent", "highest", "lowest"}:
        return _response(400, {"message": "Invalid sort. Must be one of: recent, highest, lowest"})

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

        cursor_clause = ""
        params = [customer_id]
        if cursor is not None:
            cursor_clause = " AND r.review_id < %s"
            params.append(cursor)

        params.append(limit + 1)
        order_by = _sort_clause(sort)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    r.review_id,
                    r.rating,
                    r.comment,
                    r.created_at,
                    r.job_id,
                    j.category AS job_category,
                    sp.business_name AS provider_name,
                    DATE_FORMAT(r.created_at, '%%M %%d, %%Y') AS formatted_date
                FROM provider_customer_reviews r
                LEFT JOIN jobs j ON r.job_id = j.job_id
                LEFT JOIN service_providers sp ON r.provider_id = sp.provider_id
                WHERE r.customer_id = %s
                  AND r.is_visible = TRUE
                  {cursor_clause}
                ORDER BY {order_by}
                LIMIT %s
                """,
                tuple(params),
            )
            rows = cur.fetchall()

        has_more = len(rows) > limit
        items = rows[:limit] if has_more else rows
        next_cursor = items[-1]["review_id"] if has_more and items else None

        return _response(
            200,
            {
                "reviews": items,
                "pagination": {
                    "has_more": has_more,
                    "next_cursor": next_cursor,
                    "limit": limit,
                },
            },
        )
    except Exception as exc:
        print(f"Error in get_customer_public_reviews: {exc}")
        return _response(500, {"message": "Internal server error"})
    finally:
        try:
            conn.close()
        except Exception:
            pass
