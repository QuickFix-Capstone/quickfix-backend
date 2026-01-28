import os
from src.response import ok, err
from src.event import get_json_body, get_jwt_sub
from src.db import get_conn
from src.tax import get_rate
from src.money import to_cents, compute_amounts
from src.http import post_form, post_json, basic_auth_header, bearer, HttpError
from src.sql_helpers import (
    get_customer_id_by_sub, get_job_for_payment, get_payment_by_job,
    insert_payment, update_payment_amounts, update_provider_payment_id
)

APP_FEE_RATE = float(os.getenv("APP_FEE_RATE", "0.07"))

def _paypal_base():
    env = (os.getenv("PAYPAL_ENV") or "sandbox").lower()
    return "https://api-m.paypal.com" if env == "live" else "https://api-m.sandbox.paypal.com"

def _paypal_token(client_id, secret):
    url = _paypal_base() + "/v1/oauth2/token"
    headers = {"Authorization": basic_auth_header(client_id, secret)}
    resp = post_form(url, {"grant_type": "client_credentials"}, headers=headers, timeout=25)
    return resp.get("access_token")

def handler(event, context):
    body = get_json_body(event)
    job_id = body.get("job_id")
    if not job_id:
        return err("job_id is required", 400)

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    if not client_id or not secret:
        return err("Missing PAYPAL_CLIENT_ID/PAYPAL_SECRET", 500)

    frontend = os.getenv("FRONTEND_URL", "").rstrip("/")
    return_url = (frontend + "/paypal/return") if frontend else "https://example.com/paypal/return"
    cancel_url = (frontend + "/paypal/cancel") if frontend else "https://example.com/paypal/cancel"

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
            payment_id = insert_payment(conn, job, customer_id, base_cents, tax_cents, app_fee_cents, final_cents, "paypal")
        else:
            payment_id = existing["payment_id"]
            update_payment_amounts(conn, payment_id, base_cents, tax_cents, app_fee_cents, final_cents, "paypal")

        token = _paypal_token(client_id, secret)
        if not token:
            conn.rollback()
            return err("PayPal token error", 502)

        value = f"{final_cents/100:.2f}"
        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "custom_id": str(payment_id),
                "reference_id": str(job_id),
                "amount": {"currency_code": "CAD", "value": value}
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        }
        headers = {"Authorization": bearer(token)}
        try:
            order = post_json(_paypal_base() + "/v2/checkout/orders", order_payload, headers=headers, timeout=25)
        except HttpError as he:
            conn.rollback()
            return err("PayPal error", 502, he.body)

        order_id = order.get("id")
        links = order.get("links") or []
        approval = None
        for l in links:
            if l.get("rel") == "approve":
                approval = l.get("href")
                break

        if not order_id or not approval:
            conn.rollback()
            return err("PayPal response missing order_id/approval link", 502, order)

        update_provider_payment_id(conn, payment_id, order_id, "paypal")
        conn.commit()

        return ok({
            "payment_id": int(payment_id),
            "order_id": order_id,
            "approval_url": approval,
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
