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
    Update booking status or details.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    - Customer must own the booking
    
    Path Parameters:
    - booking_id: ID of the booking to update
    
    Expected JSON input (in event["body"]):
    {
      "status": "cancelled",  # optional
      "notes": "Updated notes"  # optional
    }
    
    Allowed status transitions for customers:
    - pending -> cancelled
    - confirmed -> cancelled (with restrictions)
    
    Returns:
    - 200: Booking updated successfully
    - 400: Invalid input or status transition
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

    # 3. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 4. Validate at least one field to update
    if "status" not in data and "notes" not in data:
        return _response(400, {"message": "No fields to update"})

    # 5. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 6. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 7. Get current booking
            cur.execute(
                """
                SELECT booking_id, customer_id, status
                FROM bookings
                WHERE booking_id = %s
                """,
                (booking_id,)
            )
            booking_row = cur.fetchone()

        if not booking_row:
            return _response(404, {"message": "Booking not found"})

        # 8. Verify customer owns this booking
        if booking_row["customer_id"] != customer_id:
            return _response(403, {"message": "You do not have permission to update this booking"})

        current_status = booking_row["status"]

        # 9. Validate status transition if status is being updated
        if "status" in data:
            new_status = data["status"]
            
            # Define allowed transitions for customers
            allowed_transitions = {
                "pending": ["cancelled"],
                "confirmed": ["cancelled"]
            }
            
            if current_status not in allowed_transitions:
                return _response(400, {
                    "message": f"Cannot update booking with status '{current_status}'"
                })
            
            if new_status not in allowed_transitions[current_status]:
                return _response(400, {
                    "message": f"Cannot change status from '{current_status}' to '{new_status}'"
                })

        # 10. Build UPDATE query
        updates = []
        values = []
        
        if "status" in data:
            updates.append("status = %s")
            values.append(data["status"])
        
        if "notes" in data:
            updates.append("notes = %s")
            values.append(data["notes"])
        
        values.append(booking_id)
        
        sql = f"UPDATE bookings SET {', '.join(updates)} WHERE booking_id = %s"
        
        with conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            conn.commit()

            # 11. Fetch updated booking
            cur.execute(
                """
                SELECT 
                    b.booking_id, b.customer_id, b.provider_id,
                    b.service_category, b.service_description,
                    b.scheduled_date, b.scheduled_time, b.status,
                    b.service_address, b.service_city, b.service_state, b.service_postal_code,
                    b.estimated_price, b.final_price, b.notes,
                    b.created_at, b.updated_at, b.completed_at,
                    sp.first_name AS provider_first_name,
                    sp.last_name AS provider_last_name
                FROM bookings b
                JOIN service_providers sp ON b.provider_id = sp.provider_id
                WHERE b.booking_id = %s
                """,
                (booking_id,)
            )
            row = cur.fetchone()

        booking = {
            "booking_id": row["booking_id"],
            "customer_id": row["customer_id"],
            "provider_id": row["provider_id"],
            "provider_name": f"{row['provider_first_name']} {row['provider_last_name']}",
            "service_category": row["service_category"],
            "service_description": row["service_description"],
            "scheduled_date": str(row["scheduled_date"]),
            "scheduled_time": str(row["scheduled_time"]),
            "status": row["status"],
            "service_address": row["service_address"],
            "service_city": row["service_city"],
            "service_state": row["service_state"],
            "service_postal_code": row["service_postal_code"],
            "estimated_price": float(row["estimated_price"]) if row["estimated_price"] else None,
            "final_price": float(row["final_price"]) if row["final_price"] else None,
            "notes": row["notes"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None
        }

        return _response(200, {
            "message": "Booking updated successfully",
            "booking": booking
        })

    except Exception as e:
        print(f"Error updating booking: {e}")
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
        },
        "body": json.dumps({
            "status": "cancelled",
            "notes": "No longer needed"
        })
    }

    print("🔍 Running local test for update_booking.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
