from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserProfileResponse(BaseModel):
    """
    Detailed DTO for logged-in user profile with permissions list.
    """
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool
    role_id: int
    role_name: str
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UpdateProfileRequest(BaseModel):
    """
    Payload for updating logged-in user's own profile.
    """
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v
