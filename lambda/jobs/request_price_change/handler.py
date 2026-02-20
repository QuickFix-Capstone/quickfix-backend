import json
import sys
import os
from typing import Any, Dict
from decimal import Decimal

try:
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import track_provider_interaction
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.customer_public_profile import track_provider_interaction


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
    Provider requests additional budget for a job.

    Endpoint: POST /jobs/{jobId}/price-change-requests

    Authentication:
    - Requires JWT authorizer (Cognito)
    - Provider must be authenticated

    Path Parameter:
    - jobId: ID of the job

    Request Body:
    {
        "proposed_final_price": 350.00,
        "reason": "Discovered additional water damage requiring pipe replacement"
    }

    Business Rules (from Implementation Plan):
    - BR-BUD-02: Provider can request more budget ONLY when job status is 'in_progress'
    - BR-BUD-03: Each job can have ONLY ONE pending budget change request at a time

    Validation:
    1. Job exists
    2. Job is assigned to this provider (assigned_provider_id matches)
    3. Job status is 'in_progress'
    4. No existing pending request for this job
    5. proposed_final_price > 0
    6. proposed_final_price >= current final_price (if set)
    7. reason is not empty (min 10 characters)

    Returns:
    - 200: Budget change request submitted successfully
    - 400: Invalid input or business rule violation
    - 401: Unauthorized
    - 403: Forbidden (not assigned to this provider)
    - 404: Job not found
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

    # 2. Extract job_id from path parameters
    try:
        job_id = event["pathParameters"]["jobId"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing jobId in path"})

    # 3. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    if not data:
        return _response(400, {"message": "Request body cannot be empty"})

    # 4. Validate required fields
    proposed_final_price = data.get("proposed_final_price")
    reason = data.get("reason")

    if proposed_final_price is None:
        return _response(400, {"message": "proposed_final_price is required"})

    if not reason or not isinstance(reason, str):
        return _response(400, {"message": "reason is required and must be a string"})

    # 5. Validate proposed_final_price
    try:
        proposed_final_price = Decimal(str(proposed_final_price))
        if proposed_final_price <= 0:
            return _response(400, {"message": "proposed_final_price must be greater than 0"})
    except (ValueError, TypeError):
        return _response(400, {"message": "proposed_final_price must be a valid number"})

    # 6. Validate reason length
    reason = reason.strip()
    if len(reason) < 10:
        return _response(400, {"message": "reason must be at least 10 characters long"})

    # 7. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 8. Get provider_id from cognito_sub
            cur.execute(
                "SELECT provider_id FROM service_providers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            provider_row = cur.fetchone()

            if not provider_row:
                return _response(404, {"message": "Provider profile not found"})

            provider_id = provider_row["provider_id"]

            # 9. Get job details and validate
            cur.execute(
                """
                SELECT job_id, customer_id, assigned_provider_id, status, final_price
                FROM jobs
                WHERE job_id = %s
                """,
                (job_id,)
            )
            job_row = cur.fetchone()

            if not job_row:
                return _response(404, {"message": "Job not found"})

            # 10. Validate job is assigned to this provider (BR-BUD-02 implicit)
            if job_row["assigned_provider_id"] != provider_id:
                return _response(403, {"message": "Forbidden: This job is not assigned to you"})
            track_provider_interaction(
                conn=conn,
                provider_id=provider_id,
                customer_id=job_row["customer_id"],
                interaction_type="job_view",
                job_id=int(job_id),
            )

            # 11. Check for existing pending request FIRST (BR-BUD-03) - provides clearer error message
            cur.execute(
                """
                SELECT request_id
                FROM job_price_change_requests
                WHERE job_id = %s AND status = 'pending'
                """,
                (job_id,)
            )
            pending_request = cur.fetchone()

            if pending_request:
                return _response(400, {
                    "message": "A pending budget change request already exists for this job. Please wait for customer response before submitting a new request."
                })

            # 12. Validate job status is 'in_progress' (BR-BUD-02)
            if job_row["status"] != "in_progress":
                return _response(400, {
                    "message": f"Cannot request budget change. Job status must be 'in_progress' but is '{job_row['status']}'"
                })

            # 13. Validate proposed price >= current final_price (if set)
            if job_row["final_price"] is not None:
                current_final_price = Decimal(str(job_row["final_price"]))
                if proposed_final_price < current_final_price:
                    return _response(400, {
                        "message": f"proposed_final_price (${proposed_final_price}) must be greater than or equal to current final_price (${current_final_price})"
                    })

            # 14. Begin transaction - Insert price change request and update job status
            try:
                # Insert price change request
                cur.execute(
                    """
                    INSERT INTO job_price_change_requests
                    (job_id, requested_by_provider_id, proposed_final_price, reason, status)
                    VALUES (%s, %s, %s, %s, 'pending')
                    """,
                    (job_id, provider_id, proposed_final_price, reason)
                )
                request_id = cur.lastrowid

                # Update job status to 'budget_change_pending'
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'budget_change_pending'
                    WHERE job_id = %s
                    """,
                    (job_id,)
                )

                # Commit transaction
                conn.commit()

                # 15. Fetch the created request for response
                cur.execute(
                    """
                    SELECT
                        request_id,
                        job_id,
                        requested_by_provider_id,
                        proposed_final_price,
                        reason,
                        status,
                        created_at
                    FROM job_price_change_requests
                    WHERE request_id = %s
                    """,
                    (request_id,)
                )
                created_request = cur.fetchone()

                # 16. Format response
                request_data = {
                    "request_id": created_request["request_id"],
                    "job_id": created_request["job_id"],
                    "proposed_final_price": float(created_request["proposed_final_price"]),
                    "reason": created_request["reason"],
                    "status": created_request["status"],
                    "created_at": created_request["created_at"].isoformat() if created_request["created_at"] else None
                }

                return _response(200, {
                    "message": "Budget change request submitted successfully",
                    "request": request_data
                })

            except Exception as e:
                conn.rollback()
                print(f"Transaction error: {e}")
                raise

    except Exception as e:
        print(f"Error creating budget change request: {e}")
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
    # Test event with provider authentication
    test_event = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "cognito-sp-001"  # Provider: John Carter (SP-001)
                    }
                }
            }
        },
        "pathParameters": {
            "jobId": "1041"  # Job: Clogged Bathroom Drain (in_progress, final_price: $250)
        },
        "body": json.dumps({
            "proposed_final_price": 350.00,
            "reason": "Discovered additional water damage requiring pipe replacement and additional materials"
        })
    }

    print("🔍 Running local test for request_price_change.handler()...")
    result = handler(test_event, None)
    print("Response:")
    print(json.dumps(json.loads(result["body"]), indent=2))
