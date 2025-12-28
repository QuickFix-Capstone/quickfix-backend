from datetime import datetime
from typing import List
from .enums import ServiceCategory, PricingType


class ServiceOffering:
    ID_PREFIX = "SO"

    def __init__(
        self,
        provider_id: str,
        title: str,
        description: str,
        category: ServiceCategory,
        price: float,
        pricing_type: PricingType,
        main_image_url: str | None = None,
        image_urls: List[str] | None = None,
        rating: float = 0.0,
        is_active: bool = True,
        created_at: datetime | None = None,
        service_offering_id: str | None = None,
    ):
        self.service_offering_id = (
            service_offering_id or self._generate_service_offering_id()
        )
        self.provider_id = provider_id
        self.title = title
        self.description = description
        self.category = category
        self.price = price
        self.pricing_type = pricing_type

        # Image references (S3 URLs or keys)
        self.main_image_url = main_image_url
        self.image_urls = image_urls or []

        self.rating = rating
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def _generate_service_offering_id(cls) -> str:
        import uuid
        return f"{cls.ID_PREFIX}-{uuid.uuid4()}"
