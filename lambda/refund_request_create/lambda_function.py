import os
from src.response import ok, err
from src.event import get_jwt_sub, get_json_body
from src.db import get_conn
from src.sql_helpers import get_customer_id_by_sub, get_payment_by_id

MIN_LEN = int(os.getenv("REFUND_MIN_REASON_LEN", "30"))
MAX_ATTACH = int(os.getenv("REFUND_MAX_FILES", "5"))

def lambda_handler(event, context):
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    if (event.get("httpMethod") or "").upper() == "OPTIONS":
        return ok({"ok": True}, 200)

    body = get_json_body(event)
    payment_id = body.get("payment_id")
    job_id = body.get("job_id")
    reason_code = (body.get("reason_code") or "").strip()
    reason_text = (body.get("reason_text") or "").strip()
    attachments = body.get("attachments") or []

    if not payment_id or not job_id:
        return err("payment_id and job_id required", 400)
    if not reason_code:
        return err("reason_code required", 400)
    if len(reason_text) < MIN_LEN:
        return err(f"reason_text must be at least {MIN_LEN} chars", 400)
    if not isinstance(attachments, list):
        return err("attachments must be an array", 400)
    if len(attachments) > MAX_ATTACH:
        return err(f"Too many attachments (max {MAX_ATTACH})", 400)

    conn = None
    try:
        conn = get_conn()
        customer_id = get_customer_id_by_sub(conn, sub)
        if not customer_id:
            return err("Customer not found", 403)

        payment = get_payment_by_id(conn, payment_id)
        if not payment:
            return err("Payment not found", 404)

        if int(payment.get("customer_id")) != int(customer_id):
            return err("Forbidden", 403)

        if int(payment.get("job_id")) != int(job_id):
            return err("job_id does not match payment", 400)

        if (payment.get("status") or "").lower() != "paid":
            return err("Refunds can only be requested for PAID payments", 400)

        # prevent duplicates
        with conn.cursor() as cur:
            cur.execute(
                "SELECT refund_request_id FROM refund_request "
                "WHERE payment_id=%s AND status='PENDING' LIMIT 1",
                (payment_id,),
            )
            if cur.fetchone():
                return err("Refund already requested for this payment", 409)

        provider_id = payment.get("provider_id") or payment.get("assigned_provider_id")
        payment_method = payment.get("payment_method") or payment.get("method") or "unknown"

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO refund_request "
                "(payment_id, job_id, customer_id, provider_id, reason_code, reason_text, payment_method, status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,'PENDING')",
                (payment_id, job_id, customer_id, provider_id, reason_code, reason_text, payment_method),
            )
            refund_request_id = cur.lastrowid

            for key in attachments:
                cur.execute(
                    "INSERT INTO refund_request_attachment (refund_request_id, s3_key) VALUES (%s,%s)",
                    (refund_request_id, key),
                )

        conn.commit()
        return ok({"refund_request_id": refund_request_id, "status": "PENDING"}, 201)

    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return err("Server error", 500, str(e))
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
