from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")

class EnhancedPaginationResponse(BaseModel, Generic[T]):
    """
    Standardized paginated data wrapper payload.
    """
    page: int = Field(..., description="Current page index")
    page_size: int = Field(..., description="Items per page")
    total_records: int = Field(..., description="Total items matching filter")
    total_pages: int = Field(..., description="Total available pages")
    has_next: bool = Field(..., description="True if next page exists")
    has_previous: bool = Field(..., description="True if previous page exists")
    items: List[T] = Field(default_factory=list)

# Alias for backward compatibility or concise naming
PaginationResponse = EnhancedPaginationResponse

class PaginationRequest(BaseModel):
    """
    Query parameters model for filtering, searching, and paginating users.
    """
    page: int = Field(default=1, ge=1, description="Page index (1-based)")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page (max 100)")
    search: Optional[str] = Field(default=None, description="Search term for name or email")
    role_id: Optional[int] = Field(default=None, description="Filter by role ID")
    tenant_id: Optional[int] = Field(default=None, description="Filter by tenant ID")
    is_active: Optional[bool] = Field(default=None, description="Filter by active status")
    is_deleted: bool = Field(default=False, description="Include soft deleted records")
    sort_by: str = Field(default="created_at", description="Sort field (created_at, email, first_name, last_name)")
    order: str = Field(default="desc", description="Sort order (asc or desc)")

class CreateUserRequest(BaseModel):
    """
    Payload for creating a new user.
    """
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, description="Must be strong: uppercase, lowercase, digit, special char")
    phone: Optional[str] = Field(default=None, max_length=20)
    role_id: int = Field(..., description="Target Role ID")
    tenant_id: Optional[int] = Field(default=None, description="Associated Tenant ID")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

class UpdateUserRequest(BaseModel):
    """
    Payload for updating an existing user's details.
    """
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    role_id: Optional[int] = Field(default=None)
    tenant_id: Optional[int] = Field(default=None)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

class UserResponse(BaseModel):
    """
    Data Transfer Object for User information.
    """
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool
    is_deleted: bool
    role_id: int
    role_name: str
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ChangePasswordRequest(BaseModel):
    """
    Payload for authenticated user to change their password.
    """
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New strong password")

class ResetPasswordRequest(BaseModel):
    """
    Payload for administrative password reset of a user account.
    """
    new_password: str = Field(..., min_length=8, description="New strong password")

class ChangeUserStatusRequest(BaseModel):
    """
    Payload for modifying user active status.
    """
    is_active: bool = Field(..., description="Target active status")
