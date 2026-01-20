import json
import os
import sys
from typing import Dict, Any

# ==============================
# DB Import
# ==============================
try:
    from shared.db import get_connection
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from shared.db import get_connection


# ==============================
# API Response Helper
# ==============================
def _response(status_code: int, body: Dict[str, Any]):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body),
    }


# ==============================
# Lambda Handler
# ==============================
def lambda_handler(event, context):
    try:
        # ==============================
        # 🔐 Extract Cognito Sub
        # ==============================
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
        )

        cognito_sub = claims.get("sub")

        if not cognito_sub:
            return _response(401, {"error": "Unauthorized"})

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # ==============================
        # 🔎 Get Provider ID
        # ==============================
        cursor.execute(
            """
            SELECT provider_id
            FROM service_providers
            WHERE cognito_sub = %s
            """,
            (cognito_sub,),
        )

        provider = cursor.fetchone()
        if not provider:
            return _response(404, {"error": "Service provider not found"})

        provider_id = provider["provider_id"]

        # ==============================
        # 📦 Fetch Applications
        # ==============================
        cursor.execute(
            """
            SELECT
                ja.application_id,
                ja.job_id,
                ja.message,
                ja.proposed_price,
                ja.status AS application_status,
                ja.created_at,

                j.title,
                j.category,
                j.location_city,
                j.location_state,
                j.budget_min,
                j.budget_max,
                j.status AS job_status

            FROM job_application ja
            JOIN jobs j ON ja.job_id = j.job_id
            WHERE ja.provider_id = %s
            ORDER BY ja.created_at DESC
            """,
            (provider_id,),
        )

        applications = cursor.fetchall()

        return _response(200, {
            "provider_id": provider_id,
            "count": len(applications),
            "applications": applications
        })

    except Exception as e:
        print("❌ ERROR:", str(e))
        return _response(500, {"error": "Internal server error"})
