import os
import urllib.parse
from src.response import ok, err
from src.event import get_json_body, get_jwt_sub
from src.db import get_conn
from src.tax import get_rate
from src.money import to_cents, compute_amounts
from src.http import post_form, HttpError
from src.sql_helpers import (
    get_customer_id_by_sub, get_job_for_payment, get_payment_by_job,
    insert_payment, update_payment_amounts, update_provider_payment_id
)

APP_FEE_RATE = float(os.getenv("APP_FEE_RATE", "0.07"))

def handler(event, context):
    body = get_json_body(event)
    job_id = body.get("job_id")
    if not job_id:
        return err("job_id is required", 400)

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        return err("Missing STRIPE_SECRET_KEY", 500)

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

        base_cents = to_cents(job["final_price"])
        tax_rate, state_code = get_rate(job.get("location_state"))
        tax_cents, app_fee_cents, final_cents = compute_amounts(base_cents, tax_rate, APP_FEE_RATE)

        existing = get_payment_by_job(conn, job_id)
        if existing and existing.get("status") == "paid":
            return err("This job is already paid", 409, {"payment_id": existing["payment_id"]})

        if not existing:
            payment_id = insert_payment(conn, job, customer_id, base_cents, tax_cents, app_fee_cents, final_cents, "stripe")
        else:
            payment_id = existing["payment_id"]
            update_payment_amounts(conn, payment_id, base_cents, tax_cents, app_fee_cents, final_cents, "stripe")

        # create PaymentIntent via Stripe REST API
        form = {
            "amount": str(final_cents),
            "currency": "cad",
            "payment_method_types[]": "card",
            "metadata[payment_id]": str(payment_id),
            "metadata[job_id]": str(job_id),
            "metadata[customer_id]": str(customer_id),
            "description": f"QuickFix job #{job_id} payment_id={payment_id}",
        }
        headers = {"Authorization": f"Bearer {stripe_key}"}

        try:
            resp = post_form("https://api.stripe.com/v1/payment_intents", form, headers=headers, timeout=25)
        except HttpError as he:
            conn.rollback()
            return err("Stripe error", 502, he.body)

        provider_payment_id = resp.get("id")
        client_secret = resp.get("client_secret")
        if not provider_payment_id or not client_secret:
            conn.rollback()
            return err("Stripe response missing id/client_secret", 502, resp)

        update_provider_payment_id(conn, payment_id, provider_payment_id, "stripe")
        conn.commit()

        return ok({
            "payment_id": int(payment_id),
            "provider_payment_id": provider_payment_id,
            "clientSecret": client_secret,
            "amounts": {
                "base_amount_cents": base_cents,
                "tax_cents": tax_cents,
                "app_fee_cents": app_fee_cents,
                "final_amount_cents": final_cents,
                "currency": "cad",
            },
            "tax_rate": tax_rate,
            "normalized_state": state_code,
        })
    except Exception as e:
        try: conn.rollback()
        except: pass
        return err("Server error", 500, str(e))
    finally:
        try: conn.close()
        except: pass
