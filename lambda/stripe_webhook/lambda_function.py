import os, json, hmac, hashlib, time
from src.response import ok, err
from src.event import get_header
from src.db import get_conn
from src.sql_helpers import mark_payment_status

def _verify_stripe_signature(payload, sig_header, secret, tolerance=300):
    if not sig_header or not secret:
        return False, "missing signature/secret"

    parts = {}
    for item in sig_header.split(","):
        if "=" in item:
            k,v = item.split("=",1)
            parts.setdefault(k.strip(), []).append(v.strip())

    ts_list = parts.get("t")
    v1_list = parts.get("v1")
    if not ts_list or not v1_list:
        return False, "invalid signature header"
    ts = int(ts_list[0])
    if abs(int(time.time()) - ts) > tolerance:
        return False, "timestamp outside tolerance"

    signed_payload = f"{ts}.{payload}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if expected in v1_list:
        return True, None
    return False, "signature mismatch"

def handler(event, context):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        return err("Missing STRIPE_WEBHOOK_SECRET", 500)

    sig = get_header(event, "Stripe-Signature")
    payload = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64
        payload = base64.b64decode(payload).decode("utf-8")

    ok_sig, reason = _verify_stripe_signature(payload, sig, secret)
    if not ok_sig:
        return err("Invalid Stripe signature", 400, reason)

    try:
        evt = json.loads(payload)
    except Exception as e:
        return err("Invalid JSON", 400, str(e))

    evt_type = evt.get("type")
    obj = (evt.get("data") or {}).get("object") or {}
    pi_id = obj.get("id")
    metadata = obj.get("metadata") or {}
    payment_id = metadata.get("payment_id") or metadata.get("paymentId")
    if not payment_id:
        # nothing to update
        return ok({"received": True})

    status_to_set = None
    set_paid_at = False
    if evt_type == "payment_intent.succeeded":
        status_to_set = "paid"
        set_paid_at = True
    elif evt_type == "payment_intent.payment_failed":
        status_to_set = "failed"
    elif evt_type == "payment_intent.canceled":
        status_to_set = "canceled"
    else:
        return ok({"received": True, "ignored": evt_type})

    conn = get_conn()
    try:
        mark_payment_status(conn, int(payment_id), status_to_set, provider_payment_id=pi_id, set_paid_at=set_paid_at)
        conn.commit()
    except Exception as e:
        try: conn.rollback()
        except: pass
        return err("DB update failed", 500, str(e))
    finally:
        try: conn.close()
        except: pass

    return ok({"received": True, "status": status_to_set, "payment_id": int(payment_id)})
