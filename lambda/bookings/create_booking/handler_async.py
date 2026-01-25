import json
import sys
import os
import boto3
from typing import Any, Dict
from datetime import datetime, date, timedelta
from pymysql.err import IntegrityError

try:
    from src.db.rds_main import get_connection
    from src.utils.booking_utils import generate_confirmation_token
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.booking_utils import generate_confirmation_token


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Support both API Gateway event and local testing"""
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
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _send_email_async(booking_data: Dict[str, Any]) -> bool:
    """Send email notification asynchronously via SQS"""
    try:
        sqs = boto3.client('sqs')
        queue_url = os.environ.get('EMAIL_QUEUE_URL')
        
        if not queue_url:
            print("⚠️  EMAIL_QUEUE_URL not configured, skipping async email")
            return False
        
        # Send message to SQS queue for async processing
        message = {
            'email_type': 'booking_confirmation',
            'booking_data': booking_data
        }
        
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'EmailType': {
                    'StringValue': 'booking_confirmation',
                    'DataType': 'String'
                }
            }
        )
        
        print(f"✅ Email queued for async processing. MessageId: {response.get('MessageId')}")
        return True
        
    except Exception as e:
        print(f"⚠️  Failed to queue email: {e}")
        return False


def handler(event, context):
    """Create a new booking with async email processing"""
    
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

    # 3. Validate required fields
    required_fields = [
        "provider_id", "service_category", "service_description",
        "scheduled_date", "scheduled_time", "service_address",
        "service_city", "service_state", "service_postal_code"
    ]
    
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return _response(400, {
            "message": "Missing required fields",
            "missing": missing
        })

    # 4. Validate date is in the future
    try:
        scheduled_date = datetime.strptime(data["scheduled_date"], "%Y-%m-%d").date()
        if scheduled_date < date.today():
            return _response(400, {"message": "Scheduled date must be in the future"})
    except ValueError:
        return _response(400, {"message": "Invalid date format. Use YYYY-MM-DD"})

    # 5. Validate time format
    try:
        datetime.strptime(data["scheduled_time"], "%H:%M")
    except ValueError:
        return _response(400, {"message": "Invalid time format. Use HH:MM"})

    # 6. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 7. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 8. Verify provider exists and is active
            cur.execute(
                """
                SELECT provider_id, name, email, is_active
                FROM service_providers
                WHERE provider_id = %s
                """,
                (data["provider_id"],)
            )
            provider_row = cur.fetchone()
            
            if not provider_row:
                return _response(404, {"message": "Service provider not found"})
            
            if not provider_row["is_active"]:
                return _response(400, {"message": "Service provider is not active"})

            # 9. Create booking
            sql = """
                INSERT INTO bookings
                    (customer_id, provider_id, service_category, service_description,
                     scheduled_date, scheduled_time, service_address, service_city,
                     service_state, service_postal_code, estimated_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(sql, (
                customer_id,
                data["provider_id"],
                data["service_category"],
                data["service_description"],
                data["scheduled_date"],
                data["scheduled_time"],
                data["service_address"],
                data["service_city"],
                data["service_state"],
                data["service_postal_code"],
                data.get("estimated_price"),
                data.get("notes")
            ))
            
            conn.commit()
            booking_id = cur.lastrowid

            # 10. Generate confirmation token
            confirmation_token = generate_confirmation_token(booking_id, data["provider_id"])
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            # 11. Update booking with token and set status to pending_confirmation
            cur.execute("""
                UPDATE bookings 
                SET confirmation_token = %s, 
                    confirmation_token_expires_at = %s,
                    status = 'pending_confirmation'
                WHERE booking_id = %s
            """, (confirmation_token, expires_at, booking_id))
            conn.commit()
            
            # 12. Get customer name for email
            cur.execute("""
                SELECT first_name, last_name 
                FROM customers 
                WHERE customer_id = %s
            """, (customer_id,))
            customer = cur.fetchone()
            
            # 13. Queue email for async processing (non-blocking)
            email_data = {
                "provider_email": provider_row["email"],
                "provider_name": provider_row["name"],
                "booking_details": {
                    "booking_id": booking_id,
                    "service_category": data["service_category"],
                    "service_description": data.get("service_description", ""),
                    "scheduled_date": str(data["scheduled_date"]),
                    "scheduled_time": data["scheduled_time"],
                    "service_address": data["service_address"],
                    "customer_name": f"{customer['first_name']} {customer['last_name']}",
                    "estimated_price": data.get("estimated_price")
                },
                "confirmation_token": confirmation_token
            }
            
            # Send email asynchronously - don't wait for result
            _send_email_async(email_data)

            # 14. Fetch created booking
            cur.execute(
                """
                SELECT booking_id, customer_id, provider_id, service_category,
                       service_description, scheduled_date, scheduled_time, status,
                       service_address, service_city, service_state, service_postal_code,
                       estimated_price, final_price, notes, created_at, updated_at
                FROM bookings
                WHERE booking_id = %s
                """,
                (booking_id,)
            )
            booking_row = cur.fetchone()

        booking = {
            "booking_id": booking_row["booking_id"],
            "customer_id": booking_row["customer_id"],
            "provider_id": booking_row["provider_id"],
            "provider_name": provider_row["name"],
            "service_category": booking_row["service_category"],
            "service_description": booking_row["service_description"],
            "scheduled_date": str(booking_row["scheduled_date"]),
            "scheduled_time": str(booking_row["scheduled_time"]),
            "status": booking_row["status"],
            "service_address": booking_row["service_address"],
            "service_city": booking_row["service_city"],
            "service_state": booking_row["service_state"],
            "service_postal_code": booking_row["service_postal_code"],
            "estimated_price": float(booking_row["estimated_price"]) if booking_row["estimated_price"] else None,
            "final_price": float(booking_row["final_price"]) if booking_row["final_price"] else None,
            "notes": booking_row["notes"],
            "created_at": booking_row["created_at"].isoformat() if booking_row["created_at"] else None,
            "updated_at": booking_row["updated_at"].isoformat() if booking_row["updated_at"] else None
        }

        return _response(201, {
            "message": "Booking created successfully",
            "booking": booking,
            "email_status": "queued_for_processing"
        })

    except IntegrityError as e:
        print(f"Integrity error: {e}")
        return _response(400, {"message": "Failed to create booking due to data constraint"})

    except Exception as e:
        print(f"Error creating booking: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass