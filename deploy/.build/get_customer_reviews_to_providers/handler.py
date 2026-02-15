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
    Lambda entrypoint for getting all reviews CREATED BY the logged-in customer.
    
    This returns reviews where the customer is the REVIEWER (not reviewee).
    Use case: "Show me all the reviews I've written about providers"
    
    Query Parameters:
        sort: Sort order - 'newest' (default), 'oldest', 'highest_rating', 'lowest_rating'
        limit: Number of results per page (default: 10, max: 100)
        offset: Pagination offset (default: 0)
    
    Example URLs:
        GET /customer/reviews
        GET /customer/reviews?sort=highest_rating&limit=20&offset=0
    
    Returns:
        200: Reviews retrieved successfully
        400: Invalid parameters
        401: Unauthorized (missing JWT)
        500: Internal server error
    """
    # 1) Extract customer_id from JWT token
    customer_id = event.get("customer_id")  # For local testing
    
    if not customer_id:
        # Try to get from requestContext (API Gateway JWT authorizer)
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        jwt_claims = authorizer.get("jwt", {}).get("claims", {})
        
        # Get email from JWT claims
        email = jwt_claims.get("email")
        
        if not email:
            return _response(401, {"message": "Unauthorized - missing email in JWT token"})
    
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
            # 5) If customer_id not set (JWT flow), look up by email
            if not customer_id and 'email' in locals():
                cur.execute(
                    "SELECT customer_id, first_name, last_name FROM customers WHERE email = %s",
                    (email,)
                )
                customer_result = cur.fetchone()
                if not customer_result:
                    return _response(403, {"message": "Customer not found for this email"})
                customer_id = customer_result['customer_id']
                customer_name = f"{customer_result['first_name']} {customer_result['last_name']}"
            else:
                # Get customer name for local testing
                cur.execute(
                    "SELECT first_name, last_name FROM customers WHERE customer_id = %s",
                    (customer_id,)
                )
                customer_result = cur.fetchone()
                if not customer_result:
                    return _response(404, {"message": "Customer not found"})
                customer_name = f"{customer_result['first_name']} {customer_result['last_name']}"
            
            # 6) Get total count of reviews CREATED BY this customer
            count_sql = """
                SELECT COUNT(*) as total_count
                FROM customer_provider_reviews
                WHERE customer_id = %s
            """
            cur.execute(count_sql, (customer_id,))
            count_result = cur.fetchone()
            total_count = int(count_result['total_count']) if count_result else 0
            
            # 7) Get reviews with provider information (reviewee)
            sort_clause = _get_sort_clause(sort_option)
            
            reviews_sql = f"""
                SELECT 
                    r.review_id,
                    r.job_id,
                    r.provider_id,
                    r.rating,
                    r.comment,
                    r.created_at,
                    r.updated_at,
                    sp.business_name as provider_name,
                    sp.average_rating as provider_rating
                FROM customer_provider_reviews r
                LEFT JOIN service_providers sp ON CAST(r.provider_id AS CHAR) = CAST(sp.provider_id AS CHAR)
                WHERE r.customer_id = %s
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
                    "provider_id": row['provider_id'],
                    "provider_name": row['provider_name'] or "Unknown",
                    "provider_rating": float(row['provider_rating']) if row['provider_rating'] else 0.0,
                    "rating": row['rating'],
                    "comment": row['comment'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
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
                    "customer": {
                        "customer_id": customer_id,
                        "name": customer_name,
                        "total_reviews_written": total_count
                    }
                }
            )
    
    except Exception as e:
        print(f"Error in get_my_customer_reviews: {e}")
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
    print("Testing GET /customer/reviews (my reviews)")
    print("=" * 70)
    
    # Test 1: Get reviews created by customer 1
    print("\n📋 Test 1: Get reviews created by Customer 1")
    print("-" * 70)
    test_event_1 = {
        "customer_id": 1,
        "sort": "newest",
        "limit": 10,
        "offset": 0
    }
    
    result = handler(test_event_1, None)
    print(f"Status Code: {result['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(result['body']), indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Local testing complete!")
    print("=" * 70)
