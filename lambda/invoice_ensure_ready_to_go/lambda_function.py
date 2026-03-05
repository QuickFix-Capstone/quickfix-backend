import json
import os
import boto3
from botocore.exceptions import ClientError

# Env vars required:
# - INVOICE_BUCKET = quickfix-invoices-dev
# - INVOICE_JOBS_QUEUE_URL = https://sqs.<region>.amazonaws.com/<acct>/invoice-jobs-dev
# Optional:
# - INVOICE_URL_TTL_SECONDS = 900
# - CORS_ALLOW_ORIGIN = http://localhost:5173  (or https://your-frontend-domain)

def _cors_origin():
    return os.getenv("CORS_ALLOW_ORIGIN", "*")

def _cors_headers():
    return {
        "Access-Control-Allow-Origin": _cors_origin(),
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }

def _resp(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {**_cors_headers(), "Content-Type": "application/json"},
        "body": json.dumps(body),
    }

def _invoice_key(payment_id: int) -> str:
    return f"invoices/{payment_id}/invoice.pdf"

def _s3_exists(s3, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey", "NotFound"):
            return False
        raise

def _presign(s3, bucket: str, key: str, ttl: int) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=ttl,
    )

def handler(event, context):
    # Handle CORS preflight
    method = (event or {}).get("requestContext", {}).get("http", {}).get("method") or (event or {}).get("httpMethod")
    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": _cors_headers(),
            "body": "",
        }

    # Path param: /payments/{paymentId}/invoice/ensure
    path_params = (event or {}).get("pathParameters") or {}
    payment_id_raw = path_params.get("paymentId") or path_params.get("payment_id") or path_params.get("id")

    # Allow payment_id in JSON body as fallback
    if not payment_id_raw:
        try:
            body = json.loads((event or {}).get("body") or "{}")
            payment_id_raw = body.get("payment_id") or body.get("paymentId")
        except Exception:
            payment_id_raw = None

    try:
        payment_id = int(payment_id_raw)
        if payment_id <= 0:
            raise ValueError()
    except Exception:
        return _resp(400, {"error": "Invalid paymentId"})

    bucket = os.getenv("INVOICE_BUCKET")
    queue_url = os.getenv("INVOICE_JOBS_QUEUE_URL")
    if not bucket:
        return _resp(500, {"error": "Missing env var INVOICE_BUCKET"})
    if not queue_url:
        return _resp(500, {"error": "Missing env var INVOICE_JOBS_QUEUE_URL"})

    ttl = int(os.getenv("INVOICE_URL_TTL_SECONDS", "900"))
    key = _invoice_key(payment_id)

    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")

    try:
        if _s3_exists(s3, bucket, key):
            url = _presign(s3, bucket, key, ttl)
            return _resp(200, {
                "payment_id": payment_id,
                "invoice_available": True,
                "invoice_url": url,
                "s3_key": key,
                "ttl_seconds": ttl,
            })

        # Not available yet -> queue job
        msg = {"payment_id": payment_id, "reason": "receipt_page"}
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(msg))

        return _resp(202, {
            "payment_id": payment_id,
            "invoice_available": False,
            "status": "queued",
            "s3_key": key,
        })
    except Exception as e:
        return _resp(500, {
            "error": "Failed to ensure invoice",
            "detail": str(e),
            "payment_id": payment_id,
            "s3_key": key
        })
