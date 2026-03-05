import os
import boto3
from src.response import ok, err
from src.event import get_jwt_sub
from src.db import get_conn

s3 = boto3.client("s3")

def _path_param(event, key):
    pp = event.get("pathParameters") or {}
    return pp.get(key)

def lambda_handler(event, context):
    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    refund_request_id = _path_param(event, "refund_request_id")
    if not refund_request_id:
        return err("refund_request_id required in path", 400)

    bucket = os.getenv("REFUND_BUCKET")
    ttl = int(os.getenv("REFUND_VIEW_TTL_SECONDS", "900"))
    if not bucket:
        return err("Server misconfigured: REFUND_BUCKET missing", 500)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT refund_request_id, payment_id, job_id, customer_id, provider_id, "
                "reason_code, reason_text, status, admin_note, payment_method, "
                "requested_at, reviewed_at, refunded_at, gateway_refund_id "
                "FROM refund_request WHERE refund_request_id=%s LIMIT 1",
                (refund_request_id,)
            )
            rr = cur.fetchone()

        if not rr:
            return err("Refund request not found", 404)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT refund_attachment_id, s3_key, content_type, created_at "
                "FROM refund_request_attachment "
                "WHERE refund_request_id=%s "
                "ORDER BY created_at ASC",
                (refund_request_id,)
            )
            atts = cur.fetchall()

        attachments = []
        for a in atts:
            key = a["s3_key"]
            view_url = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=ttl
            )
            attachments.append({
                "refund_attachment_id": a["refund_attachment_id"],
                "s3_key": key,
                "content_type": a.get("content_type"),
                "created_at": a.get("created_at"),
                "view_url": view_url
            })

        return ok({"refund_request": rr, "attachments": attachments})
    except Exception as e:
        return err("Server error", 500, str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
