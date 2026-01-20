import json


def response(status_code: int, body: dict):
    """
    Standard HTTP response for AWS Lambda (HTTP API v2)
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PATCH"
        },
        "body": json.dumps(body),
    }
