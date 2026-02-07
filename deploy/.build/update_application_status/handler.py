import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from src.db.rds_main import get_connection
    from src.utils.ws_notification_service import NotificationService
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.db.rds_main import get_connection
    from src.utils.ws_notification_service import NotificationService


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
        "body": json.dumps(body),
    }


def _notify_job_status_changed(
    customer_sub: str,
    provider_sub: Optional[str],
    job_id: str,
    old_status: str,
    new_status: str,
    changed_by: str,
) -> None:
    """Send websocket status update without affecting the API success path."""
    if old_status == new_status:
        return

    user_ids = [customer_sub]
    if provider_sub:
        user_ids.append(provider_sub)

    payload = {
        "type": "JOB_STATUS_CHANGED",
        "jobId": str(job_id),
        "oldStatus": old_status,
        "newStatus": new_status,
        "changedAt": datetime.now(timezone.utc).isoformat(),
        "changedBy": changed_by,
    }

    try:
        NotificationService().notify_users(user_ids, payload)
    except Exception as exc:
        print(f"Failed to send JOB_STATUS_CHANGED notification: {exc}")


def handler(event, context):
    """
    Update job application status (accept or reject).
    
    Authentication:
    - Requires JWT authorizer (Cognito)
    - cognito_sub extracted from JWT claims
    - Only the job owner (customer) can update application status
    
    Path Parameters:
    - job_id: ID of the job
    - application_id: ID of the application to update
    
    Request Body:
    - action: "accept" or "reject"
    
    Authorization:
    - Customer can only update applications for their own jobs
    
    Accept Action:
    - Updates application status to 'accepted'
    - Updates job status to 'assigned'
    - Sets job.assigned_provider_id
    - Rejects all other pending applications for this job
    - Uses transaction for atomicity
    
    Reject Action:
    - Updates application status to 'rejected'
    
    Returns:
    - 200: Application status updated successfully
    - 400: Invalid action or missing parameters
    - 401: Unauthorized
    - 403: Forbidden (not customer's job)
    - 404: Job or application not found
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
        job_id = event["pathParameters"]["job_id"]
        application_id = event["pathParameters"]["application_id"]
    except (KeyError, TypeError):
        return _response(400, {"message": "Missing job_id or application_id in path"})

    # 3. Parse request body
    try:
        data = _parse_body(event)
    except ValueError as e:
        return _response(400, {"message": str(e)})

    # 4. Validate action
    action = data.get("action")
    if action not in ["accept", "reject"]:
        return _response(400, {"message": "Invalid action. Must be 'accept' or 'reject'"})

    # 5. Connect to database
    conn = get_connection()
    if not conn:
        return _response(500, {"message": "Database connection failed"})

    try:
        with conn.cursor() as cur:
            # 6. Get customer_id from cognito_sub
            cur.execute(
                "SELECT customer_id FROM customers WHERE cognito_sub = %s",
                (cognito_sub,)
            )
            customer_row = cur.fetchone()
            
            if not customer_row:
                return _response(404, {"message": "Customer profile not found"})
            
            customer_id = customer_row["customer_id"]
            customer_sub = cognito_sub

            # 7. Verify customer owns this job
            cur.execute(
                "SELECT customer_id, status FROM jobs WHERE job_id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()
            
            if not job_row:
                return _response(404, {"message": "Job not found"})
            
            if job_row["customer_id"] != customer_id:
                return _response(403, {"message": "Forbidden: You can only manage applications for your own jobs"})
            old_job_status = job_row["status"]

            # 8. Get application details
            cur.execute(
                """
                SELECT application_id, job_id, provider_id, status 
                FROM job_applications 
                WHERE application_id = %s AND job_id = %s
                """,
                (application_id, job_id)
            )
            app_row = cur.fetchone()
            
            if not app_row:
                return _response(404, {"message": "Application not found"})

            # 9. Check if application is already processed
            if app_row["status"] != "pending":
                return _response(400, {"message": f"Application already {app_row['status']}"})

            # 10. Process action
            if action == "accept":
                # Start transaction for accept action
                conn.begin()
                
                try:
                    # Update application to accepted
                    cur.execute(
                        "UPDATE job_applications SET status = 'accepted' WHERE application_id = %s",
                        (application_id,)
                    )
                    
                    # Update job to assigned
                    cur.execute(
                        """
                        UPDATE jobs 
                        SET status = 'assigned', assigned_provider_id = %s 
                        WHERE job_id = %s
                        """,
                        (app_row["provider_id"], job_id)
                    )
                    
                    # Reject all other pending applications for this job
                    cur.execute(
                        """
                        UPDATE job_applications 
                        SET status = 'rejected' 
                        WHERE job_id = %s AND application_id != %s AND status = 'pending'
                        """,
                        (job_id, application_id)
                    )
                    
                    conn.commit()
                    
                    message = "Application accepted successfully"
                    
                except Exception as e:
                    conn.rollback()
                    print(f"Transaction failed: {e}")
                    return _response(500, {"message": "Failed to accept application"})
                    
            else:  # action == "reject"
                # Simple update for reject
                cur.execute(
                    "UPDATE job_applications SET status = 'rejected' WHERE application_id = %s",
                    (application_id,)
                )
                conn.commit()
                message = "Application rejected successfully"

            # 11. Fetch updated application
            cur.execute(
                """
                SELECT application_id, job_id, provider_id, status, created_at
                FROM job_applications
                WHERE application_id = %s
                """,
                (application_id,)
            )
            updated_app = cur.fetchone()

            # 12. Fetch updated job (if accepted)
            job_data = None
            if action == "accept":
                cur.execute(
                    """
                    SELECT job_id, status, assigned_provider_id
                    FROM jobs
                    WHERE job_id = %s
                    """,
                    (job_id,)
                )
                job_data = cur.fetchone()

                # Lookup provider Cognito sub for websocket notifications.
                provider_sub = None
                cur.execute(
                    "SELECT cognito_sub FROM service_providers WHERE provider_id = %s",
                    (app_row["provider_id"],)
                )
                provider_row = cur.fetchone()
                if provider_row:
                    provider_sub = provider_row["cognito_sub"]

                _notify_job_status_changed(
                    customer_sub=customer_sub,
                    provider_sub=provider_sub,
                    job_id=job_id,
                    old_status=old_job_status,
                    new_status=job_data["status"] if job_data else old_job_status,
                    changed_by=customer_sub,
                )

        # 13. Format response
        response_data = {
            "message": message,
            "application": {
                "application_id": updated_app["application_id"],
                "job_id": updated_app["job_id"],
                "provider_id": updated_app["provider_id"],
                "status": updated_app["status"],
                "created_at": updated_app["created_at"].isoformat() if updated_app["created_at"] else None
            }
        }

        if job_data:
            response_data["job"] = {
                "job_id": job_data["job_id"],
                "status": job_data["status"],
                "assigned_provider_id": job_data["assigned_provider_id"]
            }

        return _response(200, response_data)

    except Exception as e:
        print(f"Error updating application status: {e}")
        return _response(500, {"message": "Internal server error"})

    finally:
        try:
            conn.close()
        except Exception:
            pass


# Local testing
if __name__ == "__main__":
    # Test event - Accept application
    test_event_accept = {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "415b3510-a0a1-708e-6a02-dc457aec9ecc"
                    }
                }
            }
        },
        "pathParameters": {
            "job_id": "1",
            "application_id": "1"
        },
        "body": json.dumps({
            "action": "accept"
        })
    }

    print("🔍 Running local test for update_application_status.handler() - ACCEPT...")
    result = handler(test_event_accept, None)
    print("Response:")
    print(json.dumps(result, indent=2))
