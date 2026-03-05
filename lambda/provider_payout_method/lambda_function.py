# Generated for QuickFix provider payouts (Stripe Connect + PayPal Payouts)
import re
from src.response import ok, err
from src.event import get_json_body, get_jwt_sub
from src.db import get_conn
from src.sql_helpers import get_provider_id_by_sub, upsert_provider_payout_method, get_provider_payout_method

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _norm_path(event):
    return (event.get("rawPath") or event.get("path") or "").lower()

def handler(event, context):
    if (event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "")).upper() == "OPTIONS":
        return ok({"ok": True})

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    path = _norm_path(event)
    conn = get_conn()
    try:
        provider_id = get_provider_id_by_sub(conn, sub)
        if not provider_id:
            return err("Provider not found for token", 403)

        if path.endswith("/providers/payout-method") and ((event.get("requestContext", {}).get("http", {}).get("method") or "").upper() in ("GET","")):
            row = get_provider_payout_method(conn, provider_id)
            return ok({"provider_id": provider_id, "payout_method": row})

        body = get_json_body(event)
        method = (body.get("method") or "").lower().strip()

        if method not in ("paypal", "stripe_connect"):
            return err("method must be paypal or stripe_connect", 400)

        stripe_account_id = body.get("stripe_account_id")
        paypal_email = body.get("paypal_email")

        if method == "paypal":
            if not paypal_email or not EMAIL_RE.match(paypal_email):
                return err("paypal_email is required and must be valid", 400)
            upsert_provider_payout_method(conn, provider_id, "paypal", stripe_account_id=None, paypal_email=paypal_email, status="verified")

        if method == "stripe_connect":
            if stripe_account_id and not str(stripe_account_id).startswith("acct_"):
                return err("stripe_account_id must look like acct_...", 400)
            # status becomes verified after onboarding check
            upsert_provider_payout_method(conn, provider_id, "stripe_connect", stripe_account_id=stripe_account_id, paypal_email=None, status="pending")

        conn.commit()
        row = get_provider_payout_method(conn, provider_id)
        return ok({"provider_id": provider_id, "payout_method": row})

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
