from datetime import datetime

class ProviderCertification:
    """
    Domain model representing a service provider's certification
    """

    def __init__(
        self,
        certification_id: str | None = None,
        provider_id: str,
        certification_s3_key: str,
        certification_type: str | None,
        verification_status: str,
        uploaded_at: datetime,
    ):
        self.certification_id = str(uuid.uuid4())
        self.provider_id = provider_id
        self.certification_s3_key = certification_s3_key
        self.certification_type = certification_type
        self.verification_status = verification_status
        self.uploaded_at = uploaded_at
