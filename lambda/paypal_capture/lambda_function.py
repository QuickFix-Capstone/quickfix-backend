import os
from src.response import ok, err
from src.event import get_json_body, get_jwt_sub
from src.db import get_conn
from src.http import post_form, post_json, basic_auth_header, bearer, HttpError
from src.sql_helpers import get_customer_id_by_sub, get_payment_by_id, mark_payment_status, update_provider_payment_id

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
    payment_id = body.get("payment_id")
    order_id = body.get("order_id") or body.get("token")  # token from return URL
    if not payment_id or not order_id:
        return err("payment_id and order_id are required", 400)

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    if not client_id or not secret:
        return err("Missing PAYPAL_CLIENT_ID/PAYPAL_SECRET", 500)

    conn = get_conn()
    try:
        customer_id = get_customer_id_by_sub(conn, sub)
        if not customer_id:
            return err("Customer not found for token", 403)

        payment = get_payment_by_id(conn, int(payment_id))
        if not payment:
            return err("Payment not found", 404)

        if int(payment["customer_id"]) != int(customer_id):
            return err("Forbidden: payment does not belong to this customer", 403)

        if payment.get("status") == "paid":
            return ok({"already_paid": True, "payment_id": int(payment_id)})

        token = _paypal_token(client_id, secret)
        if not token:
            return err("PayPal token error", 502)

        headers = {"Authorization": bearer(token)}
        try:
            capture = post_json(_paypal_base() + f"/v2/checkout/orders/{order_id}/capture", {}, headers=headers, timeout=25)
        except HttpError as he:
            try: conn.rollback()
            except: pass
            return err("PayPal capture error", 502, he.body)

        status = (capture.get("status") or "").upper()
        if status == "COMPLETED":
            # mark paid
            update_provider_payment_id(conn, int(payment_id), order_id, "paypal")
            mark_payment_status(conn, int(payment_id), "paid", provider_payment_id=order_id, set_paid_at=True)
            conn.commit()
            return ok({"payment_id": int(payment_id), "status": "paid", "paypal_status": status})
        else:
            # keep pending or failed depending
            new_status = "failed" if status in ("DECLINED", "FAILED", "VOIDED") else "pending"
            update_provider_payment_id(conn, int(payment_id), order_id, "paypal")
            mark_payment_status(conn, int(payment_id), new_status, provider_payment_id=order_id, set_paid_at=False)
            conn.commit()
            return ok({"payment_id": int(payment_id), "status": new_status, "paypal_status": status, "raw": capture})
    except Exception as e:
        try: conn.rollback()
        except: pass
        return err("Server error", 500, str(e))
    finally:
        try: conn.close()
        except: pass
