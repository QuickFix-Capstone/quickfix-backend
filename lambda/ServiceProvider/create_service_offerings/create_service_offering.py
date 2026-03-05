import json
from typing import Any, Dict
from pymysql.err import IntegrityError
import sys, os

from db.rds_main import get_connection


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
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
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
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
        return __response(500, {"message": "Database connection failed"})

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
