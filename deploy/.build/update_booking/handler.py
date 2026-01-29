import json
import sys
import os
from typing import Any, Dict
from datetime import datetime, date, time
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
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body),
    }


def validate_reschedule_datetime(scheduled_date, scheduled_time):
    """
    Validate that the new scheduled date/time is in the future.
    
    Args:
        scheduled_date: Date string (YYYY-MM-DD) or date object
        scheduled_time: Time string (HH:MM:SS) or time object
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        # Convert strings to date/time objects if needed
        if isinstance(scheduled_date, str):
            scheduled_date = date.fromisoformat(scheduled_date)
        if isinstance(scheduled_time, str):
            scheduled_time = time.fromisoformat(scheduled_time)
        
        # Combine date and time
        scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
        
        # Check if in the future
        if scheduled_datetime <= datetime.now():
            return False, "Scheduled date and time must be in the future"
        
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Invalid date/time format: {str(e)}"


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
                SELECT booking_id, customer_id, status, scheduled_date, scheduled_time
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

        # 9. Define allowed transitions and updatable fields for customers
        allowed_transitions = {
            "pending": ["cancelled", "pending_reschedule"],
            "pending_confirmation": ["cancelled"],
            "confirmed": ["cancelled", "pending_reschedule"],
            "pending_reschedule": ["cancelled", "confirmed"],
            "in_progress": [],
            "completed": [],
            "cancelled": []
        }
        
        updatable_fields = {
            "pending": ["status", "notes", "scheduled_date", "scheduled_time", 
                       "service_address", "service_city", "service_state", "service_postal_code"],
            "pending_confirmation": ["status", "notes", "scheduled_date", "scheduled_time",
                                    "service_address", "service_city", "service_state", "service_postal_code"],
            "confirmed": ["status", "notes", "scheduled_date", "scheduled_time"],
            "pending_reschedule": ["status", "notes", "scheduled_date", "scheduled_time"],
            "in_progress": [],
            "completed": [],
            "cancelled": []
        }
        
        # 10. Validate which fields can be updated based on current status
        allowed_fields = updatable_fields.get(current_status, [])
        for field in data.keys():
            if field not in allowed_fields:
                return _response(400, {
                    "message": f"Cannot update '{field}' when booking status is '{current_status}'"
                })
        
        # 11. Validate status transition if status is being updated
        if "status" in data:
            new_status = data["status"]
            
            if current_status not in allowed_transitions:
                return _response(400, {
                    "message": f"Cannot update booking with status '{current_status}'"
                })
            
            if new_status not in allowed_transitions[current_status]:
                return _response(400, {
                    "message": f"Cannot change status from '{current_status}' to '{new_status}'"
                })
        
        # 12. Validate rescheduling date/time if being updated
        if "scheduled_date" in data or "scheduled_time" in data:
            # Get current booking details for date/time
            # We already fetched scheduled_date and scheduled_time in booking_row
            current_booking_date = booking_row["scheduled_date"]
            current_booking_time = booking_row["scheduled_time"]
            
            new_date = data.get("scheduled_date", current_booking_date)
            new_time = data.get("scheduled_time", current_booking_time)
            
            is_valid, error_msg = validate_reschedule_datetime(new_date, new_time)
            if not is_valid:
                return _response(400, {"message": error_msg})
            
            # If confirmed booking is being rescheduled, auto-change status to pending_reschedule
            if current_status == "confirmed" and "status" not in data:
                data["status"] = "pending_reschedule"
            
            # Also apply to pending_confirmation
            if current_status == "pending_confirmation" and "status" not in data:
                data["status"] = "pending_reschedule"

        # 13. Build UPDATE query
        updates = []
        values = []
        
        # Status
        if "status" in data:
            updates.append("status = %s")
            values.append(data["status"])
        
        # Notes
        if "notes" in data:
            updates.append("notes = %s")
            values.append(data["notes"])
        
        # Scheduling
        if "scheduled_date" in data:
            updates.append("scheduled_date = %s")
            values.append(data["scheduled_date"])
        
        if "scheduled_time" in data:
            updates.append("scheduled_time = %s")
            values.append(data["scheduled_time"])
        
        # Address fields
        if "service_address" in data:
            updates.append("service_address = %s")
            values.append(data["service_address"])
        
        if "service_city" in data:
            updates.append("service_city = %s")
            values.append(data["service_city"])
        
        if "service_state" in data:
            updates.append("service_state = %s")
            values.append(data["service_state"])
        
        if "service_postal_code" in data:
            updates.append("service_postal_code = %s")
            values.append(data["service_postal_code"])
        
        values.append(booking_id)
        
        sql = f"UPDATE bookings SET {', '.join(updates)} WHERE booking_id = %s"
        
        with conn.cursor() as cur:
            cur.execute(sql, tuple(values))
            conn.commit()

            # 14. Fetch updated booking with full details (match get_booking_details structure)
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
                    sp.name AS provider_name,
                    sp.business_name AS provider_business_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                JOIN service_providers sp ON b.provider_id = sp.provider_id
                WHERE b.booking_id = %s
                """,
                (booking_id,)
            )
            row = cur.fetchone()

        # Format response to match get_booking_details structure
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
                "name": row["provider_name"],
                "business_name": row["provider_business_name"]
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
