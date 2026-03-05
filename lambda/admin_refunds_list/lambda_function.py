from src.response import ok, err
from src.event import get_jwt_sub
from src.db import get_conn

def _qs(event, key, default=None):
    qs = event.get("queryStringParameters") or {}
    v = qs.get(key)
    return default if v is None or v == "" else v

def lambda_handler(event, context):
    # Route should be protected by QuickFixAdminJwtAuthorizer
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    status = _qs(event, "status", None)  # PENDING/APPROVED/REJECTED/CANCELLED

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    "SELECT refund_request_id, payment_id, job_id, customer_id, provider_id, "
                    "reason_code, status, requested_at "
                    "FROM refund_request "
                    "WHERE status=%s "
                    "ORDER BY requested_at DESC "
                    "LIMIT 200",
                    (status,)
                )
            else:
                cur.execute(
                    "SELECT refund_request_id, payment_id, job_id, customer_id, provider_id, "
                    "reason_code, status, requested_at "
                    "FROM refund_request "
                    "ORDER BY requested_at DESC "
                    "LIMIT 200"
                )
            rows = cur.fetchall()

        return ok({"items": rows})
    except Exception as e:
        return err("Server error", 500, str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
