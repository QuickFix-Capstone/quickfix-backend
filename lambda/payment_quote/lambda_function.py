import os
from src.response import ok, err
from src.event import get_json_body, get_jwt_sub
from src.db import get_conn
from src.tax import get_rate
from src.money import to_cents, compute_amounts
from src.sql_helpers import get_customer_id_by_sub, get_job_for_payment, get_payment_by_job

APP_FEE_RATE = float(os.getenv("APP_FEE_RATE", "0.07"))

def handler(event, context):
    try:
        body = get_json_body(event)
        job_id = body.get("job_id")
        if not job_id:
            return err("job_id is required", 400)

        sub = get_jwt_sub(event)
        if not sub:
            return err("Unauthorized", 401)

        conn = get_conn()
        try:
            customer_id = get_customer_id_by_sub(conn, sub)
            if not customer_id:
                return err("Customer not found for token", 403)

            job = get_job_for_payment(conn, job_id)
            if not job:
                return err("Job not found", 404)

            if int(job["customer_id"]) != int(customer_id):
                return err("Forbidden: job does not belong to this customer", 403)

            if (job.get("status") or "").lower() != "completed":
                return err("Job must be completed before payment", 409, {"status": job.get("status")})

            if job.get("final_price") is None:
                return err("Job final_price is missing", 409)

            existing = get_payment_by_job(conn, job_id)
            if existing and (existing.get("status") == "paid"):
                # already paid: return existing totals
                return ok({
                    "already_paid": True,
                    "payment_id": existing["payment_id"],
                    "amounts": {
                        "base_amount_cents": existing["base_amount_cents"],
                        "tax_cents": existing["tax_cents"],
                        "app_fee_cents": existing["app_fee_cents"],
                        "final_amount_cents": existing["final_amount_cents"],
                        "currency": existing.get("currency","cad"),
                    }
                })

            base_cents = to_cents(job["final_price"])
            tax_rate, state_code = get_rate(job.get("location_state"))
            tax_cents, app_fee_cents, final_cents = compute_amounts(base_cents, tax_rate, APP_FEE_RATE)

            return ok({
                "job_id": int(job_id),
                "location_state": job.get("location_state"),
                "normalized_state": state_code,
                "tax_rate": tax_rate,
                "app_fee_rate": APP_FEE_RATE,
                "amounts": {
                    "base_amount_cents": base_cents,
                    "tax_cents": tax_cents,
                    "app_fee_cents": app_fee_cents,
                    "final_amount_cents": final_cents,
                    "currency": "cad",
                }
            })
        finally:
            try: conn.close()
            except: pass
    except Exception as e:
        return err("Server error", 500, str(e))
