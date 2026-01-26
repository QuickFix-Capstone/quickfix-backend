import json
import os
import sys
import boto3
from typing import Any, Dict
from botocore.exceptions import ClientError

try:
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        verify_booking_ownership,
        create_booking_image,
        is_image_order_available,
        verify_s3_object_exists
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        verify_booking_ownership,
        create_booking_image,
        is_image_order_available,
        verify_s3_object_exists
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
    Save booking image metadata to database after S3 upload.

    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims

    Path Parameters:
    - booking_id: ID of the booking

    Expected JSON input (in event["body"]):
    {
      "image_key": "booking-images/123/20260126-120000-photo.jpg",
      "image_order": 1,
      "content_type": "image/jpeg",
      "file_size": 1024000,
      "description": "Kitchen before repair"  (optional)
    }

    Returns:
    - 200: Image metadata saved successfully
    - 400: Invalid input / Image order already used / S3 object not found
    - 401: Unauthorized
    - 403: Forbidden (not booking owner)
    - 404: Customer or booking not found
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
    image_key = data.get("image_key")
    content_type = data.get("content_type")
    image_order = data.get("image_order")
    file_size = data.get("file_size")
    description = data.get("description")  # Optional

    if not image_key:
        return _response(400, {"message": "Missing required field: image_key"})

    if not content_type:
        return _response(400, {"message": "Missing required field: content_type"})

    if not image_order:
        return _response(400, {"message": "Missing required field: image_order"})

    if not file_size:
        return _response(400, {"message": "Missing required field: file_size"})

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

    # 7. Validate file_size
    try:
        file_size = int(file_size)
        if file_size <= 0:
            return _response(400, {"message": "file_size must be positive"})
    except (ValueError, TypeError):
        return _response(400, {"message": "file_size must be a number"})

    # 8. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        # 9. Get customer_id from cognito_sub
        with conn.cursor() as cur:
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()

            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})

            customer_id = customer_row["customer_id"]

        # 10. Verify booking exists and belongs to customer
        if not verify_booking_ownership(conn, booking_id, customer_id):
            return _response(403, {"message": "You do not have permission to add images to this booking"})

        # 11. Check if image_order is available
        if not is_image_order_available(conn, booking_id, image_order):
            return _response(400, {
                "message": f"image_order {image_order} is already used for this booking"
            })

        # 12. Verify S3 object exists
        if not verify_s3_object_exists(s3_client, S3_BUCKET, image_key):
            return _response(400, {
                "message": "Image not found in S3. Please upload the image first using the upload URL."
            })

        # 13. Save image metadata to database
        result = create_booking_image(
            conn=conn,
            booking_id=booking_id,
            image_key=image_key,
            image_order=image_order,
            content_type=content_type,
            file_size=file_size,
            uploaded_by_id=customer_id,
            description=description
        )

        if not result["success"]:
            return _response(500, {
                "message": "Failed to save image metadata",
                "error": result.get("error")
            })

        return _response(200, {
            "message": "Image metadata saved successfully",
            "image_id": result["image_id"],
            "booking_id": booking_id,
            "image_order": image_order
        })

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
            "booking_id": "75"
        },
        "body": json.dumps({
            "image_key": "booking-images/75/20260126-120000-kitchen.jpg",
            "image_order": 1,
            "content_type": "image/jpeg",
            "file_size": 1024000,
            "description": "Kitchen before repair"
        })
    }

    print("🔍 Running local test for create_booking_image.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
