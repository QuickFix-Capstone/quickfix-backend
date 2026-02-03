import json
import sys
import os
from typing import Any, Dict
from decimal import Decimal

try:
    from src.db.rds_main import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body from API Gateway event."""
    if "body" not in event:
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
    """Standard API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body, default=str),
    }


def handler(event, context):
    """
    Customer accepts a price change request for a job.

    Endpoint: POST /jobs/{jobId}/price-change-requests/{requestId}/accept

    Authentication:
    - Requires JWT authorizer (Cognito)
    - Customer must be authenticated

    Path Parameters:
    - jobId: ID of the job
    - requestId: ID of the price change request

    Business Rules:
    - BR-BUD-05: Only the customer who owns the job can accept/reject
    - BR-BUD-01: Upon acceptance, job.final_price is updated to proposed_final_price

    Validation:
    1. Request exists
    2. Request status is 'pending'
    3. Job exists and belongs to the authenticated customer
    4. Job status is 'budget_change_pending'

    On Success:
    - Updates request status to 'accepted' and sets responded_at timestamp
    - Updates job.final_price to proposed_final_price
    - Updates job.status back to 'in_progress'
    - All updates happen in a single transaction

    Returns:
    - 200: Price change request accepted successfully
    - 400: Invalid request or business rule violation
    - 401: Unauthorized
    - 403: Forbidden (not the job owner)
    - 404: Request or job not found
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

    # 2. Extract path parameters
    try:
        job_id = event["pathParameters"]["jobId"]
        request_id = event["pathParameters"]["requestId"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing jobId or requestId in path"})

    # 3. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 4. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()

            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})

            customer_id = customer_row["customer_id"]

            # 5. Get the price change request with job details
            cur.execute(
                """
                SELECT
                    pcr.request_id,
                    pcr.job_id,
                    pcr.requested_by_provider_id,
                    pcr.proposed_final_price,
                    pcr.reason,
                    pcr.status AS request_status,
                    pcr.created_at,
                    j.customer_id,
                    j.status AS job_status,
                    j.final_price AS current_final_price
                FROM job_price_change_requests pcr
                JOIN jobs j ON pcr.job_id = j.job_id
                WHERE pcr.request_id = %s AND pcr.job_id = %s
                """,
                (request_id, job_id)
            )
            request_row = cur.fetchone()

            if not request_row:
                return _response(404, {"message": "Price change request not found"})

            # 6. Validate customer owns the job (BR-BUD-05)
            if request_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You do not own this job"})

            # 7. Validate request is pending
            if request_row["request_status"] != "pending":
                return _response(400, {
                    "message": f"Cannot accept request. Request status is '{request_row['request_status']}', expected 'pending'"
                })

            # 8. Validate job status is budget_change_pending
            if request_row["job_status"] != "budget_change_pending":
                return _response(400, {
                    "message": f"Cannot accept request. Job status is '{request_row['job_status']}', expected 'budget_change_pending'"
                })

            # 9. Begin transaction - Update request, job price, and job status
            try:
                # Update the price change request to accepted
                cur.execute(
                    """
                    UPDATE job_price_change_requests
                    SET status = 'accepted', responded_at = NOW()
                    WHERE request_id = %s
                    """,
                    (request_id,)
                )

                # Update job final_price and status (BR-BUD-01)
                cur.execute(
                    """
                    UPDATE jobs
                    SET final_price = %s, status = 'in_progress'
                    WHERE job_id = %s
                    """,
                    (request_row["proposed_final_price"], job_id)
                )

                # Commit transaction
                conn.commit()

                # 10. Return success response
                return _response(200, {
                    "message": "Price change request accepted successfully",
                    "request": {
                        "request_id": request_row["request_id"],
                        "job_id": request_row["job_id"],
                        "proposed_final_price": float(request_row["proposed_final_price"]),
                        "previous_final_price": float(request_row["current_final_price"]) if request_row["current_final_price"] else None,
                        "reason": request_row["reason"],
                        "status": "accepted"
                    },
                    "job": {
                        "job_id": job_id,
                        "final_price": float(request_row["proposed_final_price"]),
                        "status": "in_progress"
                    }
                })

            except Exception as e:
                conn.rollback()
                print(f"Transaction error: {e}")
                raise

    except Exception as e:
        print(f"Error accepting price change request: {e}")
        import traceback
        traceback.print_exc()
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    # Test event with customer authentication
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "cognito-cust-001"  # Customer: Alice Johnson (CUST-001)
                    }
                }
            }
        },
        "pathParameters": {
            "jobId": "1041",
            "requestId": "1"  # Assuming a price change request exists for this job
        }
    }

    print("🔍 Running local test for accept_price_change.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
