import json
import os
import boto3
from datetime import datetime
from typing import Any, Dict
from botocore.exceptions import ClientError

# Initialize S3 client
s3_client = boto3.client('s3')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET', 'quickfix-app-files')
ALLOWED_CONTENT_TYPES = [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/gif',
    'image/webp'
]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # Configure based on your frontend domain
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
    Generate presigned S3 URL for customer avatar upload.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Expected JSON input (in event["body"]):
    {
      "file_name": "profile.jpg",
      "content_type": "image/jpeg"
    }
    
    Returns:
    - 200: Presigned URL generated successfully
    - 400: Invalid input
    - 401: Unauthorized
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

    # 2. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 3. Validate required fields
    file_name = data.get("file_name")
    content_type = data.get("content_type")

    if not file_name:
        return _response(400, {"message": "Missing required field: file_name"})
    
    if not content_type:
        return _response(400, {"message": "Missing required field: content_type"})

    # 4. Validate content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        return _response(400, {
            "message": f"Invalid content type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        })

    # 5. Generate unique S3 key
    # Each customer gets their own folder: customers-avatar/{cognito_sub}/
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    # Sanitize file name to prevent path traversal
    safe_file_name = file_name.replace("/", "-").replace("\\", "-")
    s3_key = f"customers-avatar/{cognito_sub}/{timestamp}-{safe_file_name}"

    # 6. Generate presigned POST URL with public-read ACL
    try:
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Fields={
                "Content-Type": content_type,
                "acl": "public-read"  # Make uploaded images publicly readable
            },
            Conditions=[
                {"Content-Type": content_type},
                {"acl": "public-read"},  # Allow public-read ACL
                ["content-length-range", 1, MAX_FILE_SIZE]  # 1 byte to 5MB
            ],
            ExpiresIn=300  # URL expires in 5 minutes
        )

        # 7. Construct the final avatar URL
        avatar_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"

        return _response(200, {
            "message": "Presigned URL generated successfully",
            "upload_url": presigned_post["url"],
            "fields": presigned_post["fields"],
            "avatar_url": avatar_url,
            "expires_in": 300
        })

    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return _response(500, {
            "message": "Failed to generate upload URL"
        })

    except Exception as e:
        print(f"Unexpected error: {e}")
        return _response(500, {
            "message": "Internal server error"
        })


# Local testing
if __name__ == "__main__":
    # Test event with mock JWT claims
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "test-cognito-sub-123"
                    }
                }
            }
        },
        "body": json.dumps({
            "file_name": "profile.jpg",
            "content_type": "image/jpeg"
        })
    }

    print("🔍 Running local test for upload_avatar.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
