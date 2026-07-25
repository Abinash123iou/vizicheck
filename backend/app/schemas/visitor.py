from datetime import date, datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.visitor import VisitorStatus, VerificationStatus, VerificationMethod

class CreateVisitorRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="Visitor's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Visitor's last name")
    phone: str = Field(..., min_length=5, max_length=20, description="Visitor's phone number")
    email: Optional[EmailStr] = Field(default=None, description="Visitor's email address")
    tenant_id: Optional[int] = Field(default=None, description="Tenant organization ID (Super Admin override)")
    gender: Optional[str] = Field(default=None, max_length=20, description="Gender identity")
    date_of_birth: Optional[date] = Field(default=None, description="Date of birth")
    profile_photo_url: Optional[str] = Field(default=None, description="URL of visitor profile photo")
    company: Optional[str] = Field(default=None, max_length=255, description="Visitor's company name")
    designation: Optional[str] = Field(default=None, max_length=255, description="Visitor's job designation")
    address: Optional[str] = Field(default=None, description="Street address")
    city: Optional[str] = Field(default=None, max_length=100, description="City")
    state: Optional[str] = Field(default=None, max_length=100, description="State/Province")
    country: Optional[str] = Field(default=None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(default=None, max_length=20, description="Postal / ZIP code")
    government_id_type: Optional[str] = Field(default=None, max_length=50, description="ID type (Passport, Driving License, etc.)")
    government_id_number: Optional[str] = Field(default=None, max_length=100, description="Government ID document number")
    government_id_front: Optional[str] = Field(default=None, description="URL/path to front of government ID")
    government_id_back: Optional[str] = Field(default=None, description="URL/path to back of government ID")
    emergency_contact_name: Optional[str] = Field(default=None, max_length=255, description="Emergency contact full name")
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20, description="Emergency contact phone number")
    notes: Optional[str] = Field(default=None, description="Additional administrative notes")

class UpdateVisitorRequest(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, min_length=5, max_length=20)
    email: Optional[EmailStr] = Field(default=None)
    tenant_id: Optional[int] = Field(default=None)
    gender: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = Field(default=None)
    profile_photo_url: Optional[str] = Field(default=None)
    company: Optional[str] = Field(default=None, max_length=255)
    designation: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    government_id_type: Optional[str] = Field(default=None, max_length=50)
    government_id_number: Optional[str] = Field(default=None, max_length=100)
    government_id_front: Optional[str] = Field(default=None)
    government_id_back: Optional[str] = Field(default=None)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)
    notes: Optional[str] = Field(default=None)

class VerifyVisitorRequest(BaseModel):
    verification_method: VerificationMethod = Field(default=VerificationMethod.MANUAL, description="Verification method applied")
    notes: Optional[str] = Field(default=None, description="Verification review notes")

class BlacklistVisitorRequest(BaseModel):
    blacklisted: bool = Field(default=True, description="True to blacklist, False to remove blacklist")
    reason: Optional[str] = Field(default=None, description="Reason for blacklisting action")

class VisitorStatusRequest(BaseModel):
    status: VisitorStatus = Field(..., description="Target status (ACTIVE, INACTIVE, BLACKLISTED, etc.)")

class VisitorPaginationRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    search: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    company: Optional[str] = Field(default=None)
    government_id_number: Optional[str] = Field(default=None)
    visitor_code: Optional[str] = Field(default=None)
    status: Optional[VisitorStatus] = Field(default=None)
    verified: Optional[bool] = Field(default=None)
    blacklisted: Optional[bool] = Field(default=None)
    tenant_id: Optional[int] = Field(default=None)
    created_from: Optional[datetime] = Field(default=None)
    created_to: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    sort_by: str = Field(default="created_at")
    order: str = Field(default="desc")

class VisitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    visitor_code: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_photo_url: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    government_id_type: Optional[str] = None
    government_id_number: Optional[str] = None
    government_id_front: Optional[str] = None
    government_id_back: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    blacklisted: bool
    blacklist_reason: Optional[str] = None
    verified: bool
    verification_status: VerificationStatus
    verification_method: Optional[VerificationMethod] = None
    verification_date: Optional[datetime] = None
    verified_by: Optional[int] = None
    status: VisitorStatus
    notes: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_deleted: bool

class VisitorActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    action: str
    module: str
    entity_id: Optional[int] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

class VisitorStatisticsResponse(BaseModel):
    total_visitors: int
    active_visitors: int
    inactive_visitors: int
    blacklisted_visitors: int
    verified_visitors: int
    pending_verification_visitors: int
    today_visitors: int
    this_month_visitors: int
    returning_visitors: int
