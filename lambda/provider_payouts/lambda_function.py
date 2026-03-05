# Generated for QuickFix provider payouts (Stripe Connect + PayPal Payouts)
from src.response import ok, err
from src.event import get_jwt_sub
from src.db import get_conn
from src.sql_helpers import get_provider_id_by_sub, compute_provider_balance, list_provider_payouts, get_provider_payout_method, ensure_provider_earnings_for_provider

def _qs_int(event, key, default):
    qs = event.get("queryStringParameters") or {}
    val = qs.get(key)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default

def _norm_path(event):
    return (event.get("rawPath") or event.get("path") or "").lower()

def handler(event, context):
    if (event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "")).upper() == "OPTIONS":
        return ok({"ok": True})

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    path = _norm_path(event)
    limit = max(1, min(_qs_int(event, "limit", 20), 100))
    offset = max(0, _qs_int(event, "offset", 0))

    conn = get_conn()
    try:
        provider_id = get_provider_id_by_sub(conn, sub)
        if not provider_id:
            return err("Provider not found for token", 403)

        if path.endswith("/providers/payouts/balance"):
            ensure_provider_earnings_for_provider(conn, provider_id)
            conn.commit()
            balance = compute_provider_balance(conn, provider_id)
            pm = get_provider_payout_method(conn, provider_id)
            return ok({"provider_id": provider_id, "balance": balance, "payout_method": pm})

        if path.endswith("/providers/payouts/history"):
            rows = list_provider_payouts(conn, provider_id, limit, offset)
            return ok({"provider_id": provider_id, "items": rows, "limit": limit, "offset": offset})

        return err("Not found", 404)

    except Exception as e:
        return err("Server error", 500, str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
