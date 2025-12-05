import json
from typing import Any, Dict
from pymysql.err import IntegrityError
import sys,os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(PROJECT_ROOT)

print("Python path updated with:", PROJECT_ROOT)
from src.db.rds_main import get_connection


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support API Gateway or local testing.
    """
    if "body" not in event:
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
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Lambda: Create a service offering

    Expected JSON body:
    {
      "provider_id": 1,
      "title": "Fix leaking sink",
      "category": "plumber",
      "price": 120.50,
      "description": "Leak under the kitchen sink.",
      "city": "Toronto",
      "state": "ON",
      "postal_code": "M5H 2N2",
      "availability": "2025-01-10T14:00"
    }
    """

    # 1. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    required = ["provider_id", "title", "category"]
    missing = [f for f in required if not data.get(f)]

    if missing:
        return _response(
            400,
            {"message": "Missing required fields", "missing": missing},
        )

    # 2. Connect to RDS
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO service_offerings
                    (provider_id, title, category, price, 
                     description, city, state, postal_code, availability)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cur.execute(
                sql,
                (
                    data.get("provider_id"),
                    data.get("title"),
                    data.get("category"),
                    data.get("price"),
                    data.get("description"),
                    data.get("city"),
                    data.get("state"),
                    data.get("postal_code"),
                    data.get("availability"),
                ),
            )
            conn.commit()
            new_id = cur.lastrowid

        return _response(
            201,
            {
                "message": "Service offering created successfully",
                "offering": {
                    "offering_id": new_id,
                    "provider_id": data.get("provider_id"),
                    "title": data.get("title"),
                    "category": data.get("category"),
                },
            },
        )

    except IntegrityError as e:
        return _response(
            400,
            {"message": "Integrity error while saving offering", "error": str(e)},
        )

    except Exception as e:
        print("Unexpected error:", e)
        return _response(
            500, {"message": "Internal server error while creating offering"}
        )

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local test helper
if __name__ == "__main__":
    test_event = {
        "body": json.dumps(
            {
                "provider_id": 5,
                "title": "Ceiling fan installation",
                "category": "electrician",
                "price": 150.0,
                "description": "Install ceiling fan in bedroom.",
                "city": "Toronto",
                "state": "ON",
                "postal_code": "M5H 1K2",
                "availability": "2025-01-12T14:30",
            }
        )
    }

    print("Testing create_service_offering handler()...")
    print(json.dumps(handler(test_event, None), indent=2))