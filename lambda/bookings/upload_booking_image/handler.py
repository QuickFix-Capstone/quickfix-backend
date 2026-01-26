import json
import os
import sys
import boto3
from datetime import datetime
from typing import Any, Dict
from botocore.exceptions import ClientError

try:
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        verify_booking_ownership,
        get_booking_images_count,
        is_image_order_available
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        verify_booking_ownership,
        get_booking_images_count,
        is_image_order_available
    )

# Initialize S3 client
s3_client = boto3.client('s3')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'quickfix-app-files')
ALLOWED_CONTENT_TYPES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp'
]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
MAX_IMAGES_PER_BOOKING = 5


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS"
        },
        "body": json.dumps(body),
    }


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


def handler(event, context):
    """
    Generate presigned S3 URL for booking image upload.

    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims

    Path Parameters:
    - booking_id: ID of the booking

    Expected JSON input (in event["body"]):
    {
      "file_name": "kitchen_photo.jpg",
      "content_type": "image/jpeg",
      "image_order": 1
    }

    Returns:
    - 200: Presigned URL generated successfully
    - 400: Invalid input / Max images exceeded / Invalid image_order
    - 401: Unauthorized
    - 403: Forbidden (not booking owner)
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
        booking_id = int(booking_id)
    except (KeyError, ValueError, TypeError):
        return _response(400, {"message": "Invalid or missing booking_id"})

    # 3. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 4. Validate required fields
    file_name = data.get("file_name")
    content_type = data.get("content_type")
    image_order = data.get("image_order")

    if not file_name:
        return _response(400, {"message": "Missing required field: file_name"})

    if not content_type:
        return _response(400, {"message": "Missing required field: content_type"})

    if not image_order:
        return _response(400, {"message": "Missing required field: image_order"})

    # 5. Validate content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        return _response(400, {
            "message": f"Invalid content type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        })

    # 6. Validate image_order (1-5)
    try:
        image_order = int(image_order)
        if image_order < 1 or image_order > 5:
            return _response(400, {"message": "image_order must be between 1 and 5"})
    except (ValueError, TypeError):
        return _response(400, {"message": "image_order must be a number"})

    # 7. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        # 8. Get customer_id from cognito_sub
        with conn.cursor() as cur:
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()

            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})

            customer_id = customer_row["customer_id"]

        # 9. Verify booking exists and belongs to customer
        if not verify_booking_ownership(conn, booking_id, customer_id):
            return _response(403, {"message": "You do not have permission to upload images to this booking"})

        # 10. Check image count limit
        current_count = get_booking_images_count(conn, booking_id)
        if current_count >= MAX_IMAGES_PER_BOOKING:
            return _response(400, {
                "message": f"Maximum {MAX_IMAGES_PER_BOOKING} images per booking already reached"
            })

        # 11. Check if image_order is available
        if not is_image_order_available(conn, booking_id, image_order):
            return _response(400, {
                "message": f"image_order {image_order} is already used for this booking"
            })

        # 12. Generate unique S3 key
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        # Sanitize file name to prevent path traversal
        safe_file_name = file_name.replace("/", "-").replace("\\", "-")
        s3_key = f"booking-images/{booking_id}/{timestamp}-{safe_file_name}"

        # 13. Generate presigned POST URL
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Fields={
                "Content-Type": content_type
            },
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, MAX_FILE_SIZE]  # 1 byte to 5MB
            ],
            ExpiresIn=300  # URL expires in 5 minutes
        )

        return _response(200, {
            "message": "Presigned URL generated successfully",
            "upload_url": presigned_post["url"],
            "fields": presigned_post["fields"],
            "image_key": s3_key,
            "expires_in": 300
        })

    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return _response(500, {"message": "Failed to generate upload URL"})

    except Exception as e:
        print(f"Unexpected error: {e}")
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
            "file_name": "kitchen_photo.jpg",
            "content_type": "image/jpeg",
            "image_order": 1
        })
    }

    print("🔍 Running local test for upload_booking_image.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
