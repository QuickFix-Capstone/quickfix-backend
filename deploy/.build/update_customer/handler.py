import json
import sys
import os
from typing import Any, Dict
from pymysql.err import IntegrityError

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support both:
    - API Gateway event: event["body"] is a JSON string
    - Local testing: event itself is already a dict
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
    Update customer profile information.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Expected JSON input (in event["body"]):
    {
      "first_name": "Alice",      # optional
      "last_name": "Wong",         # optional
      "email": "alice@example.com", # optional
      "phone": "416-555-1234",     # optional
      "address": "123 King St",    # optional
      "city": "Toronto",           # optional
      "state": "ON",               # optional
      "postal_code": "M5H 1J9"     # optional
    }
    
    Returns:
    - 200: Customer updated successfully
    - 400: Invalid input
    - 401: Unauthorized
    - 404: Customer not found
    - 500: Server error
    """
    
    # 1. Extract Cognito JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 3. Build UPDATE query dynamically based on provided fields
    updatable_fields = [
        "first_name", "last_name", "email", "phone",
        "address", "city", "state", "postal_code"
    ]
    
    updates = {}
    for field in updatable_fields:
        if field in data and data[field] is not None:
            updates[field] = data[field]

    if not updates:
        return _response(400, {"message": "No fields to update"})

    # 4. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # Build SET clause dynamically
            set_clause = ", ".join([f"{field} = %s" for field in updates.keys()])
            values = list(updates.values())
            values.append(cognito_sub)  # For WHERE clause

            sql = f"""
                UPDATE customers
                SET {set_clause}
                WHERE cognito_sub = %s
            """
            
            cur.execute(sql, values)
            conn.commit()

            if cur.rowcount == 0:
                return _response(404, {"message": "Customer not found"})

            # Fetch updated customer data
            cur.execute(
                """
                SELECT customer_id, first_name, last_name, email,
                       phone, address, city, state, postal_code, cognito_sub
                FROM customers
                WHERE cognito_sub = %s
                """,
                (cognito_sub,)
            )
            row = cur.fetchone()

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
        }

        return _response(200, {
            "message": "Customer updated successfully",
            "customer": customer
        })

    except IntegrityError as e:
        if "Duplicate entry" in str(e):
            return _response(409, {"message": "Email already exists"})
        return _response(400, {"message": "Failed to update customer due to data constraint"})

    except Exception as e:
        print(f"Error updating customer: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    # Test event with mock JWT claims
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "body": json.dumps({
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "555-9999"
        })
    }

    print("🔍 Running local test for update_customer.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
