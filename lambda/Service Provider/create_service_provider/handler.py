import json
from domain.service_provider import ServiceProvider
from infrastructure.repository.service_provider_repo import ServiceProviderRepository


def lambda_handler(event, context):
    """
    Create Service Provider Lambda Handler
    """

    try:
        # 1️⃣ Get Cognito claims
        claims = event["requestContext"]["authorizer"]["claims"]
        cognito_sub = claims["sub"]
        email = claims["email"]

        # 2️⃣ Parse request body
        body = json.loads(event.get("body", "{}"))

        name = body.get("name")
        address_line = body.get("address_line")
        city = body.get("city")
        province = body.get("province")
        postal_code = body.get("postal_code")

        # 3️⃣ Basic validation
        if not all([name, address_line, city, province, postal_code]):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"message": "Missing required fields"}
                ),
            }

        # 4️⃣ Create domain object
        provider = ServiceProvider(
            cognito_sub=cognito_sub,
            name=name,
            email=email,
            address_line=address_line,
            city=city,
            province=province,
            postal_code=postal_code,
            bio=body.get("bio", ""),
            certification_url=body.get("certification_url", ""),
        )

        # 5️⃣ Persist via repository
        repo = ServiceProviderRepository()
        repo.create(provider)

        # 6️⃣ Success response
        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "message": "Service Provider created successfully",
                    "provider_id": provider.provider_id,
                }
            ),
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": f"Missing required field: {str(e)}"}
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "error": "Failed to create Service Provider",
                    "details": str(e),
                }
            ),
        }
