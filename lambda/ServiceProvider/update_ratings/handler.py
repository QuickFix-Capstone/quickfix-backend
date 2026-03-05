import json
from typing import Any, Dict

from src.db.rds_main import get_connection


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
    - Lambda invoke event: event itself is already a dict
    - Direct invocation from other Lambdas
    """
    if "body" not in event:
        # Assume direct dict for Lambda-to-Lambda invocation or local testing
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


def _update_provider_rating(conn, provider_id: str) -> Dict[str, Any]:
    """
    Calculate and update rating for a service provider.

    Args:
        conn: Database connection
        provider_id: The provider's ID (varchar)

    Returns:
        Dictionary with updated rating information
    """
    with conn.cursor() as cur:
        # Calculate aggregated rating from all reviews where provider is reviewee
        sql = """
            SELECT
                COUNT(*) as total_review_count,
                COALESCE(SUM(rating), 0) as total_rating_points
            FROM customer_provider_reviews
            WHERE reviewee_id = %s AND reviewee_type = 'provider'
        """
        cur.execute(sql, (provider_id,))
        result = cur.fetchone()

        total_count = int(result['total_review_count'])
        total_points = int(result['total_rating_points'])

        # Calculate average rating (0.00 if no reviews)
        if total_count > 0:
            average_rating = round(float(total_points) / float(total_count), 2)
        else:
            average_rating = 0.00

        # Update service_providers table
        update_sql = """
            UPDATE service_providers
            SET
                average_rating = %s,
                total_rating_points = %s,
                total_review_count = %s
            WHERE provider_id = %s
        """
        cur.execute(update_sql, (average_rating, total_points, total_count, provider_id))
        conn.commit()

        return {
            "reviewee_type": "provider",
            "reviewee_id": str(provider_id),
            "average_rating": float(average_rating),
            "total_rating_points": int(total_points),
            "total_review_count": int(total_count)
        }


def _update_customer_rating(conn, customer_id: int) -> Dict[str, Any]:
    """
    Calculate and update rating for a customer.

    Args:
        conn: Database connection
        customer_id: The customer's ID

    Returns:
        Dictionary with updated rating information
    """
    with conn.cursor() as cur:
        # Calculate aggregated rating from all reviews where customer is reviewee
        sql = """
            SELECT
                COUNT(*) as total_review_count,
                COALESCE(SUM(rating), 0) as total_rating_points
            FROM customer_provider_reviews
            WHERE reviewee_id = %s AND reviewee_type = 'customer'
        """
        cur.execute(sql, (customer_id,))
        result = cur.fetchone()

        total_count = int(result['total_review_count'])
        total_points = int(result['total_rating_points'])

        # Calculate average rating (0.00 if no reviews)
        if total_count > 0:
            average_rating = round(float(total_points) / float(total_count), 2)
        else:
            average_rating = 0.00

        # Update customers table
        update_sql = """
            UPDATE customers
            SET
                average_rating = %s,
                total_rating_points = %s,
                total_review_count = %s
            WHERE customer_id = %s
        """
        cur.execute(update_sql, (average_rating, total_points, total_count, customer_id))
        conn.commit()

        return {
            "reviewee_type": "customer",
            "reviewee_id": int(customer_id),
            "average_rating": float(average_rating),
            "total_rating_points": int(total_points),
            "total_review_count": int(total_count)
        }


def handler(event, context):
    """
    Lambda entrypoint for updating provider or customer ratings.

    This function recalculates and updates the aggregated rating for a provider
    or customer based on all reviews they have received.

    Expected JSON input (in event["body"] when via API Gateway, or direct dict):
    {
      "reviewee_id": "abc123",  // string for provider, integer for customer
      "reviewee_type": "provider"  // or "customer"
    }

    Note: reviewee_id can be string (for providers) or integer (for customers)

    Returns:
        200: Rating updated successfully
        400: Invalid input data
        404: Provider/customer not found (update affected 0 rows)
        500: Internal server error

    Response format:
    {
        "message": "Rating updated successfully",
        "rating_info": {
            "reviewee_type": "provider",
            "reviewee_id": "abc123",  // string for provider
            "average_rating": 4.75,
            "total_rating_points": 19,
            "total_review_count": 4
        }
    }
    """
    # 1) Parse and validate input
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 2) Validate required fields
    if "reviewee_id" not in data:
        return _response(400, {"message": "Missing required field: reviewee_id"})

    if "reviewee_type" not in data:
        return _response(400, {"message": "Missing required field: reviewee_type"})

    reviewee_id = data["reviewee_id"]
    reviewee_type = data["reviewee_type"]

    # Validate reviewee_type
    if reviewee_type not in ["customer", "provider"]:
        return _response(400, {"message": "reviewee_type must be 'customer' or 'provider'"})

    # Validate reviewee_id based on type
    if reviewee_type == "customer":
        # customer_id is BIGINT (integer)
        try:
            reviewee_id = int(reviewee_id)
            if reviewee_id <= 0:
                return _response(400, {"message": "customer_id must be a positive integer"})
        except (ValueError, TypeError):
            return _response(400, {"message": "customer_id must be a valid integer"})
    else:  # provider
        # provider_id is VARCHAR (string)
        reviewee_id = str(reviewee_id).strip()
        if not reviewee_id:
            return _response(400, {"message": "provider_id cannot be empty"})

    # 3) Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        # 4) Update rating based on reviewee_type
        if reviewee_type == "provider":
            rating_info = _update_provider_rating(conn, reviewee_id)
        else:  # customer
            rating_info = _update_customer_rating(conn, reviewee_id)

        # 5) Build success response
        return _response(
            200,
            {
                "message": "Rating updated successfully",
                "rating_info": rating_info
            }
        )

    except Exception as e:
        # Rollback on error
        try:
            conn.rollback()
        except Exception:
            pass

        # Generic unexpected error
        print(f"Unexpected error in update_ratings: {e}")
        return _response(
            500,
            {"message": "Internal server error while updating rating"}
        )

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Optional: local test helper
if __name__ == "__main__":
    # Test scenario 1: Update provider rating
    print("=" * 60)
    print("Test 1: Update provider rating")
    print("=" * 60)
    test_event_provider = {
        "reviewee_id": "google-oauth2|103949366066974158596",  # Example Cognito sub
        "reviewee_type": "provider"
    }

    result = handler(test_event_provider, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
    print(f"Status Code: {result['statusCode']}")

    # Test scenario 2: Update customer rating
    print("\n" + "=" * 60)
    print("Test 2: Update customer rating")
    print("=" * 60)
    test_event_customer = {
        "reviewee_id": 1,
        "reviewee_type": "customer"
    }

    result = handler(test_event_customer, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
    print(f"Status Code: {result['statusCode']}")

    # Test scenario 3: Invalid reviewee_type
    print("\n" + "=" * 60)
    print("Test 3: Invalid reviewee_type")
    print("=" * 60)
    test_event_invalid = {
        "reviewee_id": 1,
        "reviewee_type": "invalid"
    }

    result = handler(test_event_invalid, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
    print(f"Status Code: {result['statusCode']}")
