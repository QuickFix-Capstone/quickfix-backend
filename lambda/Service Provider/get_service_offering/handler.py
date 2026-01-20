# import json
# from infrastructure.service_offering_repo import ServiceOfferingRepository
# from infrastructure.service_provider_repo import ServiceProviderRepository
# from decimal import Decimal

# def lambda_handler(event, context):
#     try:
#         # ==============================
#         # 0️⃣ AUTH: JWT CLAIMS
#         # ==============================
#         authorizer = event.get("requestContext", {}).get("authorizer")
#         if not authorizer or "jwt" not in authorizer:
#             return response(401, {"error": "Unauthorized"})

#         claims = authorizer["jwt"].get("claims")
#         if not claims or "sub" not in claims:
#             return response(401, {"error": "Unauthorized"})

#         cognito_sub = claims["sub"]

#         # ==============================
#         # 1️⃣ GET SERVICE PROVIDER
#         # ==============================
#         provider_repo = ServiceProviderRepository()
#         provider = provider_repo.get_by_cognito_sub(cognito_sub)

#         if not provider:
#             return response(403, {"error": "Service provider profile not found"})

#         provider_id = provider.get("provider_id")
#         if not provider_id:
#             return response(500, {"error": "Provider record missing provider_id"})

#         # ==============================
#         # 2️⃣ FETCH SERVICE OFFERINGS
#         # ==============================
#         offering_repo = ServiceOfferingRepository()
#         offerings = offering_repo.get_by_provider_id(provider_id)

#         # ==============================
#         # 3️⃣ RETURN RESPONSE
#         # ==============================
#         return response(200, {
#             "count": len(offerings),
#             "items": offerings
#         })

#     except Exception as e:
#         print("ERROR:", str(e))
#         return response(500, {
#             "error": "Internal server error",
#             "details": repr(e)
#         })

# def decimal_serializer(obj):
#     if isinstance(obj, Decimal):
#         return float(obj)
#     raise TypeError

# def response(status_code: int, body):
#     return {
#         "statusCode": status_code,
#         "headers": {
#             "Content-Type": "application/json",
#             "Access-Control-Allow-Origin": "*",
#         },
#         "body": json.dumps(body, default=decimal_serializer),
#     }


import json
from decimal import Decimal
from infrastructure.service_offering_repo import ServiceOfferingRepository
from infrastructure.service_provider_repo import ServiceProviderRepository
from datetime import datetime
from decimal import Decimal


def lambda_handler(event, context):
    try:
        # ==============================
        # 0️⃣ AUTH: JWT CLAIMS
        # ==============================
        authorizer = event.get("requestContext", {}).get("authorizer")
        if not authorizer or "jwt" not in authorizer:
            return response(401, {"error": "Unauthorized"})

        claims = authorizer["jwt"].get("claims")
        if not claims or "sub" not in claims:
            return response(401, {"error": "Unauthorized"})

        cognito_sub = claims["sub"]

        # ==============================
        # 1️⃣ GET SERVICE PROVIDER
        # ==============================
        provider_repo = ServiceProviderRepository()
        provider = provider_repo.get_by_cognito_sub(cognito_sub)

        if not provider:
            return response(403, {"error": "Service provider profile not found"})

        provider_id = provider.get("provider_id")
        if not provider_id:
            return response(500, {"error": "Provider record missing provider_id"})

        # ==============================
        # 2️⃣ FETCH SERVICE OFFERINGS
        # ==============================
        offering_repo = ServiceOfferingRepository()

        # ✅ ALWAYS guarantee a list
        offerings = offering_repo.get_by_provider_id(provider_id) or []

        # ==============================
        # 3️⃣ RETURN RESPONSE
        # ==============================
        return response(200, {
            "count": len(offerings),
            "items": offerings
        })

    except Exception as e:
        print("ERROR TYPE:", type(e))
        print("ERROR MESSAGE:", repr(e))

        return response(500, {
            "error": "Internal server error",
            "details": repr(e)
        })


# ==============================
# JSON SERIALIZATION (Decimal fix)
# ==============================
def json_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, datetime):
        return obj.isoformat()  
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")



def response(status_code: int, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=json_serializer),
    }
