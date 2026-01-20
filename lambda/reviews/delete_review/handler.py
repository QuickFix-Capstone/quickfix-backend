import json
from typing import Any, Dict
from datetime import datetime, timedelta

from src.db.rds_main import get_connection


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
        "body": json.dumps(body, default=str),
    }


def handler(event, context):
    """
    Lambda entrypoint for deleting a review.
    
    Path Parameters:
        review_id: The review's ID (from URL path)
    
    Returns:
        200: Review deleted successfully
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
    
    # 2) Extract user_id for ownership verification
    # For local testing, use user_id from event
    # For production, extract from JWT token claims and map to customer_id
    user_id = event.get("user_id")
    user_type = event.get("user_type", "customer")
    
    if not user_id:
        # Try to get from requestContext (API Gateway JWT authorizer)
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        jwt_claims = authorizer.get("jwt", {}).get("claims", {})
        
        # Get email from JWT claims
        email = jwt_claims.get("email")
        
        if not email:
            return _response(401, {"message": "Unauthorized - missing email in JWT token"})
    
    # 3) Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})
    
    try:
        with conn.cursor() as cur:
            # 4) If user_id not set (JWT flow), look up customer_id by email
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
            
            # 5) Get existing review
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
                    created_at
                FROM customer_provider_reviews
                WHERE review_id = %s
                """,
                (review_id,)
            )
            review = cur.fetchone()
            
            if not review:
                return _response(404, {"message": "Review not found"})
            
            # 6) Verify ownership
            reviewer_id = review["reviewer_id"]
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                user_id_int = user_id
            
            if reviewer_id != user_id_int:
                return _response(403, {"message": "You can only delete your own reviews"})
            
            # 7) Check time limit (30 days)
            created_at = review["created_at"]
            now = datetime.now()
            
            # Handle both datetime and string types
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            review_age = now - created_at
            if review_age > timedelta(days=30):
                return _response(
                    403,
                    {"message": "Cannot delete reviews older than 30 days"}
                )
            
            # 8) Store review data for rating recalculation
            deleted_rating = review["rating"]
            reviewee_id = review["reviewee_id"]
            reviewee_type = review["reviewee_type"]
            
            # 9) Delete the review
            cur.execute(
                "DELETE FROM customer_provider_reviews WHERE review_id = %s",
                (review_id,)
            )
            
            # 10) Recalculate rating (embedded logic)
            if reviewee_type == "provider":
                # Update provider rating
                cur.execute(
                    """
                    UPDATE service_providers
                    SET 
                        total_rating_points = total_rating_points - %s,
                        total_review_count = total_review_count - 1,
                        average_rating = CASE 
                            WHEN total_review_count - 1 = 0 THEN 0.00
                            ELSE (total_rating_points - %s) / (total_review_count - 1)
                        END
                    WHERE provider_id = %s
                    """,
                    (deleted_rating, deleted_rating, reviewee_id)
                )
            else:
                # Update customer rating
                cur.execute(
                    """
                    UPDATE customers
                    SET 
                        total_rating_points = total_rating_points - %s,
                        total_review_count = total_review_count - 1,
                        average_rating = CASE 
                            WHEN total_review_count - 1 = 0 THEN 0.00
                            ELSE (total_rating_points - %s) / (total_review_count - 1)
                        END
                    WHERE customer_id = %s
                    """,
                    (deleted_rating, deleted_rating, reviewee_id)
                )
            
            conn.commit()
            
            # 11) Build success response
            return _response(
                200,
                {
                    "message": "Review deleted successfully",
                    "deleted_review": {
                        "review_id": review["review_id"],
                        "job_id": review["job_id"],
                        "rating": review["rating"],
                        "comment": review["comment"]
                    }
                }
            )
    
    except Exception as e:
        print(f"Error in delete_review: {e}")
        import traceback
        traceback.print_exc()
        return _response(
            500,
            {"message": "Internal server error while deleting review"}
        )
    
    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    print("=" * 70)
    print("Testing DELETE /reviews/{review_id}")
    print("=" * 70)
    
    # Test 1: Try to delete review
    print("\n📋 Test 1: Delete review #8 (customer_id = 1)")
    print("-" * 70)
    test_event_1 = {
        "review_id": "8",
        "user_id": 1,
        "user_type": "customer"
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 2: Try to delete non-existent review
    print("\n📋 Test 2: Delete non-existent review (should return 404)")
    print("-" * 70)
    test_event_2 = {
        "review_id": "99999",
        "user_id": 1
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 3: Try to delete someone else's review
    print("\n📋 Test 3: Delete someone else's review (should return 403)")
    print("-" * 70)
    test_event_3 = {
        "review_id": "4",
        "user_id": 999  # Different user
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Local testing complete!")
    print("=" * 70)
