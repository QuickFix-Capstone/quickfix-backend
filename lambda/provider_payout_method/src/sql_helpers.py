def get_customer_id_by_sub(conn, sub):
    with conn.cursor() as cur:
        cur.execute("SELECT customer_id FROM customers WHERE cognito_sub=%s LIMIT 1", (sub,))
        row = cur.fetchone()
        return row["customer_id"] if row else None

def get_provider_id_by_sub(conn, sub):
    with conn.cursor() as cur:
        cur.execute("SELECT provider_id FROM service_providers WHERE cognito_sub=%s LIMIT 1", (sub,))
        row = cur.fetchone()
        return row["provider_id"] if row else None

def get_admin_id_by_sub(conn, sub):
    with conn.cursor() as cur:
        cur.execute("SELECT admin_id FROM admins WHERE cognito_sub=%s AND is_active=1 LIMIT 1", (sub,))
        row = cur.fetchone()
        return row["admin_id"] if row else None

def get_provider_email(conn, provider_id):
    with conn.cursor() as cur:
        cur.execute("SELECT email, name, business_name FROM service_providers WHERE provider_id=%s LIMIT 1", (provider_id,))
        return cur.fetchone()

def get_payment_by_id(conn, payment_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM payment WHERE payment_id=%s LIMIT 1", (payment_id,))
        return cur.fetchone()

def get_provider_payout_method(conn, provider_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM provider_payout_methods WHERE provider_id=%s LIMIT 1", (provider_id,))
        return cur.fetchone()

def upsert_provider_payout_method(conn, provider_id, method, stripe_account_id=None, paypal_email=None, status="pending"):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO provider_payout_methods (provider_id, method, stripe_account_id, paypal_email, status, updated_at) "
            "VALUES (%s,%s,%s,%s,%s,NOW()) "
            "ON DUPLICATE KEY UPDATE method=VALUES(method), stripe_account_id=VALUES(stripe_account_id), paypal_email=VALUES(paypal_email), status=VALUES(status), updated_at=NOW()",
            (provider_id, method, stripe_account_id, paypal_email, status),
        )

def ensure_provider_earning_for_payment(conn, payment_id):
    # Create one earning row per payment_id when payment is paid
    with conn.cursor() as cur:
        cur.execute("SELECT payment_id, provider_id, base_amount_cents, tax_cents, app_fee_cents, currency, status FROM payment WHERE payment_id=%s LIMIT 1", (payment_id,))
        p = cur.fetchone()
        if not p:
            return {"payment_id": payment_id, "status": "missing_payment"}
        if (p.get("status") or "").lower() != "paid":
            return {"payment_id": payment_id, "status": "skipped_not_paid", "payment_status": p.get("status")}
        provider_gross_cents = int(p.get("base_amount_cents") or 0) + int(p.get("tax_cents") or 0)
        platform_fee_cents = int(p.get("app_fee_cents") or 0)
        net_owed_cents = provider_gross_cents  # keep consistent with your provider history summary

        cur.execute("SELECT earning_id FROM provider_earnings WHERE payment_id=%s LIMIT 1", (payment_id,))
        if cur.fetchone():
            return {"payment_id": payment_id, "status": "exists"}

        cur.execute(
            "INSERT INTO provider_earnings (payment_id, provider_id, provider_gross_cents, platform_fee_cents, net_owed_cents, currency, status, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,'owed',NOW())",
            (payment_id, p["provider_id"], provider_gross_cents, platform_fee_cents, net_owed_cents, p.get("currency") or "cad"),
        )
        return {"payment_id": payment_id, "status": "created", "provider_id": p["provider_id"], "net_owed_cents": net_owed_cents}

def compute_provider_balance(conn, provider_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT "
            "COALESCE(SUM(CASE WHEN status='owed' THEN net_owed_cents ELSE 0 END),0) AS owed_cents, "
            "COALESCE(SUM(CASE WHEN status='in_payout' THEN net_owed_cents ELSE 0 END),0) AS in_payout_cents, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN net_owed_cents ELSE 0 END),0) AS paid_total_cents "
            "FROM provider_earnings WHERE provider_id=%s",
            (provider_id,),
        )
        return cur.fetchone()

def create_payout(conn, provider_id, method, amount_cents, currency="cad"):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO provider_payouts (provider_id, method, amount_cents, currency, status, created_at) "
            "VALUES (%s,%s,%s,%s,'queued',NOW())",
            (provider_id, method, int(amount_cents), currency),
        )
        return cur.lastrowid

def select_owed_earnings(conn, provider_id, max_amount_cents=None):
    # Select oldest owed earnings first.
    with conn.cursor() as cur:
        cur.execute(
            "SELECT earning_id, net_owed_cents FROM provider_earnings WHERE provider_id=%s AND status='owed' ORDER BY earning_id ASC",
            (provider_id,),
        )
        rows = cur.fetchall() or []
    if max_amount_cents is None:
        return rows
    picked=[]
    total=0
    for r in rows:
        c=int(r["net_owed_cents"] or 0)
        if total + c > int(max_amount_cents):
            break
        picked.append(r)
        total += c
    return picked

def mark_earnings_in_payout(conn, earning_ids, payout_id):
    if not earning_ids:
        return 0
    with conn.cursor() as cur:
        fmt = ",".join(["%s"]*len(earning_ids))
        cur.execute(
            f"UPDATE provider_earnings SET status='in_payout', payout_id=%s WHERE earning_id IN ({fmt}) AND status='owed'",
            (payout_id, *earning_ids),
        )
        return cur.rowcount

def mark_payout_processing(conn, payout_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE provider_payouts SET status='processing' WHERE payout_id=%s AND status='queued'", (payout_id,))
        return cur.rowcount

def mark_payout_paid(conn, payout_id, external_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE provider_payouts SET status='paid', external_id=%s, paid_at=NOW() WHERE payout_id=%s", (external_id, payout_id))

def mark_payout_failed(conn, payout_id, reason):
    with conn.cursor() as cur:
        cur.execute("UPDATE provider_payouts SET status='failed', failure_reason=%s WHERE payout_id=%s", (str(reason)[:1000], payout_id))

def mark_earnings_paid(conn, payout_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE provider_earnings SET status='paid' WHERE payout_id=%s AND status='in_payout'", (payout_id,))

def rollback_earnings_to_owed(conn, payout_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE provider_earnings SET status='owed', payout_id=NULL WHERE payout_id=%s AND status='in_payout'", (payout_id,))

def get_payout_by_id(conn, payout_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM provider_payouts WHERE payout_id=%s LIMIT 1", (payout_id,))
        return cur.fetchone()

def list_provider_payouts(conn, provider_id, limit, offset):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM provider_payouts WHERE provider_id=%s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (provider_id, limit, offset),
        )
        return cur.fetchall()

def list_admin_payouts(conn, limit, offset, status=None):
    with conn.cursor() as cur:
        if status:
            cur.execute(
                "SELECT p.*, sp.name AS provider_name, sp.business_name FROM provider_payouts p JOIN service_providers sp ON sp.provider_id=p.provider_id "
                "WHERE p.status=%s ORDER BY p.created_at DESC LIMIT %s OFFSET %s",
                (status, limit, offset),
            )
        else:
            cur.execute(
                "SELECT p.*, sp.name AS provider_name, sp.business_name FROM provider_payouts p JOIN service_providers sp ON sp.provider_id=p.provider_id "
                "ORDER BY p.created_at DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )
        return cur.fetchall()

def ensure_provider_earnings_for_provider(conn, provider_id):
    # Backfill earnings for all paid payments for this provider (idempotent)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO provider_earnings (payment_id, provider_id, provider_gross_cents, platform_fee_cents, net_owed_cents, currency, status, created_at) "
            "SELECT p.payment_id, p.provider_id, (p.base_amount_cents + p.tax_cents) AS provider_gross_cents, p.app_fee_cents, "
            "(p.base_amount_cents + p.tax_cents) AS net_owed_cents, COALESCE(p.currency,'cad') AS currency, 'owed', NOW() "
            "FROM payment p "
            "LEFT JOIN provider_earnings e ON e.payment_id = p.payment_id "
            "WHERE p.provider_id=%s AND LOWER(p.status)='paid' AND e.payment_id IS NULL",
            (provider_id,),
        )
        return cur.rowcount
