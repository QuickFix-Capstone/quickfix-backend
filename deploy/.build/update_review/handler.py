import json
from typing import Any, Dict
from datetime import datetime, timedelta

from src.db.rds_main import get_connection


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
            "Access-Control-Allow-Methods": "PUT,OPTIONS"
        },
        "body": json.dumps(body, default=str),
    }


def _validate_update_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate update data.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # At least one field must be provided
    if "rating" not in data and "comment" not in data:
        return False, "At least one field (rating or comment) must be provided"
    
    # Validate rating if provided
    if "rating" in data:
        try:
            rating = int(data["rating"])
            if rating < 1 or rating > 5:
                return False, "rating must be between 1 and 5"
        except (ValueError, TypeError):
            return False, "rating must be an integer"
    
    # Validate comment if provided
    if "comment" in data:
        comment = str(data["comment"]).strip()
        if len(comment) < 10:
            return False, "comment must be at least 10 characters"
        if len(comment) > 1000:
            return False, "comment must not exceed 1000 characters"
    
    return True, ""


def handler(event, context):
    """
    Lambda entrypoint for updating a review.
    
    Path Parameters:
        review_id: The review's ID (from URL path)
    
    Request Body (at least one field required):
    {
      "rating": 4,           // Optional - new rating (1-5)
      "comment": "Updated review text"  // Optional - new comment (10-1000 chars)
    }
    
    Returns:
        200: Review updated successfully
        400: Invalid input data
        403: Forbidden (not owner or review too old)
        404: Review not found
        500: Internal server error
    """
    # 1) Extract review_id from path parameters
    path_params = event.get("pathParameters") or {}
    review_id_str = path_params.get("review_id")
    
    # For local testing, allow review_id in event root
    if not review_id_str:
        review_id_str = event.get("review_id")
    
    if not review_id_str:
        return _response(400, {"message": "Missing required path parameter: review_id"})
    
    # Validate review_id is a positive integer
    try:
        review_id = int(review_id_str)
        if review_id <= 0:
            return _response(400, {"message": "review_id must be a positive integer"})
    except (ValueError, TypeError):
        return _response(400, {"message": "Invalid review_id format"})
    
    # 2) Parse and validate request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})
    
    is_valid, error_msg = _validate_update_data(data)
    if not is_valid:
        return _response(400, {"message": error_msg})
    
    # 3) Extract user_id for ownership verification
    # For local testing, use user_id from event
    # For production, extract from JWT token claims and map to customer_id
    user_id = event.get("user_id")
    user_type = event.get("user_type", "customer")  # Default to customer for testing
    
    if not user_id:
        # Try to get from requestContext (API Gateway JWT authorizer)
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        jwt_claims = authorizer.get("jwt", {}).get("claims", {})
        
        # Get email from JWT claims
        email = jwt_claims.get("email")
        
        if not email:
            return _response(401, {"message": "Unauthorized - missing email in JWT token"})
    
    # 4) Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})
    
    try:
        with conn.cursor() as cur:
            # 5) If user_id not set (JWT flow), look up customer_id by email
            if not user_id and 'email' in locals():
                cur.execute(
                    "SELECT customer_id FROM customers WHERE email = %s",
                    (email,)
                )
                customer_result = cur.fetchone()
                if not customer_result:
                    return _response(403, {"message": "Customer not found for this email"})
                user_id = customer_result['customer_id']
                user_type = "customer"
            
            # 6) Get existing review
            cur.execute(
                """
                SELECT 
                    review_id,
                    job_id,
                    reviewer_id,
                    reviewer_type,
                    reviewee_id,
                    reviewee_type,
                    rating,
                    comment,
                    created_at,
                    updated_at
                FROM reviews
                WHERE review_id = %s
                """,
                (review_id,)
            )
            review = cur.fetchone()
            
            if not review:
                return _response(404, {"message": "Review not found"})
            
            # 7) Verify ownership
            # Convert user_id to match reviewer_id type
            reviewer_id = review["reviewer_id"]
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                user_id_int = user_id
            
            if reviewer_id != user_id_int:
                return _response(403, {"message": "You can only update your own reviews"})
            
            # 8) Check time limit (30 days)
            created_at = review["created_at"]
            now = datetime.now()
            
            # Handle both datetime and string types
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            review_age = now - created_at
            if review_age > timedelta(days=30):
                return _response(
                    403,
                    {"message": "Cannot update reviews older than 30 days"}
                )
            
            # 9) Prepare update
            old_rating = review["rating"]
            new_rating = data.get("rating", old_rating)
            new_comment = data.get("comment", review["comment"]).strip()
            
            rating_changed = (new_rating != old_rating)
            
            # 10) Update review
            cur.execute(
                """
                UPDATE reviews
                SET rating = %s, comment = %s, updated_at = NOW()
                WHERE review_id = %s
                """,
                (new_rating, new_comment, review_id)
            )
            
            # 11) Recalculate rating if changed
            if rating_changed:
                delta = new_rating - old_rating
                reviewee_id = review["reviewee_id"]
                reviewee_type = review["reviewee_type"]
                
                if reviewee_type == "provider":
                    # Update provider rating
                    cur.execute(
                        """
                        UPDATE service_providers
                        SET 
                            total_rating_points = total_rating_points + %s,
                            average_rating = (total_rating_points + %s) / total_review_count
                        WHERE provider_id = %s
                        """,
                        (delta, delta, reviewee_id)
                    )
                else:
                    # Update customer rating
                    cur.execute(
                        """
                        UPDATE customers
                        SET 
                            total_rating_points = total_rating_points + %s,
                            average_rating = (total_rating_points + %s) / total_review_count
                        WHERE customer_id = %s
                        """,
                        (delta, delta, reviewee_id)
                    )
            
            conn.commit()
            
            # 12) Fetch updated review
            cur.execute(
                """
                SELECT 
                    review_id,
                    job_id,
                    reviewer_id,
                    reviewer_type,
                    reviewee_id,
                    reviewee_type,
                    rating,
                    comment,
                    created_at,
                    updated_at
                FROM reviews
                WHERE review_id = %s
                """,
                (review_id,)
            )
            updated_review = cur.fetchone()
            
            # 13) Build success response
            return _response(
                200,
                {
                    "message": "Review updated successfully",
                    "review": {
                        "review_id": updated_review["review_id"],
                        "job_id": updated_review["job_id"],
                        "reviewer_id": updated_review["reviewer_id"],
                        "reviewer_type": updated_review["reviewer_type"],
                        "reviewee_id": updated_review["reviewee_id"],
                        "reviewee_type": updated_review["reviewee_type"],
                        "rating": updated_review["rating"],
                        "comment": updated_review["comment"],
                        "created_at": updated_review["created_at"].isoformat() if updated_review["created_at"] else None,
                        "updated_at": updated_review["updated_at"].isoformat() if updated_review["updated_at"] else None,
                    },
                },
            )
    
    except Exception as e:
        print(f"Error in update_review: {e}")
        import traceback
        traceback.print_exc()
        return _response(
            500,
            {"message": "Internal server error while updating review"}
        )
    
    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    print("=" * 70)
    print("Testing PUT /reviews/{review_id}")
    print("=" * 70)
    
    # Test 1: Update rating only
    print("\n📋 Test 1: Update rating only (5 → 3 stars)")
    print("-" * 70)
    test_event_1 = {
        "review_id": "5",
        "user_id": 1,
        "user_type": "customer",
        "rating": 3
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 2: Update comment only
    print("\n📋 Test 2: Update comment only")
    print("-" * 70)
    test_event_2 = {
        "review_id": "5",
        "user_id": 1,
        "user_type": "customer",
        "comment": "Updated: Service was good but could be better. The plumber was professional."
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 3: Update both rating and comment
    print("\n📋 Test 3: Update both rating and comment")
    print("-" * 70)
    test_event_3 = {
        "review_id": "5",
        "user_id": 1,
        "user_type": "customer",
        "rating": 4,
        "comment": "Final update: Actually the service was quite good. Would recommend!"
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 4: Invalid rating
    print("\n📋 Test 4: Invalid rating (should return 400)")
    print("-" * 70)
    test_event_4 = {
        "review_id": "5",
        "user_id": 1,
        "rating": 6
    }
    
    result = handler(test_event_4, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 5: Non-existent review
    print("\n📋 Test 5: Non-existent review (should return 404)")
    print("-" * 70)
    test_event_5 = {
        "review_id": "99999",
        "user_id": 1,
        "rating": 4
    }
    
    result = handler(test_event_5, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Local testing complete!")
    print("=" * 70)
