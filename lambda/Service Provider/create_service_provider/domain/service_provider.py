from datetime import datetime
import uuid
from .enums import VerificationStatus


class ServiceProvider:
    ID_PREFIX = "SP"
    def __init__(
        self,
        name: str,
        email: str,
        address_line: str,
        city: str,
        province: str,
        postal_code: str,
        cognito_sub: str,
        bio: str = "",
        phone_number: str = "",
        business_name: str = "",
        rating: float = 0.0,
        certification_url: str | None = None,
        verification_status: VerificationStatus = VerificationStatus.PENDING,
        is_active: bool = True,
        created_at: datetime | None = None,
        provider_id: str | None = None,
        updated_at: datetime | None = None,
    ):
        # Generate unique Service Provider ID if not provided
        self.provider_id = provider_id or self._generate_provider_id()

        self.name = name
        self.email = email
        self.address_line = address_line
        self.city = city
        self.business_name = business_name
        self.phone_number = phone_number
        self.province = province
        self.postal_code = postal_code
        self.cognito_sub = cognito_sub
        self.bio = bio
        self.rating = rating
        self.certification_url = certification_url
        self.verification_status = verification_status
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @classmethod
    def _generate_provider_id(cls) -> str:
        return f"{cls.ID_PREFIX}-{uuid.uuid4()}"
