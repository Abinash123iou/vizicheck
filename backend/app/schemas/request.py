from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.visit_request import VisitRequestStatus

class CreateVisitRequest(BaseModel):
    visitor_id: int = Field(..., description="ID of the registered visitor")
    host_id: int = Field(..., description="User ID of the employee host")
    purpose: str = Field(..., min_length=2, max_length=255, description="Purpose of the visit (e.g. Business Meeting, Maintenance)")
    department: Optional[str] = Field(default=None, max_length=100, description="Department hosting the visitor")
    scheduled_start_time: datetime = Field(..., description="Scheduled expected arrival date & time")
    scheduled_end_time: datetime = Field(..., description="Scheduled expected departure date & time")
    additional_visitors_count: int = Field(default=0, ge=0, description="Number of accompanying visitors")
    notes: Optional[str] = Field(default=None, description="Special instructions or notes")
    tenant_id: Optional[int] = Field(default=None, description="Tenant organization ID (Super Admin override)")

class UpdateVisitRequest(BaseModel):
    visitor_id: Optional[int] = Field(default=None)
    host_id: Optional[int] = Field(default=None)
    purpose: Optional[str] = Field(default=None, min_length=2, max_length=255)
    department: Optional[str] = Field(default=None, max_length=100)
    scheduled_start_time: Optional[datetime] = Field(default=None)
    scheduled_end_time: Optional[datetime] = Field(default=None)
    additional_visitors_count: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None)

class ApprovalRequest(BaseModel):
    approval_notes: Optional[str] = Field(default=None, max_length=500, description="Optional remarks or access instructions upon approval")

class RejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=1, max_length=500, description="Explicit reason for rejecting the visit request")

class CancelRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=1, max_length=500, description="Explicit reason for cancelling the visit request")

class VisitRequestPaginationRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    search: Optional[str] = Field(default=None)
    status: Optional[VisitRequestStatus] = Field(default=None)
    visitor_id: Optional[int] = Field(default=None)
    host_id: Optional[int] = Field(default=None)
    department: Optional[str] = Field(default=None)
    request_code: Optional[str] = Field(default=None)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    tenant_id: Optional[int] = Field(default=None)
    is_deleted: bool = Field(default=False)
    sort_by: str = Field(default="created_at")
    order: str = Field(default="desc")

class VisitRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    request_code: str
    visitor_id: int
    visitor_name: Optional[str] = None
    visitor_phone: Optional[str] = None
    visitor_email: Optional[str] = None
    host_id: int
    host_name: Optional[str] = None
    host_email: Optional[str] = None
    purpose: str
    department: Optional[str] = None
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    actual_checkin: Optional[datetime] = None
    actual_checkout: Optional[datetime] = None
    additional_visitors_count: int = 0
    notes: Optional[str] = None
    status: VisitRequestStatus
    
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    
    rejected_by: Optional[int] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    cancelled_by: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

class VisitRequestStatisticsResponse(BaseModel):
    total_requests: int = 0
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    cancelled_requests: int = 0
    checked_in_requests: int = 0
    checked_out_requests: int = 0
    completed_requests: int = 0
    expired_requests: int = 0
    today_requests: int = 0
    average_approval_time_minutes: float = 0.0
    peak_visiting_hours: Dict[str, int] = Field(default_factory=dict)

class VisitRequestCalendarItem(BaseModel):
    date: str
    total_count: int = 0
    pending_count: int = 0
    approved_count: int = 0
    completed_count: int = 0

class VisitRequestCalendarResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    total_requests: int = 0
    days: List[VisitRequestCalendarItem] = Field(default_factory=list)
    requests: List[VisitRequestResponse] = Field(default_factory=list)
