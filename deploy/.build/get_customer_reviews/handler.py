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
    """Parse query string parameters from API Gateway event."""
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
    """Get SQL ORDER BY clause based on sort option."""
    sort_map = {
        "newest": "r.created_at DESC",
        "oldest": "r.created_at ASC",
        "highest_rating": "r.rating DESC, r.created_at DESC",
        "lowest_rating": "r.rating ASC, r.created_at DESC"
    }
    
    return sort_map.get(sort_option, "r.created_at DESC")


def handler(event, context):
    """
    Lambda entrypoint for getting all reviews for a customer.
    
    Path Parameters:
        customer_id: The customer's ID (from URL path)
    
    Query Parameters:
        sort: Sort order - 'newest' (default), 'oldest', 'highest_rating', 'lowest_rating'
        limit: Number of results per page (default: 10, max: 100)
        offset: Pagination offset (default: 0)
    
    Example URLs:
        GET /reviews/customer/1
        GET /reviews/customer/2?sort=highest_rating&limit=20&offset=0
    
    Returns:
        200: Reviews retrieved successfully
        400: Invalid parameters
        404: Customer not found
        500: Internal server error
    """
    # 1) Extract customer_id from path parameters
    path_params = event.get("pathParameters") or {}
    customer_id = path_params.get("customer_id")
    
    # For local testing, allow customer_id in event root
    if not customer_id:
        customer_id = event.get("customer_id")
    
    if not customer_id:
        return _response(400, {"message": "Missing required path parameter: customer_id"})
    
    # Validate customer_id is an integer
    try:
        customer_id = int(customer_id)
    except (ValueError, TypeError):
        return _response(400, {"message": "customer_id must be a valid integer"})
    
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
            # 5) Get total count of reviews for this customer
            count_sql = """
                SELECT COUNT(*) as total_count
                FROM reviews
                WHERE reviewee_id = %s AND reviewee_type = 'customer'
            """
            cur.execute(count_sql, (customer_id,))
            count_result = cur.fetchone()
            total_count = int(count_result['total_count']) if count_result else 0
            
            # 6) Get customer's rating summary
            summary_sql = """
                SELECT 
                    average_rating,
                    total_review_count,
                    first_name,
                    last_name
                FROM customers
                WHERE customer_id = %s
            """
            cur.execute(summary_sql, (customer_id,))
            summary_result = cur.fetchone()
            
            if not summary_result:
                return _response(404, {"message": "Customer not found"})
            
            average_rating = float(summary_result['average_rating']) if summary_result['average_rating'] else 0.0
            
            # 7) Get reviews with reviewer information
            sort_clause = _get_sort_clause(sort_option)
            
            reviews_sql = f"""
                SELECT 
                    r.review_id,
                    r.job_id,
                    r.reviewer_id,
                    r.reviewer_type,
                    r.rating,
                    r.comment,
                    r.created_at,
                    CASE 
                        WHEN r.reviewer_type = 'customer' THEN CONCAT(c.first_name, ' ', c.last_name)
                        WHEN r.reviewer_type = 'provider' THEN sp.business_name
                    END as reviewer_name
                FROM reviews r
                LEFT JOIN customers c ON r.reviewer_id = c.customer_id AND r.reviewer_type = 'customer'
                LEFT JOIN service_providers sp ON r.reviewer_id = sp.provider_id AND r.reviewer_type = 'provider'
                WHERE r.reviewee_id = %s AND r.reviewee_type = 'customer'
                ORDER BY {sort_clause}
                LIMIT %s OFFSET %s
            """
            
            cur.execute(reviews_sql, (customer_id, limit, offset))
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
                    "summary": {
                        "customer_name": f"{summary_result['first_name']} {summary_result['last_name']}",
                        "average_rating": average_rating,
                        "total_reviews": total_count
                    }
                }
            )
    
    except Exception as e:
        print(f"Error in get_customer_reviews: {e}")
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
    print("Testing GET /reviews/customer/{customer_id}")
    print("=" * 70)
    
    # Test 1: Get reviews for Customer 2 (KunPeng Yang - best rating)
    print("\n📋 Test 1: Get reviews for Customer 2 (default params)")
    print("-" * 70)
    test_event_1 = {
        "customer_id": 2,
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 2: Get reviews sorted by highest rating
    print("\n📋 Test 2: Get reviews for Customer 1 (sorted by highest rating)")
    print("-" * 70)
    test_event_2 = {
        "customer_id": 1,
        "sort": "highest_rating",
        "limit": 5,
        "offset": 0
    }
    
    result = handler(test_event_2, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    # Test 3: Invalid customer_id
    print("\n📋 Test 3: Invalid customer_id (should return 404)")
    print("-" * 70)
    test_event_3 = {
        "customer_id": 9999,
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_3, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Local testing complete!")
    print("=" * 70)
