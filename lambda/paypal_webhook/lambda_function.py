import json
import os
from src import response
from src import db
from src import http

PAYPAL_EVENT_TO_STATUS = {
    # success
    "PAYMENT.CAPTURE.COMPLETED": "paid",
    # failure / denied
    "PAYMENT.CAPTURE.DENIED": "declined",
    "PAYMENT.CAPTURE.REFUNDED": "refunded",
    "PAYMENT.CAPTURE.REVERSED": "declined",
    "CHECKOUT.ORDER.CANCELLED": "declined",
    "CHECKOUT.ORDER.VOIDED": "declined",
    # order approved means user approved, capture may still be pending
    "CHECKOUT.ORDER.APPROVED": "pending",
}

def _h(headers, name):
    if not headers:
        return None
    # API Gateway HTTP API lowercases headers; be safe.
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return None

def _parse_body(event):
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body) if body else {}
    except Exception:
        # PayPal sends JSON; if invalid, return raw text for debugging
        return {"_raw": body}

def _paypal_access_token():
    base = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com").rstrip("/")
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_SECRET")
    if not client_id or not secret:
        raise RuntimeError("Missing PAYPAL_CLIENT_ID or PAYPAL_SECRET env vars")

    url = f"{base}/v1/oauth2/token"
    headers = {"Authorization": http.basic_auth_header(client_id, secret)}
    resp = http.post_form(url, {"grant_type": "client_credentials"}, headers=headers)
    return resp.get("access_token")

def _verify_signature(event_headers, webhook_event):
    """
    Verify PayPal webhook signature using PayPal verify-webhook-signature API.
    Docs: https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature
    """
    webhook_id = os.getenv("PAYPAL_WEBHOOK_ID")
    if not webhook_id:
        raise RuntimeError("Missing PAYPAL_WEBHOOK_ID env var (from PayPal webhook config)")

    transmission_id = _h(event_headers, "paypal-transmission-id")
    transmission_time = _h(event_headers, "paypal-transmission-time")
    cert_url = _h(event_headers, "paypal-cert-url")
    auth_algo = _h(event_headers, "paypal-auth-algo")
    transmission_sig = _h(event_headers, "paypal-transmission-sig")

    missing = [k for k,v in {
        "paypal-transmission-id": transmission_id,
        "paypal-transmission-time": transmission_time,
        "paypal-cert-url": cert_url,
        "paypal-auth-algo": auth_algo,
        "paypal-transmission-sig": transmission_sig,
    }.items() if not v]
    if missing:
        # For local/manual testing you might not have headers; fail closed for security.
        raise RuntimeError(f"Missing PayPal webhook headers: {', '.join(missing)}")

    token = _paypal_access_token()
    base = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com").rstrip("/")
    url = f"{base}/v1/notifications/verify-webhook-signature"
    payload = {
        "auth_algo": auth_algo,
        "cert_url": cert_url,
        "transmission_id": transmission_id,
        "transmission_sig": transmission_sig,
        "transmission_time": transmission_time,
        "webhook_id": webhook_id,
        "webhook_event": webhook_event,
    }
    headers = {"Authorization": http.bearer(token)}
    resp = http.post_json(url, payload, headers=headers)
    return (resp.get("verification_status") == "SUCCESS")

def _find_order_id(pp_event):
    """
    Try to extract PayPal order_id (we store this in payment.provider_payment_id).
    """
    resource = pp_event.get("resource") or {}
    etype = pp_event.get("event_type")

    # For ORDER events, resource.id is order id
    if etype and etype.startswith("CHECKOUT.ORDER"):
        return resource.get("id")

    # For CAPTURE events, order id often available in supplementary_data.related_ids.order_id
    supp = resource.get("supplementary_data") or {}
    rel = supp.get("related_ids") or {}
    return rel.get("order_id") or resource.get("id")

def _update_payment_status(order_id, new_status, pp_event):
    if not order_id:
        return False, "Missing order_id"

    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            # update by provider_payment_id (PayPal order id)
            cur.execute(
                """
                UPDATE payment
                SET status=%s,
                    paid_at = CASE WHEN %s='paid' THEN COALESCE(paid_at, NOW()) ELSE paid_at END
                WHERE provider_payment_id=%s AND payment_method='paypal'
                """,
                (new_status, new_status, order_id),
            )
        conn.commit()
        return True, None
    finally:
        conn.close()

def handler(event, context):
    # PayPal may send OPTIONS preflight if called from browsers (unlikely), handle anyway.
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return response.ok({"ok": True})

    headers = event.get("headers") or {}
    pp_event = _parse_body(event)

    # Verify signature (fail closed)
    try:
        ok_sig = _verify_signature(headers, pp_event)
    except Exception as e:
        return response.err("Webhook signature verification failed", 400, {"message": str(e)})

    if not ok_sig:
        return response.err("Invalid PayPal webhook signature", 400)

    event_type = pp_event.get("event_type")
    new_status = PAYPAL_EVENT_TO_STATUS.get(event_type)

    # Ignore events we don't care about, but return 200 so PayPal doesn't retry forever
    if not new_status:
        return response.ok({"received": True, "ignored": True, "event_type": event_type})

    order_id = _find_order_id(pp_event)
    updated, why = _update_payment_status(order_id, new_status, pp_event)

    if not updated:
        # still return 200 to avoid repeated retries; include info for logs
        return response.ok({"received": True, "updated": False, "event_type": event_type, "order_id": order_id, "reason": why})

    return response.ok({"received": True, "updated": True, "event_type": event_type, "order_id": order_id, "status": new_status})
