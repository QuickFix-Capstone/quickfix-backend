import json
from typing import Any, Dict

from src.db.rds_main import get_connection
from pymysql.err import IntegrityError


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Support both:
    - API Gateway event: event["body"] is a JSON string
    - Local testing: event itself is already a dict
    """
    if "body" not in event:
        # Assume direct dict for local testing
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
            "Access-Control-Allow-Methods": "POST,OPTIONS"
        },
        "body": json.dumps(body),
    }


def _validate_review_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate review data for customer reviewing a provider.

    Returns:
        tuple: (is_valid, error_message)
    """
    # Required fields for customer_provider_reviews
    required_fields = ["job_id", "provider_id", "rating", "comment"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Validate rating range
    try:
        rating = int(data["rating"])
        if rating < 1 or rating > 5:
            return False, "rating must be between 1 and 5"
    except (ValueError, TypeError):
        return False, "rating must be an integer"

    # Validate comment length
    comment = str(data["comment"]).strip()
    if len(comment) < 10:
        return False, "comment must be at least 10 characters"
    if len(comment) > 1000:
        return False, "comment must not exceed 1000 characters"

    return True, ""


def handler(event, context):
    """
    Lambda entrypoint for creating a review BY a customer ABOUT a provider.

    This creates a record in the customer_provider_reviews table.

    Expected JSON input (in event["body"] when via API Gateway):

    {
      "job_id": 123,
      "provider_id": 5,
      "rating": 5,
      "comment": "Excellent service! Very professional and completed the job on time."
    }

    Note: customer_id is derived from JWT token (email claim mapped to customers table)

    Returns:
        201: Review created successfully
        400: Invalid input data
        401: Unauthorized (missing/invalid JWT)
        403: Customer not found for email
        404: Job not found
        409: Duplicate review (customer already reviewed this job)
        500: Internal server error
    """
    # 1) Parse and validate input
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 2) Validate review data
    is_valid, error_msg = _validate_review_data(data)
    if not is_valid:
        return _response(400, {"message": error_msg})

    # 3) Extract customer_id from JWT or local testing
    customer_id = data.get("customer_id")  # For local testing

    if not customer_id:
        # Try to get from requestContext (API Gateway JWT authorizer)
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        jwt_claims = authorizer.get("jwt", {}).get("claims", {})

        # Get email from JWT claims
        email = jwt_claims.get("email")

        if not email:
            return _response(401, {"message": "Unauthorized - missing email in JWT token"})

    # 4) Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 5) If customer_id not set (JWT flow), look up by email
            if not customer_id and 'email' in locals():
                cur.execute(
                    "SELECT customer_id FROM customers WHERE email = %s",
                    (email,)
                )
                customer_result = cur.fetchone()
                if not customer_result:
                    return _response(403, {"message": "Customer not found for this email"})
                customer_id = customer_result['customer_id']

            # 6) Check if job exists and is completed
            cur.execute(
                "SELECT status, customer_id, assigned_provider_id FROM jobs WHERE job_id = %s",
                (data["job_id"],)
            )
            job = cur.fetchone()

            if not job:
                return _response(404, {"message": "Job not found"})

            if job["status"] != "completed":
                return _response(
                    400,
                    {"message": "Job must be completed before submitting a review"}
                )

            # 7) Verify customer owns this job
            if job["customer_id"] != customer_id:
                return _response(
                    403,
                    {"message": "You can only review jobs that you created"}
                )

            # 8) Insert the review into customer_provider_reviews
            sql = """
                INSERT INTO customer_provider_reviews
                (job_id, customer_id, provider_id, rating, comment)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(
                sql,
                (
                    data["job_id"],
                    customer_id,
                    data["provider_id"],
                    data["rating"],
                    data["comment"].strip(),
                ),
            )
            conn.commit()
            review_id = cur.lastrowid

            # 9) Fetch the created review
            cur.execute(
                "SELECT * FROM customer_provider_reviews WHERE review_id = %s",
                (review_id,)
            )
            review = cur.fetchone()

        # 10) Build success response
        return _response(
            201,
            {
                "message": "Review created successfully",
                "review": {
                    "review_id": review["review_id"],
                    "job_id": review["job_id"],
                    "customer_id": review["customer_id"],
                    "provider_id": review["provider_id"],
                    "rating": review["rating"],
                    "comment": review["comment"],
                    "created_at": review["created_at"].isoformat() if review["created_at"] else None,
                },
            },
        )

    except IntegrityError as e:
        error_str = str(e)
        # Duplicate review check
        if "unique_customer_job" in error_str.lower() or "duplicate" in error_str.lower():
            return _response(
                409,
                {"message": "You have already submitted a review for this job"},
            )
        # Foreign key constraint violation
        if "foreign key" in error_str.lower():
            return _response(
                400,
                {"message": "Invalid job_id, customer_id, or provider_id"},
            )
        # Other integrity errors
        return _response(
            400,
            {"message": "Failed to create review due to data constraint"},
        )

    except Exception as e:
        # Generic unexpected error
        print("Unexpected error in create_review:", e)
        return _response(
            500,
            {"message": "Internal server error while creating review"},
        )

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Optional: local test helper
if __name__ == "__main__":
    # Simulate creating a review by customer for provider
    test_event = {
        "body": json.dumps(
            {
                "job_id": 1,
                "customer_id": 1,  # For local testing - in production this comes from JWT
                "provider_id": 1,
                "rating": 5,
                "comment": "Excellent service! Very professional and completed the job on time. Would definitely hire again.",
            }
        )
    }

    print("Running local test for create_review.handler() (customer reviews provider)...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
    print(f"Status Code: {result['statusCode']}")
