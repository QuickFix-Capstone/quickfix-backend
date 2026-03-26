import json
import os
import sys
import traceback
from typing import Any, Dict, Optional

import pymysql
import pymysql.cursors


ACCEPTABLE_STATES = {"pending_confirmation", "pending"}
MAX_CLAIM_LENGTH = 512


def _get_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
        port=int(os.environ.get("DB_PORT", "3306")),
        connect_timeout=8,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def _get_http_method(event: Dict[str, Any]) -> str:
    return (
        event.get("requestContext", {}).get("http", {}).get("method", "")
        or event.get("httpMethod", "")
    ).upper()


def _get_booking_id(event: Dict[str, Any]) -> Optional[int]:
    path_params = event.get("pathParameters") or {}
    raw = path_params.get("booking_id") or path_params.get("bookingId") or ""
    try:
        booking_id = int(str(raw).strip())
        return booking_id if booking_id > 0 else None
    except (TypeError, ValueError):
        return None


def _get_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    if claims:
        return claims
    return event.get("requestContext", {}).get("authorizer", {}).get("claims", {}) or {}


def _get_cognito_sub(event: Dict[str, Any]) -> Optional[str]:
    cognito_sub = str(_get_claims(event).get("sub", "")).strip()
    if not cognito_sub or len(cognito_sub) > MAX_CLAIM_LENGTH:
        return None
    return cognito_sub


def _get_role(event: Dict[str, Any]) -> str:
    claims = _get_claims(event)
    groups = str(claims.get("cognito:groups", ""))
    if "Admin" in groups:
        return "admin"
    if "ServiceProvider" in groups:
        return "provider"
    return str(claims.get("custom:role", "")).strip().lower()


def _lookup_service_provider_id(conn, cognito_sub: str) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT provider_id FROM service_providers WHERE cognito_sub = %s LIMIT 1",
            (cognito_sub,),
        )
        row = cur.fetchone()
    return str(row["provider_id"]) if row and row.get("provider_id") else None


def _validate_booking(booking_id: int, provider_id: str, conn) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                booking_id,
                customer_id,
                provider_id,
                status,
                job_id,
                service_category,
                service_description,
                scheduled_date,
                scheduled_time,
                service_address,
                service_city,
                service_state,
                service_postal_code,
                service_lat,
                service_lng,
                estimated_price
            FROM bookings
            WHERE booking_id = %s
            LIMIT 1
            """,
            (booking_id,),
        )
        booking = cur.fetchone()

    if not booking:
        return {
            "valid": False,
            "status": 404,
            "error_code": "BOOKING_NOT_FOUND",
            "error": f"Booking {booking_id} not found",
        }

    if str(booking["provider_id"]) != str(provider_id):
        return {
            "valid": False,
            "status": 403,
            "error_code": "FORBIDDEN",
            "error": "You are not assigned to this booking",
        }

    if booking["status"] not in ACCEPTABLE_STATES:
        return {
            "valid": False,
            "status": 409,
            "error_code": "INVALID_STATE",
            "error": f"Cannot accept booking with status '{booking['status']}'",
        }

    if booking.get("job_id"):
        return {
            "valid": False,
            "status": 409,
            "error_code": "ALREADY_PROCESSED",
            "error": f"Booking already confirmed and linked to job {booking['job_id']}",
        }

    return {"valid": True, "booking": booking}


def _run_accept_transaction(booking_id: int, booking: Dict[str, Any], conn) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT status, job_id
            FROM bookings
            WHERE booking_id = %s
            FOR UPDATE
            """,
            (booking_id,),
        )
        locked = cur.fetchone()

        if not locked:
            raise ValueError("Booking disappeared during lock")
        if locked["status"] not in ACCEPTABLE_STATES:
            raise ValueError(f"Booking state changed to '{locked['status']}' before lock acquired")
        if locked.get("job_id"):
            raise ValueError(f"Booking already linked to job {locked['job_id']} - duplicate request")

        cur.execute(
            """
            UPDATE bookings
            SET status = 'confirmed',
                confirmed_at = NOW(),
                updated_at = NOW()
            WHERE booking_id = %s
              AND status IN ('pending_confirmation', 'pending')
              AND job_id IS NULL
            """,
            (booking_id,),
        )
        if cur.rowcount == 0:
            raise ValueError("UPDATE affected 0 rows - concurrent modification")

        job_title = f"{booking['service_category'].title()} Service"
        job_description = (
            booking["service_description"]
            or f"{booking['service_category'].title()} service requested"
        )

        cur.execute(
            """
            INSERT INTO jobs (
                customer_id,
                title,
                description,
                category,
                location_address,
                location_city,
                location_state,
                location_zip,
                location_lat,
                location_lng,
                preferred_date,
                preferred_time,
                budget_min,
                budget_max,
                status,
                assigned_provider_id,
                booking_id,
                assigned_at,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
            )
            """,
            (
                booking["customer_id"],
                job_title,
                job_description,
                booking["service_category"],
                booking["service_address"],
                booking["service_city"],
                booking["service_state"],
                booking["service_postal_code"],
                booking["service_lat"],
                booking["service_lng"],
                booking["scheduled_date"],
                booking["scheduled_time"],
                booking["estimated_price"],
                booking["estimated_price"],
                "assigned",
                booking["provider_id"],
                booking_id,
            ),
        )
        job_id = cur.lastrowid
        if not job_id:
            raise RuntimeError("Job INSERT returned no lastrowid")

        cur.execute(
            """
            UPDATE bookings
            SET job_id = %s,
                updated_at = NOW()
            WHERE booking_id = %s
            """,
            (job_id, booking_id),
        )
        if cur.rowcount == 0:
            raise RuntimeError(f"Failed to link job {job_id} back to booking {booking_id}")

    return {"job_id": job_id}


def handler(event, context):
    method = _get_http_method(event)
    if method == "OPTIONS":
        return _response(200, {"message": "OK"})
    if method and method != "POST":
        return _response(405, {"message": "Method not allowed", "error_code": "METHOD_NOT_ALLOWED"})

    cognito_sub = _get_cognito_sub(event)
    if not cognito_sub:
        return _response(401, {"message": "Unauthorized - missing or invalid token", "error_code": "UNAUTHORIZED"})

    role = _get_role(event)
    if role not in ("provider", "admin"):
        return _response(403, {"message": "Forbidden - provider role required", "error_code": "FORBIDDEN"})

    booking_id = _get_booking_id(event)
    if not booking_id:
        return _response(400, {"message": "Invalid or missing booking_id", "error_code": "INVALID_BOOKING_ID"})

    try:
        conn = _get_connection()
        provider_id = _lookup_service_provider_id(conn, cognito_sub)
        if not provider_id:
            return _response(403, {"message": "Provider profile not found for this user", "error_code": "PROVIDER_NOT_FOUND"})
    except Exception as error:
        traceback.print_exc()
        return _response(500, {"message": "Database connection failed", "error": str(error)})

    try:
        validation = _validate_booking(booking_id, provider_id, conn)
        if not validation["valid"]:
            return _response(
                validation["status"],
                {"message": validation["error"], "error_code": validation["error_code"]},
            )

        try:
            result = _run_accept_transaction(booking_id, validation["booking"], conn)
            conn.commit()
            return _response(
                200,
                {
                    "message": "Booking accepted successfully",
                    "booking_id": booking_id,
                    "job_id": result["job_id"],
                    "status": "confirmed",
                },
            )
        except ValueError as error:
            conn.rollback()
            return _response(409, {"message": str(error), "error_code": "CONFLICT"})
        except Exception as error:
            conn.rollback()
            traceback.print_exc()
            return _response(500, {"message": "Failed to accept booking", "error": str(error)})
    except Exception as error:
        traceback.print_exc()
        return _response(500, {"message": "Internal server error", "error": str(error)})
    finally:
        try:
            conn.close()
        except Exception:
            pass
