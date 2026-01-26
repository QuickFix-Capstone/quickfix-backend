import json
import os
import sys
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        verify_booking_ownership,
        create_booking_image,
        verify_s3_object_exists,
        get_booking_images_count,
        is_image_order_available
    )
    from src.s3.s3_client import s3 as s3_client, BUCKET as S3_BUCKET
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        verify_booking_ownership,
        create_booking_image,
        verify_s3_object_exists,
        get_booking_images_count,
        is_image_order_available
    )
    from src.s3.s3_client import s3 as s3_client, BUCKET as S3_BUCKET

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
    Save booking image metadata to database after S3 upload.

    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims

    Path Parameters:
    - booking_id: ID of the booking

    Expected JSON input (in event["body"]):
    {
      "image_key": "booking-images/123/20260126-143022-photo.jpg",
      "image_order": 1,
      "content_type": "image/jpeg",
      "file_size": 1048576,
      "description": "Leaking pipe"  # optional
    }

    Returns:
    - 201: Image metadata saved successfully
    - 400: Invalid input / S3 object not found / Max images exceeded
    - 401: Unauthorized
    - 403: Forbidden (not booking owner)
    - 404: Booking or customer not found
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
    required_fields = ["image_key", "image_order", "content_type", "file_size"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return _response(400, {
            "message": "Missing required fields",
            "missing": missing
        })

    image_key = data["image_key"]
    image_order = data["image_order"]
    content_type = data["content_type"]
    file_size = data["file_size"]
    description = data.get("description")

    # 5. Validate image_order (1-5)
    try:
        image_order = int(image_order)
        if image_order < 1 or image_order > 5:
            return _response(400, {"message": "image_order must be between 1 and 5"})
    except (ValueError, TypeError):
        return _response(400, {"message": "image_order must be a number"})

    # 6. Validate file_size
    try:
        file_size = int(file_size)
        if file_size < 1:
            return _response(400, {"message": "file_size must be positive"})
    except (ValueError, TypeError):
        return _response(400, {"message": "file_size must be a number"})

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
            return _response(403, {"message": "You do not have permission to add images to this booking"})

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

        # 12. Verify S3 object exists
        bucket = S3_BUCKET or os.environ.get('S3_BUCKET', 'quickfix-app-files')
        if not verify_s3_object_exists(s3_client, bucket, image_key):
            return _response(400, {
                "message": "Image file not found in S3. Please upload the file first."
            })

        # 13. Create image record
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

        # 14. Fetch the created image record
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT image_id, booking_id, image_key, image_order, content_type,
                       file_size, description, uploaded_by_id, created_at, updated_at
                FROM booking_images
                WHERE image_id = %s
                """,
                (result["image_id"],)
            )
            image_row = cur.fetchone()

        image_data = {
            "image_id": image_row["image_id"],
            "booking_id": image_row["booking_id"],
            "image_key": image_row["image_key"],
            "image_order": image_row["image_order"],
            "content_type": image_row["content_type"],
            "file_size": image_row["file_size"],
            "description": image_row["description"],
            "uploaded_by_id": image_row["uploaded_by_id"],
            "created_at": image_row["created_at"].isoformat() if image_row["created_at"] else None,
            "updated_at": image_row["updated_at"].isoformat() if image_row["updated_at"] else None
        }

        return _response(201, {
            "message": "Image metadata saved successfully",
            "image": image_data
        })

    except Exception as e:
        print(f"Error saving image metadata: {e}")
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
            "image_key": "booking-images/1/20260126-143022-test.jpg",
            "image_order": 1,
            "content_type": "image/jpeg",
            "file_size": 1048576,
            "description": "Test image"
        })
    }

    print("🔍 Running local test for create_booking_image.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
