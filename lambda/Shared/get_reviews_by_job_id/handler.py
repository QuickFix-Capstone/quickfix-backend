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
        "body": json.dumps(body, default=str),
    }


def _parse_query_params(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse query string parameters from API Gateway event.
    
    Supports both:
    - API Gateway event: event["queryStringParameters"]
    - Local testing: event itself contains the params
    """
    # For local testing, if no queryStringParameters, use event directly
    if "queryStringParameters" not in event:
        return {
            "sort": event.get("sort", "newest"),
            "limit": int(event.get("limit", 10)),
            "offset": int(event.get("offset", 0))
        }
    
    params = event.get("queryStringParameters") or {}
    
    return {
        "sort": params.get("sort", "newest"),
        "limit": int(params.get("limit", 10)),
        "offset": int(params.get("offset", 0))
    }


def _get_sort_clause(sort_option: str) -> str:
    """
    Get SQL ORDER BY clause based on sort option.
    
    Args:
        sort_option: One of 'newest', 'oldest', 'highest_rating', 'lowest_rating'
    
    Returns:
        SQL ORDER BY clause
    """
    sort_map = {
        "newest": "r.created_at DESC",
        "oldest": "r.created_at ASC",
        "highest_rating": "r.rating DESC, r.created_at DESC",
        "lowest_rating": "r.rating ASC, r.created_at DESC"
    }
    
    return sort_map.get(sort_option, "r.created_at DESC")


def handler(event, context):
    """
    Lambda entrypoint for getting all reviews for a specific job.
    
    This endpoint retrieves both customer and provider reviews for a job,
    showing the bidirectional feedback after job completion.
    
    Path Parameters:
        job_id: The job's ID (from URL path)
    
    Query Parameters:
        sort: Sort order - 'newest' (default), 'oldest', 'highest_rating', 'lowest_rating'
        limit: Number of results per page (default: 10, max: 100)
        offset: Pagination offset (default: 0)
    
    Example URLs:
        GET /reviews/job/1001
        GET /reviews/job/1001?sort=highest_rating&limit=20&offset=0
    
    Returns:
        200: Reviews retrieved successfully
        400: Invalid parameters
        404: Job not found
        500: Internal server error
    
    Response format:
    {
        "reviews": [
            {
                "review_id": 1,
                "job_id": 1001,
                "reviewer_id": 123,
                "reviewer_name": "John Doe",
                "reviewer_type": "customer",
                "reviewee_id": 456,
                "reviewee_name": "ABC Plumbing",
                "reviewee_type": "provider",
                "rating": 5,
                "comment": "Excellent work!",
                "created_at": "2026-01-10T14:30:00"
            }
        ],
        "pagination": {
            "limit": 10,
            "offset": 0,
            "total_count": 2,
            "has_more": false,
            "next_offset": null
        },
        "job_info": {
            "job_id": 1001,
            "title": "Fix leaking pipe"
        }
    }
    """
    # 1) Extract job_id from path parameters
    path_params = event.get("pathParameters") or {}
    job_id_str = path_params.get("job_id")
    
    # For local testing, allow job_id in event root
    if not job_id_str:
        job_id_str = event.get("job_id")
    
    if not job_id_str:
        return _response(400, {"message": "Missing required path parameter: job_id"})
    
    # Validate job_id is a positive integer
    try:
        job_id = int(job_id_str)
        if job_id <= 0:
            return _response(400, {"message": "job_id must be a positive integer"})
    except (ValueError, TypeError):
        return _response(400, {"message": "Invalid job_id format"})
    
    # 2) Parse query parameters
    try:
        params = _parse_query_params(event)
        sort_option = params["sort"]
        limit = params["limit"]
        offset = params["offset"]
    except (ValueError, TypeError) as e:
        return _response(400, {"message": f"Invalid query parameters: {str(e)}"})
    
    # 3) Validate parameters
    if sort_option not in ["newest", "oldest", "highest_rating", "lowest_rating"]:
        return _response(400, {"message": "Invalid sort option. Must be: newest, oldest, highest_rating, or lowest_rating"})
    
    if limit < 1 or limit > 100:
        return _response(400, {"message": "limit must be between 1 and 100"})
    
    if offset < 0:
        return _response(400, {"message": "offset must be >= 0"})
    
    # 4) Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})
    
    try:
        with conn.cursor() as cur:
            # 5) Verify job exists and get job info
            job_sql = """
                SELECT 
                    job_id,
                    title,
                    status
                FROM jobs
                WHERE job_id = %s
            """
            cur.execute(job_sql, (job_id,))
            job_result = cur.fetchone()
            
            if not job_result:
                return _response(404, {"message": "Job not found"})
            
            # 6) Get total count of reviews for this job
            count_sql = """
                SELECT COUNT(*) as total_count
                FROM customer_provider_reviews
                WHERE job_id = %s
            """
            cur.execute(count_sql, (job_id,))
            count_result = cur.fetchone()
            total_count = int(count_result['total_count']) if count_result else 0
            
            # 7) Get reviews with reviewer and reviewee information
            sort_clause = _get_sort_clause(sort_option)
            
            reviews_sql = f"""
                SELECT 
                    r.review_id,
                    r.job_id,
                    r.reviewer_id,
                    r.reviewer_type,
                    r.reviewee_id,
                    r.reviewee_type,
                    r.rating,
                    r.comment,
                    r.created_at,
                    CASE 
                        WHEN r.reviewer_type = 'customer' THEN CONCAT(c_reviewer.first_name, ' ', c_reviewer.last_name)
                        WHEN r.reviewer_type = 'provider' THEN sp_reviewer.business_name
                    END as reviewer_name,
                    CASE 
                        WHEN r.reviewee_type = 'customer' THEN CONCAT(c_reviewee.first_name, ' ', c_reviewee.last_name)
                        WHEN r.reviewee_type = 'provider' THEN sp_reviewee.business_name
                    END as reviewee_name
                FROM customer_provider_reviews r
                LEFT JOIN customers c_reviewer ON r.reviewer_id = c_reviewer.customer_id AND r.reviewer_type = 'customer'
                LEFT JOIN service_providers sp_reviewer ON r.reviewer_id = sp_reviewer.provider_id AND r.reviewer_type = 'provider'
                LEFT JOIN customers c_reviewee ON r.reviewee_id = c_reviewee.customer_id AND r.reviewee_type = 'customer'
                LEFT JOIN service_providers sp_reviewee ON r.reviewee_id = sp_reviewee.provider_id AND r.reviewee_type = 'provider'
                WHERE r.job_id = %s
                ORDER BY {sort_clause}
                LIMIT %s OFFSET %s
            """
            
            cur.execute(reviews_sql, (job_id, limit, offset))
            reviews_data = cur.fetchall()
            
            # 8) Format reviews
            reviews = []
            for row in reviews_data:
                reviews.append({
                    "review_id": row['review_id'],
                    "job_id": row['job_id'],
                    "reviewer_id": row['reviewer_id'],
                    "reviewer_name": row['reviewer_name'] or "Unknown",
                    "reviewer_type": row['reviewer_type'],
                    "reviewee_id": row['reviewee_id'],
                    "reviewee_name": row['reviewee_name'] or "Unknown",
                    "reviewee_type": row['reviewee_type'],
                    "rating": row['rating'],
                    "comment": row['comment'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            # 9) Build response
            has_more = (offset + limit) < total_count
            
            return _response(
                200,
                {
                    "reviews": reviews,
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "total_count": total_count,
                        "has_more": has_more,
                        "next_offset": offset + limit if has_more else None
                    },
                    "job_info": {
                        "job_id": job_result['job_id'],
                        "title": job_result['title'],
                        "status": job_result['status']
                    }
                }
            )
    
    except Exception as e:
        print(f"Error in get_job_reviews: {e}")
        import traceback
        traceback.print_exc()
        return _response(
            500,
            {"message": "Internal server error while retrieving reviews"}
        )
    
    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    print("=" * 70)
    print("Testing GET /reviews/job/{job_id}")
    print("=" * 70)
    
    # Test 1: Get reviews for a job with reviews
    print("\n📋 Test 1: Get reviews for job 1001 (default params)")
    print("-" * 70)
    test_event_1 = {
        "job_id": "1001",
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 2: Get reviews sorted by highest rating
    print("\n📋 Test 2: Get reviews for job 1001 (sorted by highest rating)")
    print("-" * 70)
    test_event_2 = {
        "job_id": "1001",
        "sort": "highest_rating",
        "limit": 5,
        "offset": 0
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 3: Test with non-existent job
    print("\n📋 Test 3: Get reviews for non-existent job 99999")
    print("-" * 70)
    test_event_3 = {
        "job_id": "99999",
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 4: Test with invalid job_id
    print("\n📋 Test 4: Get reviews with invalid job_id")
    print("-" * 70)
    test_event_4 = {
        "job_id": "invalid",
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_4, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Local testing complete!")
    print("=" * 70)
