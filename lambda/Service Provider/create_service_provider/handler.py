import json
import boto3
import os
from domain.service_provider import ServiceProvider
from infrastructure.repository.service_provider_repo import ServiceProviderRepository

cognito = boto3.client("cognito-idp")

def lambda_handler(event, context):
    try:
        # 🔐 JWT Authorizer (HTTP API)
        authorizer = event.get("requestContext", {}).get("authorizer")

        if not authorizer or "jwt" not in authorizer:
            print("❌ Missing JWT authorizer")
            return _response(401, {"error": "Unauthorized"})

        claims = authorizer["jwt"].get("claims")

        if not claims:
            print("❌ JWT claims missing")
            return _response(401, {"error": "Unauthorized"})

        required_claims = ["cognito:username", "sub", "email"]
        missing = [c for c in required_claims if c not in claims]

        if missing:
            print("❌ Missing required claims:", missing)
            return _response(401, {"error": "Invalid token"})

        # ✅ Safe identity values
        username = claims["cognito:username"]
        cognito_sub = claims["sub"]
        email = claims["email"]

        print("✅ Authenticated user:", username)

        # 📦 Parse body
        body = json.loads(event.get("body", "{}"))

        required_fields = ["name", "address_line", "city", "province", "postal_code"]
        if not all(body.get(f) for f in required_fields):
            return _response(400, {"error": "Missing required fields"})

        # 🧠 Domain object
        provider = ServiceProvider(
            cognito_sub=cognito_sub,
            name=body["name"],
            email=email,
            address_line=body["address_line"],
            city=body["city"],
            province=body["province"],
            postal_code=body["postal_code"],
            bio=body.get("bio", ""),
            certification_url=body.get("certification_url", ""),
        )

        repo = ServiceProviderRepository()
        repo.create(provider)

        # 👤 Promote user to ServiceProvider group
        try:
            cognito.admin_add_user_to_group(
                UserPoolId=os.environ["USER_POOL_ID"],
                Username=username,
                GroupName="ServiceProvider",
            )
            print("✅ User added to ServiceProvider group")

        except Exception as e:
            print("❌ Group assignment failed:", str(e))

        return _response(201, {
            "message": "Service Provider created successfully",
            "provider_id": provider.provider_id,
        })

    except Exception as e:
        print("❌ Lambda error:", str(e))
        return _response(500, {
            "error": "Failed to create Service Provider",
            "details": str(e),
        })


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
