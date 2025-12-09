import json
from typing import Any, Dict

from src.db.rds_main import get_connection
from pymysql.err import IntegrityError


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support both:
    - API Gateway event: event["body"] is a JSON string
    - Local testing: event itself is already a dict
    """
    if "body" not in event:
        # Assume direct dict for local testing
        return event

    body = event["body"]

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

    raise ValueError("Unsupported body format")


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Lambda entrypoint for creating (registering) a new customer.

    Expected JSON input (in event["body"] when via API Gateway):

    {
      "first_name": "Alice",
      "last_name": "Wong",
      "email": "alice@example.com",
      "phone": "416-555-1234",        # optional
      "address": "123 King St",       # optional
      "city": "Toronto",              # optional
      "state": "ON",                  # optional
      "postal_code": "M5H 1J9",       # optional
      "cognito_sub": "xyz-123"        # optional, if using Cognito
    }
    """
    # 1) Parse and validate input
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    required_fields = ["first_name", "last_name", "email"]
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return _response(
            400,
            {
                "message": "Missing required fields",
                "missing": missing,
            },
        )

    # 2) Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO customers
                    (first_name, last_name, email,
                     phone, address, city, state,
                     postal_code, cognito_sub)
                VALUES (%s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s)
            """
            cur.execute(
                sql,
                (
                    data.get("first_name"),
                    data.get("last_name"),
                    data.get("email"),
                    data.get("phone"),
                    data.get("address"),
                    data.get("city"),
                    data.get("state"),
                    data.get("postal_code"),
                    data.get("cognito_sub"),
                ),
            )
            conn.commit()
            new_id = cur.lastrowid

        # 3) Build success response
        return _response(
            201,
            {
                "message": "Customer created successfully",
                "customer": {
                    "customer_id": new_id,
                    "first_name": data.get("first_name"),
                    "last_name": data.get("last_name"),
                    "email": data.get("email"),
                },
            },
        )

    except IntegrityError as e:
        # Likely a duplicate email if you have UNIQUE(email)
        if "Duplicate entry" in str(e):
            return _response(
                409,
                {"message": "A customer with this email already exists."},
            )
        # Other integrity errors
        return _response(
            400,
            {"message": "Failed to create customer due to data constraint."},
        )

    except Exception as e:
        # Generic unexpected error
        print("Unexpected error in create_customer:", e)
        return _response(
            500,
            {"message": "Internal server error while creating customer."},
        )

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Optional: local test helper
if __name__ == "__main__":
    # Simulate an API Gateway event for quick local testing
    test_event = {
        "body": json.dumps(
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "test.user@example.com",
                "phone": "123-456-7890",
                "address": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "T3S 7T1",
                "cognito_sub": None,
            }
        )
    }

    print("🔍 Running local test for create_customer.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))