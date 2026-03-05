import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import json
from typing import Any, Dict
from pymysql.err import IntegrityError
# from db.rds_main import get_connection
from db.rds_main import get_connection


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    GET service offerings.
    
    Query params supported:
      - provider_id  (optional)
      
    Example:
       GET /offerings             → returns all
       GET /offerings?provider_id=3 → returns provider's offerings
    """

    provider_id = None

    # Extract from API Gateway GET params
    if event.get("queryStringParameters"):
        provider_id = event["queryStringParameters"].get("provider_id")

    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            if provider_id:
                sql = "SELECT * FROM service_offerings WHERE provider_id = %s"
                cur.execute(sql, (provider_id,))
            else:
                sql = "SELECT * FROM service_offerings"
                cur.execute(sql)

            offerings = cur.fetchall()
            # Convert Decimals & datetimes to JSON-safe strings
            offerings = json.loads(json.dumps(offerings, default=str))

        return _response(
            200,
            {"count": len(offerings), "offerings": offerings}
        )

    except Exception as e:
        print("Unexpected error:", e)
        return _response(500, {"message": "Internal server error when fetching offerings"})

    finally:
        try:
            conn.close()
        except:
            pass


# # Local test
# if __name__ == "__main__":
#     event = {
#         "queryStringParameters": {"provider_id": "5"}
#     }
#     print(json.dumps(handler(event, None), indent=2))
