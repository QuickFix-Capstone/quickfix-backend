from src.response import ok, err
from src.event import get_jwt_sub
from src.db import get_conn
from src.sql_helpers import get_customer_id_by_sub, get_provider_id_by_sub

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

def _customer_payload(conn, customer_id, limit, offset):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT "
            "COUNT(*) AS total_payments, "
            "SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) AS total_paid_count, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN final_amount_cents ELSE 0 END),0) AS total_paid_cents, "
            "SUM(CASE WHEN status='paid' AND job_id IS NOT NULL THEN 1 ELSE 0 END) AS jobs_completed_and_paid "
            "FROM payment WHERE customer_id=%s",
            (customer_id,),
        )
        summary = cur.fetchone()

        cur.execute(
            "SELECT "
            "p.payment_id, p.job_id, p.status, p.payment_method, "
            "p.base_amount_cents, p.tax_cents, p.app_fee_cents, p.final_amount_cents, "
            "p.currency, p.provider_payment_id, p.paid_at, p.created_at, "
            "j.title, j.category, j.location_city, j.location_state, j.completed_at, "
            "sp.business_name AS provider_business_name, sp.name AS provider_name "
            "FROM payment p "
            "JOIN jobs j ON j.job_id = p.job_id "
            "LEFT JOIN service_providers sp ON sp.provider_id = p.provider_id "
            "WHERE p.customer_id=%s "
            "ORDER BY COALESCE(p.paid_at, p.created_at) DESC "
            "LIMIT %s OFFSET %s",
            (customer_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"role": "customer", "summary": summary, "items": rows, "limit": limit, "offset": offset}

def _provider_payload(conn, provider_id, limit, offset):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT "
            "COUNT(*) AS total_payments, "
            "SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) AS total_paid_count, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN base_amount_cents ELSE 0 END),0) AS total_earned_base_cents, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN tax_cents ELSE 0 END),0) AS total_tax_cents, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN app_fee_cents ELSE 0 END),0) AS total_app_fee_cents, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN (base_amount_cents + tax_cents) ELSE 0 END),0) AS provider_gross_cents, "
            "SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) AS jobs_completed_and_paid "
            "FROM payment WHERE provider_id=%s",
            (provider_id,),
        )
        summary = cur.fetchone()

        cur.execute(
            "SELECT "
            "p.payment_id, p.job_id, p.status, p.payment_method, "
            "p.base_amount_cents, p.tax_cents, p.app_fee_cents, p.final_amount_cents, "
            "p.currency, p.provider_payment_id, p.paid_at, p.created_at, "
            "j.title, j.category, j.location_city, j.location_state, j.completed_at, "
            "CONCAT(c.first_name, ' ', c.last_name) AS customer_name, c.email AS customer_email "
            "FROM payment p "
            "JOIN jobs j ON j.job_id = p.job_id "
            "LEFT JOIN customers c ON c.customer_id = p.customer_id "
            "WHERE p.provider_id=%s "
            "ORDER BY COALESCE(p.paid_at, p.created_at) DESC "
            "LIMIT %s OFFSET %s",
            (provider_id, limit, offset),
        )
        rows = cur.fetchall()

    return {"role": "provider", "summary": summary, "items": rows, "limit": limit, "offset": offset}

def handler(event, context):
    # CORS preflight (API Gateway may send OPTIONS)
    if (event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "")).upper() == "OPTIONS":
        return ok({"ok": True})

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    path = _norm_path(event)
    limit = _qs_int(event, "limit", 20)
    offset = _qs_int(event, "offset", 0)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    conn = get_conn()
    try:
        # explicit routes
        if path.endswith("/payments/history/customer"):
            customer_id = get_customer_id_by_sub(conn, sub)
            if not customer_id:
                return err("Customer not found for token", 403)
            return ok(_customer_payload(conn, customer_id, limit, offset))

        if path.endswith("/payments/history/provider"):
            provider_id = get_provider_id_by_sub(conn, sub)
            if not provider_id:
                return err("Provider not found for token", 403)
            return ok(_provider_payload(conn, provider_id, limit, offset))

        # optional unified route: /payments/history
        if path.endswith("/payments/history"):
            customer_id = get_customer_id_by_sub(conn, sub)
            if customer_id:
                return ok(_customer_payload(conn, customer_id, limit, offset))
            provider_id = get_provider_id_by_sub(conn, sub)
            if provider_id:
                return ok(_provider_payload(conn, provider_id, limit, offset))
            return err("User not found as customer or provider", 403)

        return err("Not found", 404)

    except Exception as e:
        return err("Server error", 500, str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
