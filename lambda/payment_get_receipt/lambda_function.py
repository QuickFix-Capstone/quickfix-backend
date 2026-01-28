from src.response import ok, err
from src.event import get_jwt_sub
from src.db import get_conn
from src.sql_helpers import get_customer_id_by_sub

def handler(event, context):
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    path_params = event.get("pathParameters") or {}
    payment_id = path_params.get("payment_id") or path_params.get("id")
    if not payment_id:
        return err("payment_id path param required", 400)

    conn = get_conn()
    try:
        customer_id = get_customer_id_by_sub(conn, sub)
        if not customer_id:
            return err("Customer not found for token", 403)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT p.*, j.title, j.description, j.category, j.location_address, j.location_city, j.location_state, j.location_zip, j.completed_at "
                "FROM payment p JOIN jobs j ON j.job_id = p.job_id "
                "WHERE p.payment_id=%s LIMIT 1",
                (payment_id,)
            )
            row = cur.fetchone()
            if not row:
                return err("Payment not found", 404)

            if int(row["customer_id"]) != int(customer_id):
                return err("Forbidden", 403)

        return ok({"payment": row})
    except Exception as e:
        return err("Server error", 500, str(e))
    finally:
        try: conn.close()
        except: pass
