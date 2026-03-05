import json

# NOTE:
# - Allow both Authorization and authorization (some browsers/libraries lowercase it)
# CORS note:
# If you use Access-Control-Allow-Origin: "*" you must NOT also send
# Access-Control-Allow-Credentials: true, or browsers will block the response.
# So we intentionally do not send Allow-Credentials here.
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,authorization,Stripe-Signature",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
}


def ok(body, status_code=200, extra_headers=None):
    headers = dict(CORS_HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body, default=str),
    }

def err(message, status_code=400, details=None):
    body = {"error": message}
    if details is not None:
        body["details"] = details
    return ok(body, status_code=status_code)
