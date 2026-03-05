import json
import sys
import os
from typing import Any, Dict
import unittest
import uuid
from unittest.mock import MagicMock, patch



try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    # Likely running this file directly (e.g. python handler.py)
    # -> add project root (quickfix_backend) to sys.path and try again
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)

    from src.db.rds_main import get_connection



def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Get the current customer's profile.

    Authentication:
    - This Lambda expects JWT authorizer (Cognito)
    - Email and Cognito sub must come from event["requestContext"]["authorizer"]["jwt"]["claims"]

    Flow:
    1. Extract email + sub from JWT
    2. Search customer DB by cognito_sub first, fallback to email
    3. If found → return 200 with full customer profile
    4. If not found → return 404 (frontend will know it's first-time user)
    """

    # -----------------------------
    # 1. Extract Cognito JWT claims
    # -----------------------------
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        email = claims.get("email")
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not email:
        return _response(400, {"message": "Invalid token: email missing"})

    # -----------------------------
    # 2. Connect to DB
    # -----------------------------
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # First try cognito_sub → most reliable
            sql = """
                SELECT customer_id, first_name, last_name, email,
                       phone, address, city, state, postal_code, cognito_sub, avatar_url, created_at
                FROM customers
                WHERE cognito_sub = %s OR email = %s
                LIMIT 1
            """
            cur.execute(sql, (cognito_sub, email))
            row = cur.fetchone()

        if not row:
            # This user has no profile yet → first-time user
            return _response(404, {"message": "Customer profile not found"})

        # Build response
        customer = {
            "customer_id": row["customer_id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "email": row["email"],
            "phone": row["phone"],
            "address": row["address"],
            "city": row["city"],
            "state": row["state"],
            "postal_code": row["postal_code"],
            "cognito_sub": row["cognito_sub"],
            "avatar_url": row["avatar_url"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }

        return _response(200, {"customer": customer})

    except Exception as e:
        print("Error in get_customer:", e)
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass


class TestGetCustomer(unittest.TestCase):
    def setUp(self):
        # Generate unique test data
        self.test_email = f"test_{uuid.uuid4()}@example.com"
        self.test_sub = f"sub_{uuid.uuid4()}"
        self.test_customer_id = None
        
        # Insert test customer into DB
        self.conn = get_connection()
        if self.conn:
            with self.conn.cursor() as cur:
                sql = """
                    INSERT INTO customers (first_name, last_name, email, phone, address, city, state, postal_code, cognito_sub)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, ("TestFirst", "TestLast", self.test_email, "555-0000", "123 Test St", "TestCity", "TS", "00000", self.test_sub))
                self.conn.commit()
                self.test_customer_id = cur.lastrowid
            self.conn.close()

        self.mock_event = {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "email": self.test_email,
                            "sub": self.test_sub
                        }
                    }
                }
            }
        }
        self.mock_context = None

    def tearDown(self):
        # Clean up test data
        if self.test_customer_id:
            conn = get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM customers WHERE customer_id = %s", (self.test_customer_id,))
                    conn.commit()
                conn.close()

    def test_handler_success(self):
        # Test success case with real DB
        response = handler(self.mock_event, self.mock_context)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["customer"]["email"], self.test_email)
        self.assertEqual(body["customer"]["first_name"], "TestFirst")
        self.assertEqual(body["customer"]["cognito_sub"], self.test_sub)

    def test_handler_not_found(self):
        # Test not found case
        event = {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "email": "nonexistent@example.com",
                            "sub": "nonexistent-sub"
                        }
                    }
                }
            }
        }
        response = handler(event, self.mock_context)

        self.assertEqual(response["statusCode"], 404)
        body = json.loads(response["body"])
        self.assertIn("Customer profile not found", body["message"])


if __name__ == "__main__":
    unittest.main()
