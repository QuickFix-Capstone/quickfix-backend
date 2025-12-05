import sys
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(PROJECT_ROOT)
print("Python path updated with:", PROJECT_ROOT)
from src.db.rds_main import get_connection


def _parse_body(event):
    if "body" not in event:
        return event
    body = event["body"]
    if isinstance(body, str):
        return json.loads(body)
    return body


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    data = _parse_body(event)

    offering_id = data.get("offering_id")
    if not offering_id:
        return _response(400, {"message": "offering_id is required"})

    fields = []
    values = []

    allowed = [
        "title", "summary", "description", "category",
        "price", "city", "state", "postal_code", "availability"
    ]

    for key in allowed:
        if key in data:
            fields.append(f"{key}=%s")
            values.append(data[key])

    if not fields:
        return _response(400, {"message": "No fields to update"})

    values.append(offering_id)

    sql = f"UPDATE service_offerings SET {', '.join(fields)} WHERE offering_id=%s"

    conn = get_connection()
    if not conn:
        return _response(500, {"message": "DB connection failed"})

    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            conn.commit()

        return _response(200, {"message": "Offering updated"})

    except Exception as e:
        print("ERROR:", e)
        return _response(500, {"message": "Internal server error"})
    finally:
        conn.close()


if __name__ == "__main__":
    test_event = {
        "body": json.dumps({
            "offering_id": 3,
            "price": 120,
            "city": "Brampton"
        })
    }
    print(json.dumps(handler(test_event, None), indent=2))
