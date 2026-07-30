from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.checkin import CheckInStatus, GateVerificationStatus



class GateDeviceMeta(BaseModel):
    """
    Authenticated metadata for gate scanning devices.
    """
    gate_device_id: Optional[str] = Field(default="DEV-GATE-01", description="Unique device identifier")
    scanner_name: Optional[str] = Field(default="Main Gate Scanner 1", description="Friendly scanner name")
    scanner_ip: Optional[str] = Field(default=None, description="IP address of scanning unit")
    scanner_location: Optional[str] = Field(default="Main Gate Entrance", description="Physical location")
    scanner_version: Optional[str] = Field(default="v1.0.0", description="Scanner software version")
    gate_name: Optional[str] = Field(default="Main Gate", description="Gate name")
    gate_number: Optional[str] = Field(default="Gate 1", description="Gate number/bay")


class QRCheckInRequest(BaseModel):
    """
    Request schema for scanning QR code during gate check-in.
    """
    qr_token: str = Field(..., description="Encrypted JWT QR token string or scanned raw payload")
    device_meta: Optional[GateDeviceMeta] = Field(default=None, description="Gate scanner device metadata")
    notes: Optional[str] = Field(default=None, description="Optional entry notes by security officer")


class ManualCheckInRequest(BaseModel):
    """
    Request schema for security override / manual check-in.
    """
    pass_code: Optional[str] = Field(default=None, description="Pass code identifier")
    pass_id: Optional[int] = Field(default=None, description="Pass integer ID")
    request_code: Optional[str] = Field(default=None, description="Visit request code")
    reason: str = Field(..., min_length=3, description="Required justification reason for manual check-in override")
    device_meta: Optional[GateDeviceMeta] = Field(default=None, description="Gate scanner device metadata")
    notes: Optional[str] = Field(default=None, description="Optional notes")


class QRCheckOutRequest(BaseModel):
    """
    Request schema for scanning QR code during exit check-out.
    """
    qr_token: str = Field(..., description="Encrypted JWT QR token string or scanned raw payload")
    device_meta: Optional[GateDeviceMeta] = Field(default=None, description="Gate scanner device metadata")
    notes: Optional[str] = Field(default=None, description="Optional exit notes by security officer")


class ManualCheckOutRequest(BaseModel):
    """
    Request schema for manual exit check-out override.
    """
    checkin_id: Optional[int] = Field(default=None, description="Check-in record integer ID")
    pass_code: Optional[str] = Field(default=None, description="Pass code identifier")
    reason: str = Field(..., min_length=3, description="Required justification reason for manual check-out override")
    device_meta: Optional[GateDeviceMeta] = Field(default=None, description="Gate scanner device metadata")
    notes: Optional[str] = Field(default=None, description="Optional exit notes")


class UndoCheckInRequest(BaseModel):
    """
    Request schema for admin undoing a check-in.
    """
    reason: str = Field(..., min_length=3, description="Reason for reverting visitor check-in state")


class CheckInResponse(BaseModel):
    """
    Unified response DTO for CheckIn records.
    """
    id: int
    uuid: str
    tenant_id: int
    pass_id: int
    visit_request_id: int
    visitor_id: int
    host_id: int

    checkin_time: datetime
    checkout_time: Optional[datetime] = None
    status: CheckInStatus

    gate_device_id: Optional[str] = None
    scanner_name: Optional[str] = None
    scanner_ip: Optional[str] = None
    scanner_location: Optional[str] = None
    scanner_version: Optional[str] = None
    gate_name: Optional[str] = None
    gate_number: Optional[str] = None

    verification_method: str
    checked_in_by: Optional[int] = None
    checked_out_by: Optional[int] = None
    checkin_notes: Optional[str] = None
    checkout_notes: Optional[str] = None

    is_manual_checkin: bool
    is_manual_checkout: bool
    manual_checkin_reason: Optional[str] = None
    manual_checkout_reason: Optional[str] = None

    visit_duration_minutes: Optional[float] = None
    visit_duration_seconds: Optional[int] = None

    is_undone: bool = False
    undone_by: Optional[int] = None
    undone_at: Optional[datetime] = None
    undone_reason: Optional[str] = None

    visitor_name: Optional[str] = None
    visitor_code: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_phone: Optional[str] = None
    visitor_company: Optional[str] = None

    host_name: Optional[str] = None
    host_department: Optional[str] = None
    pass_code: Optional[str] = None
    request_code: Optional[str] = None
    purpose: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScanLogResponse(BaseModel):
    """
    DTO for scan log analytics records.
    """
    id: int
    tenant_id: int
    pass_id: Optional[int] = None
    visitor_id: Optional[int] = None
    gate_device_id: Optional[str] = None
    scanner_name: Optional[str] = None
    scanner_ip: Optional[str] = None
    qr_token: Optional[str] = None
    scan_result: GateVerificationStatus
    reason: str
    ip_address: Optional[str] = None
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


class GateEventResponse(BaseModel):
    """
    DTO for gate event history log entries.
    """
    id: int
    tenant_id: int
    checkin_id: Optional[int] = None
    pass_id: Optional[int] = None
    event_type: str
    performed_by: Optional[int] = None
    performed_by_name: Optional[str] = None
    gate_device_id: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class CheckInPaginationRequest(BaseModel):
    """
    Query parameters for filtering, searching, and paginating check-ins.
    """
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    search: Optional[str] = None
    status: Optional[CheckInStatus] = None
    gate_name: Optional[str] = None
    visitor_id: Optional[int] = None
    host_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tenant_id: Optional[int] = None
    sort_by: str = "checkin_time"
    order: str = "desc"


class CheckInStatisticsResponse(BaseModel):
    """
    Summary metrics DTO for check-in statistics.
    """
    total_checkins_today: int
    total_checkouts_today: int
    active_visitors_count: int
    manual_overrides_count: int
    average_visit_duration_minutes: float
    gate_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]


class LiveDashboardResponse(BaseModel):
    """
    Comprehensive Live Gate Dashboard response payload for real-time monitoring.
    """
    visitors_inside: int
    todays_entries: int
    todays_exits: int
    pending_exits: int
    current_occupancy: int
    peak_occupancy_today: int
    average_visit_duration_minutes: float
    visitors_inside_by_gate: Dict[str, int]
    visitors_inside_by_department: Dict[str, int]
    recent_activities: List[GateEventResponse]
    scan_analytics_summary: Dict[str, int]
