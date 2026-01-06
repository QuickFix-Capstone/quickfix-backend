import json
import sys
import os
from typing import Any, Dict

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway style response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Get all bookings for the authenticated customer.
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    
    Query Parameters:
    - status (optional): Filter by status (pending, confirmed, in_progress, completed, cancelled)
    - limit (optional): Number of results (default 20, max 100)
    - offset (optional): Pagination offset (default 0)
    
    Returns:
    - 200: List of bookings
    - 401: Unauthorized
    - 404: Customer not found
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

    # 2. Parse query parameters
    params = event.get("queryStringParameters") or {}
    status_filter = params.get("status")
    limit = min(int(params.get("limit", 20)), 100)  # Max 100
    offset = int(params.get("offset", 0))

    # 3. Validate status filter if provided
    valid_statuses = ["pending", "confirmed", "in_progress", "completed", "cancelled"]
    if status_filter and status_filter not in valid_statuses:
        return _response(400, {
            "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        })

    # 4. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 5. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]

            # 6. Build query with optional status filter
            base_query = """
                SELECT 
                    b.booking_id, b.customer_id, b.provider_id,
                    b.service_category, b.service_description,
                    b.scheduled_date, b.scheduled_time, b.status,
                    b.service_address, b.service_city, b.service_state, b.service_postal_code,
                    b.estimated_price, b.final_price, b.notes,
                    b.created_at, b.updated_at, b.completed_at,
                    sp.name AS provider_name,
                    sp.business_name AS provider_business_name,
                    sp.rating AS provider_rating
                FROM bookings b
                JOIN service_providers sp ON b.provider_id = sp.provider_id
                WHERE b.customer_id = %s
            """
            
            query_params = [customer_id]
            
            if status_filter:
                base_query += " AND b.status = %s"
                query_params.append(status_filter)
            
            base_query += " ORDER BY b.scheduled_date DESC, b.scheduled_time DESC"
            base_query += " LIMIT %s OFFSET %s"
            query_params.extend([limit, offset])
            
            cur.execute(base_query, tuple(query_params))
            rows = cur.fetchall()

            # 7. Get total count for pagination
            count_query = "SELECT COUNT(*) as total FROM bookings WHERE customer_id = %s"
            count_params = [customer_id]
            
            if status_filter:
                count_query += " AND status = %s"
                count_params.append(status_filter)
            
            cur.execute(count_query, tuple(count_params))
            total = cur.fetchone()["total"]

        # 8. Format bookings
        bookings = []
        for row in rows:
            bookings.append({
                "booking_id": row["booking_id"],
                "provider": {
                    "provider_id": row["provider_id"],
                    "name": row["provider_name"],
                    "business_name": row["provider_business_name"],
                    "rating": float(row["provider_rating"]) if row["provider_rating"] else 0.0
                },
                "service_category": row["service_category"],
                "service_description": row["service_description"],
                "scheduled_date": str(row["scheduled_date"]),
                "scheduled_time": str(row["scheduled_time"]),
                "status": row["status"],
                "location": {
                    "address": row["service_address"],
                    "city": row["service_city"],
                    "state": row["service_state"],
                    "postal_code": row["service_postal_code"]
                },
                "estimated_price": float(row["estimated_price"]) if row["estimated_price"] else None,
                "final_price": float(row["final_price"]) if row["final_price"] else None,
                "notes": row["notes"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None
            })

        return _response(200, {
            "bookings": bookings,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total
            }
        })

    except Exception as e:
        print(f"Error fetching bookings: {e}")
        return _response(500, {"message": f"Internal server error: {str(e)}"})

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
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "queryStringParameters": {
            "status": "pending",
            "limit": "10"
        }
    }

    print("🔍 Running local test for get_customer_bookings.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(result, indent=2))
