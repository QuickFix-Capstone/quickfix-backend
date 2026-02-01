import json
import os
import sys
import boto3
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
    from src.db.job_images import (
        verify_job_ownership,
        get_job_images
    )
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.db.job_images import (
        verify_job_ownership,
        get_job_images
    )

# Initialize S3 client
s3_client = boto3.client('s3')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'quickfix-app-files')
PRESIGNED_URL_EXPIRATION = int(os.environ.get('PRESIGNED_URL_EXPIRATION', 3600))  # 1 hour default


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body),
    }


def generate_presigned_url(image_key: str) -> str:
    """
    Generate presigned URL for S3 object.

    Args:
        image_key: S3 object key

    Returns:
        str: Presigned URL for downloading the image
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': image_key
            },
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL for {image_key}: {e}")
        return None


def handler(event, context):
    """
    Get all job images with presigned URLs for viewing.

    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    - User must be the job owner (customer)

    Path Parameters:
    - job_id: ID of the job

    Returns:
    - 200: List of images with presigned URLs
    - 401: Unauthorized
    - 403: Forbidden (no access to job)
    - 404: Job not found or customer not found
    - 500: Server error

    Response format:
    {
      "job_id": 1041,
      "images": [
        {
          "image_id": 1,
          "image_key": "job-images/1041/...",
          "image_order": 1,
          "content_type": "image/jpeg",
          "file_size": 1024000,
          "description": "Kitchen before repair",
          "uploaded_by_id": 4,
          "created_at": "2026-02-01T10:30:00",
          "url": "https://s3.amazonaws.com/..."
        }
      ],
      "count": 1
    }
    """

    # 1. Extract Cognito JWT claims
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        cognito_sub = claims.get("sub")
    except Exception:
        return _response(401, {"message": "Unauthorized: Missing identity"})

    if not cognito_sub:
        return _response(401, {"message": "Unauthorized: Missing cognito_sub"})

    # 2. Get job_id from path parameters
    try:
        job_id = event["pathParameters"]["job_id"]
        job_id = int(job_id)
    except (KeyError, ValueError, TypeError):
        return _response(400, {"message": "Invalid or missing job_id"})

    # 3. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        # 4. Get customer_id from cognito_sub
        with conn.cursor() as cur:
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()

            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})

            customer_id = customer_row["customer_id"]

        # 5. Verify job exists and belongs to customer
        if not verify_job_ownership(conn, job_id, customer_id):
            return _response(403, {
                "message": "You do not have permission to view images for this job"
            })

        # 6. Get all images for the job
        images = get_job_images(conn, job_id)

        # 7. Generate presigned URLs for each image
        images_with_urls = []
        for image in images:
            # Convert datetime objects to ISO format strings
            image_dict = dict(image)
            if image_dict.get('created_at'):
                image_dict['created_at'] = image_dict['created_at'].isoformat()
            if image_dict.get('updated_at'):
                image_dict['updated_at'] = image_dict['updated_at'].isoformat()

            # Generate presigned URL
            presigned_url = generate_presigned_url(image_dict['image_key'])
            image_dict['url'] = presigned_url

            images_with_urls.append(image_dict)

        return _response(200, {
            "job_id": job_id,
            "images": images_with_urls,
            "count": len(images_with_urls)
        })

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
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
                        "sub": "117b75e0-f0d1-705b-736a-49b964f8b11c"  # Replace with valid customer cognito_sub
                    }
                }
            }
        },
        "pathParameters": {
            "job_id": "1041"  # Replace with valid job_id
        }
    }

    print("🔍 Running local test for get_job_images.handler()...")
    result = handler(test_event, None)
    print("\nResponse:")
    print(f"Status Code: {result['statusCode']}")
    print("\nBody:")
    body = json.loads(result["body"])
    print(json.dumps(body, indent=2))
