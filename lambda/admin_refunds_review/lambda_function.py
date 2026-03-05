from src.response import ok, err
from src.event import get_jwt_sub, get_json_body
from src.db import get_conn

def _path_param(event, key):
    pp = event.get("pathParameters") or {}
    return pp.get(key)

def lambda_handler(event, context):
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    refund_request_id = _path_param(event, "refund_request_id")
    if not refund_request_id:
        return err("refund_request_id required in path", 400)

    body = get_json_body(event) or {}
    action = (body.get("action") or "").strip().upper()  # APPROVE / REJECT
    admin_note = (body.get("admin_note") or "").strip()

    if action not in ("APPROVE", "REJECT"):
        return err("action must be APPROVE or REJECT", 400)

    new_status = "APPROVED" if action == "APPROVE" else "REJECTED"

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM refund_request WHERE refund_request_id=%s LIMIT 1",
                (refund_request_id,)
            )
            rr = cur.fetchone()

        if not rr:
            return err("Refund request not found", 404)

        if rr["status"] != "PENDING":
            return err(f"Cannot review a refund request in status {rr['status']}", 409)

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE refund_request "
                "SET status=%s, admin_note=%s, reviewed_at=NOW() "
                "WHERE refund_request_id=%s",
                (new_status, admin_note if admin_note else None, refund_request_id)
            )

        conn.commit()
        return ok({"refund_request_id": int(refund_request_id), "status": new_status})
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return err("Server error", 500, str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
