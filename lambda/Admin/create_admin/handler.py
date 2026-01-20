import json
import uuid
import os
from datetime import datetime

import boto3

from domain.admin import Admin
from infrastrucuture.admin_repo import AdminRepository
from shared.response import response

cognito = boto3.client("cognito-idp")

USER_POOL_ID = os.environ["USER_POOL_ID"]
ADMIN_GROUP_NAME = "Administrator"


def lambda_handler(event, context):
    try:
        # ============================
        # 🔐 AUTH – JWT Claims
        # ============================
        claims = (
            event.get("requestContext", {})
            .get("authorizer", {})
            .get("jwt", {})
            .get("claims", {})
        )

        requester_sub = claims.get("sub")
        requester_email = claims.get("email")
        requester_groups = claims.get("cognito:groups", [])

        if not requester_sub or "Administrator" not in requester_groups:
            return response(403, {"error": "Administrator access required"})

        # ============================
        # 📦 BODY
        # ============================
        body = json.loads(event.get("body") or "{}")
        target_username = body.get("username")  # Cognito username
        target_name = body.get("name")
        target_email = body.get("email")

        if not target_username or not target_email:
            return response(400, {
                "error": "username and email are required"
            })

        # ============================
        # 👤 ADD USER TO COGNITO GROUP
        # ============================
        cognito.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=target_username,
            GroupName=ADMIN_GROUP_NAME,
        )

        # ============================
        # 🧠 GET USER SUB FROM COGNITO
        # ============================
        user = cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=target_username,
        )

        cognito_sub = next(
            attr["Value"]
            for attr in user["UserAttributes"]
            if attr["Name"] == "sub"
        )

        # ============================
        # 🗄️ CREATE ADMIN RECORD
        # ============================
        repo = AdminRepository()

        existing_admin = repo.get_by_cognito_sub(cognito_sub)
        if existing_admin:
            return response(200, {
                "message": "User already an administrator",
                "admin": existing_admin,
            })

        now = datetime.utcnow()

        admin = Admin(
            admin_id=str(uuid.uuid4()),
            cognito_sub=cognito_sub,
            name=target_name or target_username,
            email=target_email,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        repo.create(admin)

        return response(201, {
            "message": "Administrator created successfully",
            "admin_id": admin.admin_id,
            "cognito_group": ADMIN_GROUP_NAME,
        })

    except cognito.exceptions.UserNotFoundException:
        return response(404, {"error": "Cognito user not found"})

    except Exception as e:
        print("❌ Create admin error:", str(e))
        return response(500, {"error": "Internal server error"})
