from domain.service_provider import ServiceProvider
from domain.enums import VerificationStatus, ServiceCategory,PricingType


# # def main():
# #     provider = ServiceProvider(
# #         name="AJ Smith",
# #         email="john.smith@email.com",
# #         address_line="123 King St",
# #         city="Toronto",
# #         province="ON",
# #         postal_code="M5V 1A1",
# #         bio="Licensed plumber with 10 years experience",
# #     )

# #     print("=== Service Provider Test ===")
# #     print("Provider ID:", provider.provider_id)
# #     print("Name:", provider.name)
# #     print("Email:", provider.email)
# #     print("City:", provider.city)
# #     print("Verification Status:", provider.verification_status)
# #     print("Is Active:", provider.is_active)
# #     print("Created At:", provider.created_at)

#     # # Simple assertions (manual sanity checks)
#     # assert provider.provider_id.startswith("SP-")
#     # assert provider.verification_status == VerificationStatus.PENDING
#     # assert provider.is_active is True

#     print("\n✅ ServiceProvider test passed successfully!")


# if __name__ == "__main__":
#     main()


"""
Integration test:
- Domain
- Repository
- Database
"""

from domain.service_provider import ServiceProvider
from infrastructure.repository.service_provider_repo import ServiceProviderRepository

def main():
    print("=== STARTING SERVICE PROVIDER INTEGRATION TEST ===")

    # 1️⃣ Create domain object
    provider = ServiceProvider(
        name="TEST Provider",
        email="test.provider@example.com",
        address_line="123 Test St",
        city="Toronto",
        province="ON",
        postal_code="T0T 0T0",
        bio="This is a test provider inserted via integration test",
    )

    print("Created ServiceProvider object")
    print("Provider ID:", provider.provider_id)

    # 2️⃣ Persist using repository
    repo = ServiceProviderRepository()
    repo.create(provider)

    print("Inserted ServiceProvider into database")

    print("=== TEST PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
