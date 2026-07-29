from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.visitor_pass import PassStatus

class GeneratePassRequest(BaseModel):
    valid_from: Optional[datetime] = Field(default=None, description="Optional override for pass valid from timestamp")
    valid_until: Optional[datetime] = Field(default=None, description="Optional override for pass valid until timestamp")
    notes: Optional[str] = Field(default=None, description="Optional notes or access instructions")
    tenant_id: Optional[int] = Field(default=None, description="Tenant organization ID (Super Admin override)")

class UpdatePassRequest(BaseModel):
    valid_from: Optional[datetime] = Field(default=None)
    valid_until: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)

class RevokePassRequest(BaseModel):
    revocation_reason: str = Field(..., min_length=1, max_length=500, description="Explicit reason for revoking the visitor pass")

class PassStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pass_id: int
    old_status: Optional[PassStatus] = None
    new_status: PassStatus
    changed_by: Optional[int] = None
    changed_at: datetime
    remarks: Optional[str] = None

class QRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pass_id: int
    tenant_id: int
    token: str
    version: int
    is_active: bool
    expires_at: datetime
    created_at: datetime
    
    # Decoded JWT Claims Breakdown
    sub: str = Field(description="Pass UUID")
    visitor_id: int
    visit_request_id: int
    token_type: str = "VISITOR_PASS"
    iss: str = "ViziCheck"
    aud: str = "GateScanner"
    iat: int
    exp: int
    qr_code_base64: Optional[str] = Field(default=None, description="Base64 encoded PNG QR code image data URI")

class PassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    tenant_id: int
    visit_request_id: int
    request_code: Optional[str] = None
    visitor_id: int
    visitor_name: Optional[str] = None
    visitor_phone: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_company: Optional[str] = None
    host_id: int
    host_name: Optional[str] = None
    host_email: Optional[str] = None
    
    pass_code: str
    status: PassStatus
    latest_qr_version: int = 1
    
    valid_from: datetime
    valid_until: datetime
    used_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    revoked_by: Optional[int] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None

    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    status_history: List[PassStatusHistoryResponse] = Field(default_factory=list)
    active_qr: Optional[QRResponse] = None

class PassPaginationRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    search: Optional[str] = Field(default=None)
    status: Optional[PassStatus] = Field(default=None)
    visitor_id: Optional[int] = Field(default=None)
    host_id: Optional[int] = Field(default=None)
    visit_request_id: Optional[int] = Field(default=None)
    tenant_id: Optional[int] = Field(default=None)
    is_deleted: bool = Field(default=False)
    sort_by: str = Field(default="created_at")
    order: str = Field(default="desc")

class PassStatisticsResponse(BaseModel):
    total_passes: int = 0
    pending_passes: int = 0
    active_passes: int = 0
    used_passes: int = 0
    completed_passes: int = 0
    expired_passes: int = 0
    revoked_passes: int = 0
    today_generated: int = 0
    today_expired: int = 0
    today_revoked: int = 0
    currently_valid: int = 0
    average_validity_duration_minutes: float = 0.0
    qr_regeneration_count: int = 0
