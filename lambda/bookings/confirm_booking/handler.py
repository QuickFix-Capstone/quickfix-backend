import json
import sys
import os
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.email.ses_service import send_booking_confirmed_notification
    from src.utils.booking_utils import validate_confirmation_token, convert_booking_to_job
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.email.ses_service import send_booking_confirmed_notification
    from src.utils.booking_utils import validate_confirmation_token, convert_booking_to_job


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET, OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Confirm a booking using a confirmation token from email link.
    
    This is a PUBLIC endpoint (no JWT required) - authentication via token.
    
    Query Parameters:
        token (required): Confirmation token from provider's email
    
    Workflow:
        1. Validate token (exists, not expired, booking pending)
        2. Update booking status to 'confirmed'
        3. Create job from booking details
        4. Link booking ↔ job
        5. Send confirmation email to customer
        6. Return success response
    
    Returns:
        200: Booking confirmed successfully, job created
        400: Invalid or expired token
        404: Token not found
        409: Booking already confirmed
        500: Server error
    """
    
    # 1. Extract token from query parameters
    try:
        query_params = event.get("queryStringParameters") or {}
        token = query_params.get("token")
    except Exception as e:
        print(f"Error parsing query parameters: {e}")
        return _response(400, {"message": "Invalid request format"})
    
    if not token:
        return _response(400, {
            "message": "Missing required parameter: token",
            "error_code": "MISSING_TOKEN"
        })
    
    # 2. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})
    
    try:
        # 3. Validate confirmation token
        print(f"🔍 Validating token: {token[:16]}...")
        validation_result = validate_confirmation_token(token, conn)
        
        if not validation_result["valid"]:
            error_code = validation_result.get("error_code", "INVALID_TOKEN")
            error_message = validation_result.get("error", "Invalid token")
            
            print(f"❌ Token validation failed: {error_message}")
            
            # Map error codes to HTTP status codes
            status_code = 400
            if error_code == "TOKEN_NOT_FOUND":
                status_code = 404
            elif error_code == "ALREADY_CONFIRMED":
                status_code = 409
            
            return _response(status_code, {
                "message": error_message,
                "error_code": error_code
            })
        
        booking_id = validation_result["booking_id"]
        print(f"✅ Token valid for booking ID: {booking_id}")
        
        # 4. Convert booking to job
        print(f"🔄 Converting booking {booking_id} to job...")
        job_result = convert_booking_to_job(booking_id, conn)
        
        if not job_result["success"]:
            print(f"❌ Failed to create job: {job_result['error']}")
            return _response(500, {
                "message": "Failed to create job from booking",
                "error": job_result["error"]
            })
        
        job_id = job_result["job_id"]
        print(f"✅ Job created: {job_id}")
        
        # 5. Fetch customer and booking details for email notification
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    b.booking_id,
                    b.service_category,
                    b.service_description,
                    b.scheduled_date,
                    b.scheduled_time,
                    b.service_address,
                    b.service_city,
                    b.service_state,
                    b.estimated_price,
                    c.email as customer_email,
                    c.first_name,
                    c.last_name,
                    sp.name as provider_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                JOIN service_providers sp ON b.provider_id = sp.provider_id
                WHERE b.booking_id = %s
            """, (booking_id,))
            
            booking_data = cur.fetchone()
        
        if not booking_data:
            print(f"⚠️  Warning: Could not fetch booking details for email")
        else:
            # 6. Send confirmation email to customer
            try:
                customer_name = f"{booking_data['first_name']} {booking_data['last_name']}"
                
                email_sent = send_booking_confirmed_notification(
                    customer_email=booking_data['customer_email'],
                    customer_name=customer_name,
                    booking_details={
                        "booking_id": booking_id,
                        "job_id": job_id,
                        "service_category": booking_data['service_category'],
                        "service_description": booking_data['service_description'],
                        "scheduled_date": str(booking_data['scheduled_date']),
                        "scheduled_time": str(booking_data['scheduled_time']),
                        "service_address": booking_data['service_address'],
                        "provider_name": booking_data['provider_name'],
                        "estimated_price": float(booking_data['estimated_price']) if booking_data['estimated_price'] else None
                    }
                )
                
                if email_sent:
                    print(f"✅ Confirmation email sent to {booking_data['customer_email']}")
                else:
                    print(f"⚠️  Warning: Failed to send confirmation email")
                    # Don't fail the confirmation if email fails
                    
            except Exception as email_error:
                print(f"⚠️  Warning: Email error: {email_error}")
                # Don't fail the confirmation if email fails
        
        # 7. Return success response
        return _response(200, {
            "message": "Booking confirmed successfully",
            "booking_id": booking_id,
            "job_id": job_id,
            "status": "confirmed"
        })
    
    except Exception as e:
        print(f"❌ Unexpected error confirming booking: {e}")
        import traceback
        traceback.print_exc()
        return _response(500, {
            "message": "Internal server error",
            "error": str(e)
        })
    
    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    # Test with a real token from database
    # You'll need to get this from the bookings table
    test_event = {
        "queryStringParameters": {
            "token": "YOUR_TOKEN_HERE"  # Replace with actual token from database
        }
    }
    
    print("🔍 Running local test for confirm_booking.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
