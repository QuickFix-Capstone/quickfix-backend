import json
from domain import ServiceOffering, ServiceCategory, PricingType
from infrastructure.service_offering_repo import ServiceOfferingRepository
from infrastructure.service_provider_repo import ServiceProviderRepository


def lambda_handler(event, context):
    """
    Create Service Offering Lambda
    (Temporary version without Cognito)

    Expects:
    - provider_id (passed manually)
    - request body with service offering data
    """

    try:
        # ==============================
        # 1️⃣ IDENTIFY SERVICE PROVIDER
        # ==============================
        provider_id = event.get("provider_id")

        if not provider_id:
            return response(400, "Missing provider_id")

        provider_repo = ServiceProviderRepository()
        provider = provider_repo.get_by_provider_id(provider_id)

        if not provider:
            return response(403, "Service provider profile not found")

        # ==============================
        # 2️⃣ ENFORCE VERIFICATION
        # ==============================
        if provider["verification_status"] != "VERIFIED":
            return response(
                403,
                "Your account must be verified before creating a service offering"
            )

        # ==============================
        # 3️⃣ PARSE REQUEST BODY
        # ==============================
        body = json.loads(event.get("body", "{}"))

        required_fields = [
            "title",
            "description",
            "category",
            "price",
            "pricing_type"
        ]

        for field in required_fields:
            if field not in body:
                return response(400, f"Missing required field: {field}")

        # ==============================
        # 4️⃣ CREATE DOMAIN OBJECT
        # ==============================
        offering = ServiceOffering(
            provider_id=provider_id,
            title=body["title"],
            description=body["description"],
            category=ServiceCategory(body["category"]),
            price=float(body["price"]),
            pricing_type=PricingType(body["pricing_type"]),
            main_image_url=body.get("main_image_url"),
            is_active=True
        )

        # ==============================
        # 5️⃣ SAVE TO DATABASE
        # ==============================
        repo = ServiceOfferingRepository()
        repo.create(offering)

        return response(201, {
            "message": "Service offering created successfully",
            "service_offering_id": offering.service_offering_id
        })

    except ValueError as e:
        # Enum conversion or casting errors
        return response(400, str(e))

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, "Internal server error")


# ==============================
# 🔧 RESPONSE HELPER
# ==============================
def response(status_code: int, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
