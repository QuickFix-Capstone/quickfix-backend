import json
import base64
import os
from typing import Any, Dict

import boto3
from src.db.rds_main import get_connection
from pymysql.err import IntegrityError

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=os.environ.get('AWS_REGION', 'us-east-2'))
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', 'us-east-2_45z5OMePi')


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


def _extract_email_from_jwt(event: Dict[str, Any]) -> str:
    """
    Extract email from JWT token in Authorization header.
    Returns None if extraction fails.
    """
    try:
        # Get headers (handle both lowercase and capitalized)
        headers = event.get('headers', {})
        
        # Try different header key variations
        auth_header = (
            headers.get('Authorization') or 
            headers.get('authorization') or 
            ''
        )
        
        print(f"🔍 Debug: Headers keys: {list(headers.keys())}")
        print(f"🔍 Debug: Auth header present: {bool(auth_header)}")
        
        if not auth_header:
            print("⚠️ No Authorization header found")
            return None
            
        if not auth_header.startswith('Bearer '):
            print(f"⚠️ Authorization header doesn't start with 'Bearer ': {auth_header[:20]}...")
            return None
        
        token = auth_header.replace('Bearer ', '')
        print(f"🔍 Debug: Token extracted (first 20 chars): {token[:20]}...")
        
        # Decode JWT payload (second part of token)
        parts = token.split('.')
        if len(parts) != 3:
            print(f"⚠️ Invalid JWT format: expected 3 parts, got {len(parts)}")
            return None
            
        payload = parts[1]
        
        # Add padding if needed for base64 decoding
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded = base64.b64decode(payload)
        claims = json.loads(decoded)
        
        email = claims.get('email')
        print(f"🔍 Debug: Extracted email from JWT: {email}")
        
        return email
    except Exception as e:
        print(f"⚠️ Failed to extract email from JWT: {e}")
        import traceback
        print(f"⚠️ Traceback: {traceback.format_exc()}")
        return None


def _add_user_to_customer_group(email: str) -> bool:
    """
    Add user to customer group in Cognito.
    Returns True if successful, False otherwise.
    """
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=email,  # Cognito uses email as username
            GroupName='customer'
        )
        print(f"✅ Successfully added {email} to customer group")
        return True
    except cognito_client.exceptions.ResourceNotFoundException:
        print(f"⚠️ Customer group does not exist in Cognito")
        return False
    except Exception as e:
        print(f"⚠️ Failed to add user to group: {e}")
        return False


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
            cur.execute(
                """
                SELECT customer_id, first_name, last_name, email, created_at
                FROM customers
                WHERE customer_id = %s
                LIMIT 1
                """,
                (new_id,),
            )
            created_customer = cur.fetchone()

        # 3) Add user to Cognito customer group
        # Try to extract email from JWT first, fallback to request body
        user_email = _extract_email_from_jwt(event)
        if not user_email:
            # Fallback: use email from request body
            user_email = data.get("email")
            print(f"ℹ️ Using email from request body: {user_email}")
        
        if user_email:
            _add_user_to_customer_group(user_email)
        else:
            print("⚠️ No email available for group assignment")

        # 4) Build success response
        return _response(
            201,
            {
                "message": "Customer created successfully",
                "customer": {
                    "customer_id": created_customer["customer_id"] if created_customer else new_id,
                    "first_name": created_customer["first_name"] if created_customer else data.get("first_name"),
                    "last_name": created_customer["last_name"] if created_customer else data.get("last_name"),
                    "email": created_customer["email"] if created_customer else data.get("email"),
                    "created_at": (
                        created_customer["created_at"].isoformat()
                        if created_customer and created_customer.get("created_at")
                        else None
                    ),
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
