# Generated for QuickFix provider payouts (Stripe Connect + PayPal Payouts)
import json
import os

from src.db import get_conn
from src.http import post_form, post_json, basic_auth_header, bearer, HttpError
from src.sql_helpers import (
    get_payout_by_id,
    get_provider_payout_method,
    mark_payout_processing,
    mark_payout_paid,
    mark_payout_failed,
    mark_earnings_paid,
    rollback_earnings_to_owed,
)

def _stripe_base():
    return "https://api.stripe.com"

def _stripe_headers(secret_key):
    return {"Authorization": basic_auth_header(secret_key, "")}

def _paypal_base():
    env = (os.getenv("PAYPAL_ENV") or "sandbox").lower()
    return "https://api-m.paypal.com" if env == "live" else "https://api-m.sandbox.paypal.com"

def _paypal_token(client_id, secret):
    url = _paypal_base() + "/v1/oauth2/token"
    headers = {"Authorization": basic_auth_header(client_id, secret)}
    resp = post_form(url, {"grant_type": "client_credentials"}, headers=headers, timeout=25)
    return resp.get("access_token")

def _paypal_payout(access_token, receiver_email, amount_cents, currency="CAD"):
    url = _paypal_base() + "/v1/payments/payouts"
    headers = {"Authorization": bearer(access_token)}
    value = f"{int(amount_cents)/100:.2f}"
    payload = {
        "sender_batch_header": {
            "sender_batch_id": f"QF-PAYOUT-{os.urandom(6).hex()}",
            "email_subject": "QuickFix payout",
        },
        "items": [
            {
                "recipient_type": "EMAIL",
                "amount": {"value": value, "currency": currency.upper()},
                "receiver": receiver_email,
                "note": "Thanks for working with QuickFix!",
                "sender_item_id": f"item-{os.urandom(4).hex()}",
            }
        ],
    }
    return post_json(url, payload, headers=headers, timeout=25)

def _stripe_transfer(secret_key, destination_acct, amount_cents, currency="cad", metadata=None):
    url = _stripe_base() + "/v1/transfers"
    form = {
        "amount": str(int(amount_cents)),
        "currency": currency.lower(),
        "destination": destination_acct,
    }
    if metadata:
        for k,v in metadata.items():
            form[f"metadata[{k}]"] = str(v)
    return post_form(url, form, headers=_stripe_headers(secret_key), timeout=25)

def handler(event, context):
    records = event.get("Records") or []
    results = []

    conn = get_conn()
    try:
        for r in records:
            body = r.get("body") or "{}"
            try:
                msg = json.loads(body)
            except Exception:
                msg = {}
            payout_id = msg.get("payout_id")
            if not payout_id:
                results.append({"status": "skipped", "reason": "missing_payout_id", "body": body[:200]})
                continue

            payout = get_payout_by_id(conn, int(payout_id))
            if not payout:
                results.append({"payout_id": payout_id, "status": "missing_payout"})
                continue

            if payout.get("status") == "paid":
                results.append({"payout_id": payout_id, "status": "already_paid"})
                continue

            # Try to move queued->processing (idempotent)
            mark_payout_processing(conn, int(payout_id))
            conn.commit()

            provider_id = payout["provider_id"]
            pm = get_provider_payout_method(conn, provider_id)
            if not pm or (pm.get("status") or "") != "verified":
                raise RuntimeError(f"Provider payout method not verified for {provider_id}")

            method = payout.get("method")
            amount_cents = int(payout.get("amount_cents") or 0)
            currency = (payout.get("currency") or "cad").upper()

            try:
                if method == "stripe_connect":
                    stripe_key = os.getenv("STRIPE_SECRET_KEY")
                    if not stripe_key:
                        raise RuntimeError("Missing STRIPE_SECRET_KEY")
                    dest = pm.get("stripe_account_id")
                    if not dest:
                        raise RuntimeError("Missing stripe_account_id for provider")
                    tr = _stripe_transfer(stripe_key, dest, amount_cents, currency="cad", metadata={"payout_id": payout_id, "provider_id": provider_id})
                    external = tr.get("id") or json.dumps(tr)[:200]
                    mark_payout_paid(conn, int(payout_id), external)
                    mark_earnings_paid(conn, int(payout_id))
                    conn.commit()
                    results.append({"payout_id": payout_id, "status": "paid", "external_id": external})

                elif method == "paypal":
                    client_id = os.getenv("PAYPAL_CLIENT_ID")
                    secret = os.getenv("PAYPAL_SECRET")
                    if not client_id or not secret:
                        raise RuntimeError("Missing PAYPAL_CLIENT_ID / PAYPAL_SECRET")
                    receiver = pm.get("paypal_email")
                    if not receiver:
                        raise RuntimeError("Missing paypal_email for provider")
                    token = _paypal_token(client_id, secret)
                    resp = _paypal_payout(token, receiver, amount_cents, currency=currency)
                    # Try to capture ids
                    batch_id = (resp.get("batch_header") or {}).get("payout_batch_id") or resp.get("payout_batch_id")
                    external = batch_id or json.dumps(resp)[:200]
                    mark_payout_paid(conn, int(payout_id), external)
                    mark_earnings_paid(conn, int(payout_id))
                    conn.commit()
                    results.append({"payout_id": payout_id, "status": "paid", "external_id": external})

                else:
                    raise RuntimeError(f"Unsupported payout method: {method}")

            except Exception as e:
                # mark failed and return earnings to owed so admin can retry
                mark_payout_failed(conn, int(payout_id), str(e))
                rollback_earnings_to_owed(conn, int(payout_id))
                conn.commit()
                results.append({"payout_id": payout_id, "status": "failed", "error": str(e)})

    finally:
        try:
            conn.close()
        except Exception:
            pass

    return {"ok": True, "results": results}
