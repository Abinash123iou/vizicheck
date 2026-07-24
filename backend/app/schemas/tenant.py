from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.tenant import TenantStatus
from app.schemas.user import EnhancedPaginationResponse

class TenantSettingsDTO(BaseModel):
    """
    Data Transfer Object for Tenant Settings configuration.
    """
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)
    currency: str = Field(default="USD", max_length=10)
    date_format: str = Field(default="YYYY-MM-DD", max_length=20)
    max_users: int = Field(default=100, ge=1)
    max_visitors: int = Field(default=1000, ge=1)
    allowed_login_methods: List[str] = Field(default_factory=lambda: ["PASSWORD"])

    model_config = ConfigDict(from_attributes=True)

class CreateTenantRequest(BaseModel):
    """
    Payload for creating a new tenant organization.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: Optional[str] = Field(default=None, max_length=100, description="URL slug (alphanumeric and hyphens)")
    domain: Optional[str] = Field(default=None, max_length=255, description="Custom domain name")
    description: Optional[str] = Field(default=None, description="Detailed organization description")
    contact_person: str = Field(..., min_length=1, max_length=255, description="Primary contact name")
    contact_email: EmailStr = Field(..., description="Primary contact email address")
    contact_phone: Optional[str] = Field(default=None, max_length=20, description="Primary contact phone number")
    settings: Optional[TenantSettingsDTO] = Field(default=None, description="Initial tenant settings")

    @field_validator("contact_email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("name", "contact_person", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("slug", mode="before")
    @classmethod
    def normalize_slug(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip():
            return v.strip().lower()
        return None

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip():
            return v.strip().lower()
        return None

class UpdateTenantRequest(BaseModel):
    """
    Payload for updating an existing tenant organization details and settings.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=100)
    domain: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    contact_person: Optional[str] = Field(default=None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    settings: Optional[TenantSettingsDTO] = Field(default=None)

    @field_validator("contact_email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("name", "contact_person", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

class TenantStatusUpdateRequest(BaseModel):
    """
    Payload for updating tenant active/suspended status.
    """
    status: TenantStatus = Field(..., description="Target status (ACTIVE, SUSPENDED, etc.)")

class TenantResponse(BaseModel):
    """
    Data Transfer Object for Tenant information.
    """
    id: int
    code: str
    name: str
    slug: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    contact_person: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    status: TenantStatus
    is_deleted: bool
    user_count: int = 0
    settings: Optional[TenantSettingsDTO] = None
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TenantPaginationRequest(BaseModel):
    """
    Query parameters model for searching, filtering, and paginating tenants.
    """
    page: int = Field(default=1, ge=1, description="Page index (1-based)")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page (max 100)")
    search: Optional[str] = Field(default=None, description="Search term for name, email, slug, domain, code")
    status: Optional[TenantStatus] = Field(default=None, description="Filter by tenant status")
    is_deleted: bool = Field(default=False, description="Include soft-deleted records")
    sort_by: str = Field(default="created_at", description="Sort field")
    order: str = Field(default="desc", description="Sort order (asc or desc)")

# Sub-DTOs for structured Statistics
class TenantOverviewStats(BaseModel):
    total: int = 0
    active: int = 0
    inactive: int = 0
    pending: int = 0
    suspended: int = 0
    archived: int = 0
    deleted: int = 0

class UserStatsSummary(BaseModel):
    total_users: int = 0
    security_officers: int = 0

class VisitorStatsSummary(BaseModel):
    total_visitors: int = 0
    today_visitors: int = 0
    check_ins: int = 0
    check_outs: int = 0

class RequestStatsSummary(BaseModel):
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0

class PassStatsSummary(BaseModel):
    passes_generated: int = 0

class TenantStatisticsResponse(BaseModel):
    """
    Aggregated dashboard metrics response DTO.
    """
    tenant_overview: TenantOverviewStats
    user_stats: UserStatsSummary
    visitor_stats: VisitorStatsSummary
    request_stats: RequestStatsSummary
    pass_stats: PassStatsSummary

class TenantActivityResponse(BaseModel):
    """
    Data Transfer Object for single activity timeline record.
    """
    id: int
    user_id: Optional[int] = None
    action: str
    module: str
    entity_id: Optional[int] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Alias for pagination response DTO
TenantPaginationResponse = EnhancedPaginationResponse[TenantResponse]
