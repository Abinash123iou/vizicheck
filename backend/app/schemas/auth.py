from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")

class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Standard unified API response structure.
    """
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[List[Any]] = None

class RefreshTokenRequest(BaseModel):
    """
    Payload for refreshing access and refresh tokens.
    """
    refresh_token: str = Field(..., description="Valid refresh token")

class UserProfileResponse(BaseModel):
    """
    User details DTO returned upon authentication or /me query.
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

    model_config = ConfigDict(from_attributes=True)
