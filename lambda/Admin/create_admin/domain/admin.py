from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Admin:
    """
    Represents an Admin user persisted in the database.

    Authentication & group membership are handled by Cognito.
    This class represents application-level admin metadata.
    """

    admin_id: str
    cognito_sub: str
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
