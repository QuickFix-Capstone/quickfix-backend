import json
import os
import sys
import boto3
from typing import Any, Dict
from botocore.exceptions import ClientError

try:
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        get_booking_image_by_id,
        delete_booking_image,
        verify_booking_access
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.db.booking_images import (
        get_booking_image_by_id,
        delete_booking_image,
        verify_booking_access
    )

# Initialize S3 client
s3_client = boto3.client('s3')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'quickfix-app-files')


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "DELETE,OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Delete a booking image from S3 and database.

    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims

    Path Parameters:
    - booking_id: ID of the booking
    - image_id: ID of the image to delete

    Returns:
    - 200: Image deleted successfully
    - 401: Unauthorized
    - 403: Forbidden (not booking owner/provider)
    - 404: Booking or image not found
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

    # 2. Get booking_id and image_id from path parameters
    try:
        booking_id = event["pathParameters"]["booking_id"]
        booking_id = int(booking_id)
        image_id = event["pathParameters"]["image_id"]
        image_id = int(image_id)
    except (KeyError, ValueError, TypeError):
        return _response(400, {"message": "Invalid or missing booking_id or image_id"})

    # 3. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        # 4. Get customer_id or provider_id from cognito_sub
        with conn.cursor() as cur:
            # Try customer first
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()

            customer_id = None
            provider_id = None

            if customer_row:
                customer_id = customer_row["customer_id"]
            else:
                # Try provider (if table exists)
                try:
                    cur.execute(
                        "SELECT provider_id FROM providers WHERE cognito_sub = %s",
                        (cognito_sub,)
                    )
                    provider_row = cur.fetchone()
                    if provider_row:
                        provider_id = provider_row["provider_id"]
                    else:
                        return _response(404, {"message": "User profile not found"})
                except Exception as e:
                    # Providers table might not exist yet
                    return _response(404, {"message": "User profile not found"})

        # 5. Get the image record
        image_record = get_booking_image_by_id(conn, image_id)
        if not image_record:
            return _response(404, {"message": "Image not found"})

        # 6. Verify the image belongs to this booking
        if image_record['booking_id'] != booking_id:
            return _response(404, {"message": "Image not found for this booking"})

        # 7. Verify user has access to the booking
        has_access = verify_booking_access(
            conn,
            booking_id,
            customer_id=customer_id,
            provider_id=provider_id
        )
        if not has_access:
            return _response(403, {
                "message": "You do not have permission to delete images from this booking"
            })

        # 8. Delete from S3
        s3_key = image_record['image_key']
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
            print(f"Deleted S3 object: {s3_key}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            # If object doesn't exist in S3, continue with DB deletion
            if error_code != 'NoSuchKey':
                print(f"Error deleting from S3: {e}")
                return _response(500, {"message": "Failed to delete image from storage"})

        # 9. Delete from database
        result = delete_booking_image(conn, image_id)
        if not result.get('success'):
            print(f"Error deleting from database: {result.get('error')}")
            return _response(500, {"message": "Failed to delete image from database"})

        return _response(200, {
            "message": "Image deleted successfully",
            "image_id": image_id,
            "booking_id": booking_id
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
            "booking_id": "1",
            "image_id": "1"
        }
    }

    print("🔍 Running local test for delete_booking_image.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
