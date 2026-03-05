import os
import uuid
import boto3

from src.response import ok, err
from src.event import get_jwt_sub, get_json_body
from src.db import get_conn
from src.sql_helpers import get_customer_id_by_sub, get_payment_by_id

s3 = boto3.client("s3")

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg"}
def _safe_filename(name: str) -> str:
    # keep it simple; prevent weird paths
    name = (name or "file").split("/")[-1].split("\\")[-1]
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)[:120]

import re

def lambda_handler(event, context):
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    if (event.get("httpMethod") or "").upper() == "OPTIONS":
        return ok({"ok": True}, 200)

    body = get_json_body(event)
    payment_id = body.get("payment_id")
    job_id = body.get("job_id")
    files = body.get("files") or []

    bucket = os.getenv("REFUND_BUCKET")
    ttl = int(os.getenv("REFUND_UPLOAD_TTL_SECONDS", "900"))
    max_files = int(os.getenv("REFUND_MAX_FILES", "5"))

    if not bucket:
        return err("Server misconfigured: REFUND_BUCKET missing", 500)

    if not payment_id or not job_id:
        return err("payment_id and job_id required", 400)

    if not isinstance(files, list) or len(files) == 0:
        return err("files[] required", 400)
    if len(files) > max_files:
        return err(f"Too many files (max {max_files})", 400)

    conn = None
    try:
        conn = get_conn()
        customer_id = get_customer_id_by_sub(conn, sub)
        if not customer_id:
            return err("Customer not found", 403)

        payment = get_payment_by_id(conn, payment_id)
        if not payment:
            return err("Payment not found", 404)

        if int(payment.get("customer_id")) != int(customer_id):
            return err("Forbidden", 403)

        if int(payment.get("job_id")) != int(job_id):
            return err("job_id does not match payment", 400)

        if (payment.get("status") or "").lower() != "paid":
            return err("Refunds can only be requested for PAID payments", 400)

        uploads = []
        for f in files:
            f = f or {}
            filename = _safe_filename(f.get("filename") or "file")
            content_type = (f.get("content_type") or "application/octet-stream").lower()
            if content_type not in ALLOWED_TYPES:
                return err(f"Unsupported content_type: {content_type}", 400)

            key = f"refunds/{job_id}/{payment_id}/{uuid.uuid4()}-{filename}"
            url = s3.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": bucket,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=ttl,
            )
            uploads.append({"s3_key": key, "upload_url": url})

        return ok({"uploads": uploads})
    except Exception as e:
        return err("Server error", 500, str(e))
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
