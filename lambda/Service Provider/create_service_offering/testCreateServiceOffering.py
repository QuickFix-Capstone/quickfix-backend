
# """
# Integration test for creating a Service Offering
# """

# from domain.service_offering import ServiceOffering
# from domain.enums import ServiceCategory, PricingType
# from infrastructure.service_offering_repo import ServiceOfferingRepository

# def main():
#     print("=== STARTING SERVICE OFFERING INTEGRATION TEST ===")

#     provider_id = "SP-29438f93-01d0-4ef1-913c-9c2b7e9e315b"

#     # 1️⃣ Create domain object
#     offering = ServiceOffering(
#         provider_id=provider_id,
#         title="Emergency Plumbing Repair",
#         description="24/7 emergency plumbing services for leaks and pipe bursts",
#         category=ServiceCategory.PLUMBING,
#         price=120.00,
#         pricing_type=PricingType.HOURLY,
#         main_image_url="https://example-bucket.s3.amazonaws.com/plumbing.jpg",
#     )

#     print("Created ServiceOffering object")
#     print("Service Offering ID:", offering.service_offering_id)
#     print("Provider ID:", offering.provider_id)

#     # 2️⃣ Persist using repository
#     repo = ServiceOfferingRepository()
#     repo.create(offering)

#     print("Inserted ServiceOffering into database")

#     print("=== TEST PASSED SUCCESSFULLY ===")


# if __name__ == "__main__":
#     main()

import json
from handler import lambda_handler

event = {
    "provider_id": "SP-29438f93-01d0-4ef1-913c-9c2b7e9e315b",
    "body": json.dumps({
        "title": "Emergency Plumbing Repair",
        "description": "24/7 emergency plumbing services",
        "category": "PLUMBING",
        "price": 120,
        "pricing_type": "HOURLY"
    })
}

response = lambda_handler(event, None)
print(response)
