import json
import sys
import os
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


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
    Get detailed information about a specific booking.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    - Customer must own the booking
    
    Path Parameters:
    - booking_id: ID of the booking to retrieve
    
    Returns:
    - 200: Booking details
    - 401: Unauthorized
    - 403: Forbidden (booking belongs to another customer)
    - 404: Booking not found
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

    # 2. Get booking_id from path parameters
    try:
        booking_id = event["pathParameters"]["booking_id"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing booking_id in path"})

    # 3. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 4. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 5. Get booking with full details
            cur.execute(
                """
                SELECT 
                    b.booking_id, b.customer_id, b.provider_id,
                    b.service_category, b.service_description,
                    b.scheduled_date, b.scheduled_time, b.status,
                    b.service_address, b.service_city, b.service_state, b.service_postal_code,
                    b.estimated_price, b.final_price, b.notes,
                    b.created_at, b.updated_at, b.completed_at,
                    c.first_name AS customer_first_name,
                    c.last_name AS customer_last_name,
                    c.email AS customer_email,
                    c.phone AS customer_phone,
                    sp.first_name AS provider_first_name,
                    sp.last_name AS provider_last_name,
                    sp.business_name AS provider_business_name,
                    sp.email AS provider_email,
                    sp.phone AS provider_phone,
                    sp.category AS provider_category,
                    sp.rating AS provider_rating,
                    sp.bio AS provider_bio
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                JOIN service_providers sp ON b.provider_id = sp.provider_id
                WHERE b.booking_id = %s
                """,
                (booking_id,)
            )
            row = cur.fetchone()

        if not row:
            return _response(404, {"message": "Booking not found"})

        # 6. Verify customer owns this booking
        if row["customer_id"] != customer_id:
            return _response(403, {"message": "You do not have permission to view this booking"})

        # 7. Format booking details
        booking = {
            "booking_id": row["booking_id"],
            "customer": {
                "customer_id": row["customer_id"],
                "name": f"{row['customer_first_name']} {row['customer_last_name']}",
                "email": row["customer_email"],
                "phone": row["customer_phone"]
            },
            "provider": {
                "provider_id": row["provider_id"],
                "name": f"{row['provider_first_name']} {row['provider_last_name']}",
                "business_name": row["provider_business_name"],
                "email": row["provider_email"],
                "phone": row["provider_phone"],
                "category": row["provider_category"],
                "rating": float(row["provider_rating"]) if row["provider_rating"] else 0.0,
                "bio": row["provider_bio"]
            },
            "service": {
                "category": row["service_category"],
                "description": row["service_description"]
            },
            "schedule": {
                "date": str(row["scheduled_date"]),
                "time": str(row["scheduled_time"])
            },
            "status": row["status"],
            "location": {
                "address": row["service_address"],
                "city": row["service_city"],
                "state": row["service_state"],
                "postal_code": row["service_postal_code"]
            },
            "pricing": {
                "estimated_price": float(row["estimated_price"]) if row["estimated_price"] else None,
                "final_price": float(row["final_price"]) if row["final_price"] else None
            },
            "notes": row["notes"],
            "timestamps": {
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None
            }
        }

        return _response(200, {"booking": booking})

    except Exception as e:
        print(f"Error fetching booking details: {e}")
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
        "pathParameters": {
            "booking_id": "1"
        }
    }

    print("🔍 Running local test for get_booking_details.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
