# Generated for QuickFix provider payouts (Stripe Connect + PayPal Payouts)
import json
import os
import boto3

from src.response import ok, err
from src.event import get_json_body, get_jwt_sub, get_jwt_groups
from src.db import get_conn
from src.sql_helpers import (
    get_admin_id_by_sub,
    get_provider_payout_method,
    compute_provider_balance,
    select_owed_earnings,
    create_payout,
    mark_earnings_in_payout,
    ensure_provider_earnings_for_provider,
    list_admin_payouts,
)

def _qs_int(event, key, default):
    qs = event.get("queryStringParameters") or {}
    val = qs.get(key)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default

def _qs_str(event, key, default=None):
    qs = event.get("queryStringParameters") or {}
    val = qs.get(key)
    if val is None or val == "":
        return default
    return str(val)

def _norm_path(event):
    """
    Normalizes API Gateway v2 rawPath:
      rawPath example: /prod/admin/payouts/history
    returns:
      /admin/payouts/history
    """
    raw = (event.get("rawPath") or event.get("path") or "").lower().rstrip("/")
    stage = (event.get("requestContext") or {}).get("stage")
    if stage and raw.startswith(f"/{stage}/"):
        raw = raw[len(stage) + 1:]  # removes '/prod'
    return raw

def _http_method(event):
    return (event.get("requestContext", {}).get("http", {}).get("method")
            or event.get("httpMethod") or "GET").upper()

def _enqueue_payout(payout_id: int):
    qurl = os.getenv("PAYOUT_JOBS_QUEUE_URL")
    if not qurl:
        raise RuntimeError("Missing env var PAYOUT_JOBS_QUEUE_URL")
    sqs = boto3.client("sqs")
    sqs.send_message(
        QueueUrl=qurl,
        MessageBody=json.dumps({"payout_id": int(payout_id), "source": "admin_payout_create"})
    )

def handler(event, context):
    method = _http_method(event)

    # Preflight must always succeed
    if method == "OPTIONS":
        return ok({"ok": True})

    # Auth
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    path = _norm_path(event)

    conn = get_conn()
    try:
        # Admin check: allow either DB admin record OR Cognito Administrator group
        admin_id = get_admin_id_by_sub(conn, sub)
        groups = get_jwt_groups(event)
        if not admin_id and "Administrator" not in groups:
            return err("Unauthorized", 401)

        # -----------------------------
        # GET /admin/payouts/eligible
        # -----------------------------
        # Returns providers who:
        # - have VERIFIED payout method
        # - have owed_cents > 0
        if path.endswith("/admin/payouts/eligible") and method == "GET":
            # Optional filters/pagination
            limit = max(1, min(_qs_int(event, "limit", 50), 200))
            offset = max(0, _qs_int(event, "offset", 0))

            # Strategy:
            # 1) Find providers with verified payout methods
            # 2) Backfill earnings (idempotent) + compute balance
            #
            # We don't have a "list_eligible_providers" helper in sql_helpers,
            # so we use compute_provider_balance per provider only after
            # selecting verified methods from DB.

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT provider_id, method, stripe_account_id, paypal_email, status
                    FROM provider_payout_methods
                    WHERE status = 'verified'
                    ORDER BY provider_id
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                methods = cur.fetchall() or []

            items = []
            total_outstanding = 0

            for pm in methods:
                provider_id = pm["provider_id"]

                # Backfill earnings from paid payments (safe + idempotent)
                ensure_provider_earnings_for_provider(conn, provider_id)

                bal = compute_provider_balance(conn, provider_id)
                owed_cents = int((bal or {}).get("owed_cents") or 0)
                if owed_cents <= 0:
                    continue

                total_outstanding += owed_cents

                items.append({
                    "provider_id": provider_id,
                    "method": pm.get("method"),
                    "owed_cents": owed_cents,
                    "payout_method": {
                        "stripe_account_id": pm.get("stripe_account_id"),
                        "paypal_email": pm.get("paypal_email"),
                        "status": pm.get("status"),
                    }
                })

            return ok({
                "items": items,
                "limit": limit,
                "offset": offset,
                "total_outstanding_cents": total_outstanding
            })

        # -----------------------------
        # GET /admin/payouts/history
        # -----------------------------
        if path.endswith("/admin/payouts/history") and method == "GET":
            limit = max(1, min(_qs_int(event, "limit", 25), 100))
            offset = max(0, _qs_int(event, "offset", 0))
            status = _qs_str(event, "status")  # optional
            rows = list_admin_payouts(conn, limit, offset, status=status)
            return ok({"items": rows, "limit": limit, "offset": offset})

        # -----------------------------
        # POST /admin/payouts/pay
        # -----------------------------
        # Body: { provider_id, amount_cents? }
        if path.endswith("/admin/payouts/pay") and method == "POST":
            body = get_json_body(event)
            provider_id = body.get("provider_id")
            if not provider_id:
                return err("provider_id is required", 400)

            max_amount_cents = body.get("amount_cents")  # optional cap
            if max_amount_cents is not None:
                try:
                    max_amount_cents = int(max_amount_cents)
                    if max_amount_cents <= 0:
                        return err("amount_cents must be > 0", 400)
                except Exception:
                    return err("amount_cents must be integer cents", 400)

            pm = get_provider_payout_method(conn, provider_id)
            if not pm:
                return err("Provider has no payout method on file", 400)
            if (pm.get("status") or "").lower() != "verified":
                return err("Provider payout method is not verified yet", 400)

            payout_method = pm.get("method")

            # Backfill earnings from paid payments (idempotent)
            ensure_provider_earnings_for_provider(conn, provider_id)

            owed = compute_provider_balance(conn, provider_id)
            owed_cents = int((owed or {}).get("owed_cents") or 0)
            if owed_cents <= 0:
                return err("Provider has no owed balance to pay", 400)

            earnings = select_owed_earnings(conn, provider_id, max_amount_cents=max_amount_cents)
            if not earnings:
                return err("No owed earnings found", 400)

            amount_cents = sum(int(r.get("net_owed_cents") or 0) for r in earnings)

            payout_id = create_payout(conn, provider_id, payout_method, amount_cents, currency="cad")
            affected = mark_earnings_in_payout(conn, [r["earning_id"] for r in earnings], payout_id)
            if affected <= 0:
                raise RuntimeError("Failed to mark earnings in_payout (possible race condition)")

            conn.commit()

            # enqueue AFTER commit
            _enqueue_payout(payout_id)

            return ok({
                "payout_id": payout_id,
                "provider_id": provider_id,
                "method": payout_method,
                "amount_cents": amount_cents,
                "earning_count": len(earnings)
            })

        # -----------------------------
        # Existing routes (keep)
        # GET /admin/payouts
        # POST /admin/payouts
        # -----------------------------
        if path.endswith("/admin/payouts") and method == "GET":
            limit = max(1, min(_qs_int(event, "limit", 25), 100))
            offset = max(0, _qs_int(event, "offset", 0))
            status = _qs_str(event, "status")
            rows = list_admin_payouts(conn, limit, offset, status=status)
            return ok({"items": rows, "limit": limit, "offset": offset})

        if path.endswith("/admin/payouts") and method == "POST":
            body = get_json_body(event)
            provider_id = body.get("provider_id")
            if not provider_id:
                return err("provider_id is required", 400)

            max_amount_cents = body.get("amount_cents")  # optional cap
            if max_amount_cents is not None:
                try:
                    max_amount_cents = int(max_amount_cents)
                    if max_amount_cents <= 0:
                        return err("amount_cents must be > 0", 400)
                except Exception:
                    return err("amount_cents must be integer cents", 400)

            pm = get_provider_payout_method(conn, provider_id)
            if not pm:
                return err("Provider has no payout method on file", 400)
            if (pm.get("status") or "").lower() != "verified":
                return err("Provider payout method is not verified yet", 400)

            payout_method = pm.get("method")

            ensure_provider_earnings_for_provider(conn, provider_id)
            owed = compute_provider_balance(conn, provider_id)
            owed_cents = int((owed or {}).get("owed_cents") or 0)
            if owed_cents <= 0:
                return err("Provider has no owed balance to pay", 400)

            earnings = select_owed_earnings(conn, provider_id, max_amount_cents=max_amount_cents)
            if not earnings:
                return err("No owed earnings found", 400)

            amount_cents = sum(int(r.get("net_owed_cents") or 0) for r in earnings)

            payout_id = create_payout(conn, provider_id, payout_method, amount_cents, currency="cad")
            affected = mark_earnings_in_payout(conn, [r["earning_id"] for r in earnings], payout_id)
            if affected <= 0:
                raise RuntimeError("Failed to mark earnings in_payout (possible race condition)")

            conn.commit()
            _enqueue_payout(payout_id)

            return ok({
                "payout_id": payout_id,
                "provider_id": provider_id,
                "method": payout_method,
                "amount_cents": amount_cents,
                "earning_count": len(earnings)
            })

        return err("Not found", 404)

    except Exception as e:
        print("ERROR:", str(e))
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