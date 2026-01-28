from .db import get_conn

def get_customer_id_by_sub(conn, sub):
    with conn.cursor() as cur:
        cur.execute("SELECT customer_id FROM customers WHERE cognito_sub=%s LIMIT 1", (sub,))
        row = cur.fetchone()
        return row["customer_id"] if row else None

def get_job_for_payment(conn, job_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT job_id, customer_id, assigned_provider_id, status, final_price, location_state, title, location_address, location_city, location_zip, completed_at "
            "FROM jobs WHERE job_id=%s LIMIT 1",
            (job_id,),
        )
        return cur.fetchone()

def get_payment_by_job(conn, job_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM payment WHERE job_id=%s LIMIT 1", (job_id,))
        return cur.fetchone()

def get_payment_by_id(conn, payment_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM payment WHERE payment_id=%s LIMIT 1", (payment_id,))
        return cur.fetchone()

def insert_payment(conn, job, customer_id, base_cents, tax_cents, app_fee_cents, final_cents, method):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO payment (job_id, customer_id, provider_id, base_amount_cents, tax_cents, app_fee_cents, final_amount_cents, currency, payment_method, status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,'cad',%s,'pending')",
            (job["job_id"], customer_id, job["assigned_provider_id"], base_cents, tax_cents, app_fee_cents, final_cents, method),
        )
        return cur.lastrowid

def update_payment_amounts(conn, payment_id, base_cents, tax_cents, app_fee_cents, final_cents, method):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE payment SET base_amount_cents=%s, tax_cents=%s, app_fee_cents=%s, final_amount_cents=%s, payment_method=%s, status='pending' "
            "WHERE payment_id=%s",
            (base_cents, tax_cents, app_fee_cents, final_cents, method, payment_id),
        )

def update_provider_payment_id(conn, payment_id, provider_payment_id, method):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE payment SET provider_payment_id=%s, payment_method=%s WHERE payment_id=%s",
            (provider_payment_id, method, payment_id),
        )

def mark_payment_status(conn, payment_id, status, provider_payment_id=None, set_paid_at=False):
    with conn.cursor() as cur:
        if set_paid_at:
            cur.execute(
                "UPDATE payment SET status=%s, paid_at=NOW(), provider_payment_id=COALESCE(%s, provider_payment_id) WHERE payment_id=%s",
                (status, provider_payment_id, payment_id),
            )
        else:
            cur.execute(
                "UPDATE payment SET status=%s, provider_payment_id=COALESCE(%s, provider_payment_id) WHERE payment_id=%s",
                (status, provider_payment_id, payment_id),
            )
