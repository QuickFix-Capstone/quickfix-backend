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
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Lambda entrypoint for retrieving a review by ID.
    
    This endpoint can be used by both customers and service providers
    to view review details.
    
    Expected input:
        - Path parameter: review_id (from API Gateway route: /review/{review_id})
    
    Returns:
        200: Review found and returned
        400: Invalid review_id format
        404: Review not found
        500: Internal server error
    
    Response format:
    {
        "review": {
            "review_id": 1,
            "job_id": 123,
            "reviewer_id": 1,
            "reviewer_type": "customer",
            "reviewee_id": 5,
            "reviewee_type": "provider",
            "rating": 5,
            "comment": "Excellent service!",
            "created_at": "2026-01-07T12:00:00",
            "updated_at": "2026-01-07T12:00:00"
        }
    }
    """
    # 1) Extract review_id from path parameters
    try:
        path_params = event.get("pathParameters", {})
        if not path_params or "review_id" not in path_params:
            return _response(400, {"message": "Missing review_id in path"})
        
        review_id = int(path_params["review_id"])
        if review_id <= 0:
            return _response(400, {"message": "review_id must be a positive integer"})
    
    except (ValueError, TypeError):
        return _response(400, {"message": "Invalid review_id format"})
    
    # 2) Connect to DB
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})
    
    try:
        with conn.cursor() as cur:
            # Fetch the review by ID
            sql = """
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
                FROM customer_provider_reviews
                WHERE review_id = %s
            """
            cur.execute(sql, (review_id,))
            review = cur.fetchone()
            
            if not review:
                return _response(404, {"message": "Review not found"})
            
            # 3) Build success response
            return _response(
                200,
                {
                    "review": {
                        "review_id": review["review_id"],
                        "job_id": review["job_id"],
                        "reviewer_id": review["reviewer_id"],
                        "reviewer_type": review["reviewer_type"],
                        "reviewee_id": review["reviewee_id"],
                        "reviewee_type": review["reviewee_type"],
                        "rating": review["rating"],
                        "comment": review["comment"],
                        "created_at": review["created_at"].isoformat() if review["created_at"] else None,
                        "updated_at": review["updated_at"].isoformat() if review["updated_at"] else None,
                    }
                },
            )
    
    except Exception as e:
        # Generic unexpected error
        print(f"Unexpected error in get_review_by_id: {e}")
        return _response(
            500,
            {"message": "Internal server error while retrieving review"},
        )
    
    finally:
        try:
            conn.close()
        except Exception:
            pass


# Optional: local test helper
if __name__ == "__main__":
    # Simulate an API Gateway event for quick local testing
    test_event = {
        "pathParameters": {
            "review_id": "1"
        }
    }
    
    print("🔍 Running local test for get_review_by_id.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
    print(f"Status Code: {result['statusCode']}")
