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
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"  # Enable CORS
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """
    Public endpoint - Check if email exists in database
    NO JWT required - this is called BEFORE user logs in
    
    Query params:
    - email: Email address to check
    
    Returns:
    - 200: Email exists
    - 404: Email not found (new user)
    """
    
    # Get email from query string
    query_params = event.get("queryStringParameters") or {}
    email = query_params.get("email")
    
    if not email:
        return _response(400, {"message": "Email parameter required"})
    
    # Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})
    
    try:
        with conn.cursor() as cur:
            sql = "SELECT customer_id FROM customers WHERE email = %s LIMIT 1"
            cur.execute(sql, (email,))
            row = cur.fetchone()
        
        if row:
            # Email exists
            return _response(200, {"exists": True, "message": "User found"})
        else:
            # Email doesn't exist - new user
            return _response(404, {"exists": False, "message": "User not found"})
    
    except Exception as e:
        print(f"Error checking email: {e}")
        return _response(500, {"message": "Internal server error"})
    
    finally:
        try:
            conn.close()
        except Exception:
            pass


