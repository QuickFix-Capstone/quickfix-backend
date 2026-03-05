import json
import os
import boto3

from src.db import get_conn

# SQS message body: {"payment_id": 123, "source": "stripe_webhook"}

def _money(cents, currency="CAD"):
    try:
        cents = int(cents or 0)
    except Exception:
        cents = 0
    return f"{currency.upper()} {cents/100:.2f}"

def _get_invoice_s3_key(payment_id: int) -> str:
    return f"invoices/{payment_id}/invoice.pdf"

def _head_s3(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False

def _presign(s3, bucket: str, key: str, ttl: int) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=ttl
    )

def _fetch_invoice_data(conn, payment_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              p.*,
              j.title,
              j.description,
              j.category,
              j.location_address,
              j.location_city,
              j.location_state,
              j.location_zip,
              j.completed_at,

              c.first_name  AS customer_first_name,
              c.last_name   AS customer_last_name,
              c.email       AS customer_email,

              sp.name       AS provider_name,
              sp.email      AS provider_email
            FROM payment p
            JOIN jobs j ON j.job_id = p.job_id
            JOIN customers c ON c.customer_id = p.customer_id
            JOIN service_providers sp ON sp.provider_id = p.provider_id
            WHERE p.payment_id = %s
            LIMIT 1
            """,
            (payment_id,)
        )
        return cur.fetchone()

def _build_invoice_number(payment_id: int) -> str:
    return f"INV-{payment_id:07d}"

def _render_pdf_reportlab(invoice_number: str, data: dict) -> bytes:
    # Requires reportlab via a Lambda Layer for Python 3.12
    import io
    import os
    os.environ["RL_NO_PIL"] = "1"
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 60, "QuickFix Invoice")

    c.setFont("Helvetica", 11)
    c.drawString(50, height - 85, f"Invoice #: {invoice_number}")
    c.drawString(50, height - 100, f"Payment ID: {data.get('payment_id')}")
    c.drawString(50, height - 115, f"Date Paid: {data.get('paid_at') or 'N/A'}")
    c.drawString(50, height - 130, f"Method: {data.get('payment_method') or 'N/A'}")
    c.drawString(50, height - 145, f"Reference: {data.get('provider_payment_id') or ''}")

    y = height - 180
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Billed To (Customer)")
    c.setFont("Helvetica", 11)
    y -= 16
    c.drawString(50, y, f"{(data.get('customer_first_name','') + ' ' + data.get('customer_last_name','')).strip()}")
    y -= 14
    c.drawString(50, y, f"{data.get('customer_email','')}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Service Provider")
    c.setFont("Helvetica", 11)
    y -= 16
    c.drawString(50, y, f"{data.get('provider_name','')}".strip())
    y -= 14
    c.drawString(50, y, f"{data.get('provider_email','')}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Job")
    c.setFont("Helvetica", 11)
    y -= 16
    c.drawString(50, y, f"Title: {data.get('title','')}")
    y -= 14
    loc = ", ".join([x for x in [data.get("location_address"), data.get("location_city"), data.get("location_state"), data.get("location_zip")] if x])
    c.drawString(50, y, f"Location: {loc}")

    y -= 35
    currency = data.get("currency") or "CAD"
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Amount Breakdown")
    c.setFont("Helvetica", 11)
    y -= 18

    lines = [
        ("Base Amount", _money(data.get("base_amount_cents"), currency)),
        ("Tax", _money(data.get("tax_cents"), currency)),
        ("App Fee", _money(data.get("app_fee_cents"), currency)),
        ("Total Paid", _money(data.get("final_amount_cents"), currency)),
    ]
    for label, val in lines:
        c.drawString(50, y, label)
        c.drawRightString(width - 50, y, val)
        y -= 16

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 50, "Thank you for using QuickFix.")
    c.showPage()
    c.save()

    return buf.getvalue()

def _send_email_ses(subject: str, body_text: str, to_addrs: list):
    from_email = os.getenv("SES_FROM_EMAIL")
    if not from_email or not to_addrs:
        return
    ses = boto3.client("ses")
    ses.send_email(
        Source=from_email,
        Destination={"ToAddresses": to_addrs},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Text": {"Data": body_text, "Charset": "UTF-8"}},
        },
    )

def _process_one(payment_id: int):
    bucket = os.getenv("INVOICE_BUCKET")
    if not bucket:
        raise RuntimeError("Missing env var INVOICE_BUCKET")

    ttl = int(os.getenv("INVOICE_URL_TTL_SECONDS", "900"))
    s3 = boto3.client("s3")
    key = _get_invoice_s3_key(payment_id)

    conn = get_conn()
    try:
        data = _fetch_invoice_data(conn, payment_id)
        if not data:
            return {"payment_id": payment_id, "status": "skipped", "reason": "payment_not_found"}

        if (data.get("status") or "").lower() != "paid":
            return {"payment_id": payment_id, "status": "skipped", "reason": "not_paid"}

        invoice_number = _build_invoice_number(payment_id)

        if not _head_s3(s3, bucket, key):
            pdf_bytes = _render_pdf_reportlab(invoice_number, data)
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=pdf_bytes,
                ContentType="application/pdf",
                ServerSideEncryption="AES256",
                Metadata={"invoice_number": invoice_number, "payment_id": str(payment_id)},
            )

        url = _presign(s3, bucket, key, ttl)

        subject = f"QuickFix Invoice {invoice_number}"
        body = (
            f"Invoice: {invoice_number}\n"
            f"Payment ID: {payment_id}\n"
            f"Job: {data.get('title','')}\n"
            f"Total Paid: {_money(data.get('final_amount_cents'), data.get('currency') or 'CAD')}\n\n"
            f"Download (link expires in {max(1, ttl//60)} minutes):\n{url}\n"
        )

        _send_email_ses(subject, body, [data.get("customer_email")] if data.get("customer_email") else [])
        _send_email_ses(subject, body, [data.get("provider_email")] if data.get("provider_email") else [])

        return {"payment_id": payment_id, "status": "ok", "invoice_number": invoice_number, "s3_key": key}
    finally:
        try:
            conn.close()
        except Exception:
            pass

def handler(event, context):
    results = []
    for r in (event or {}).get("Records", []) or []:
        body = r.get("body") or "{}"
        msg = json.loads(body)
        payment_id = int(msg.get("payment_id"))
        results.append(_process_one(payment_id))
    return {"results": results}
