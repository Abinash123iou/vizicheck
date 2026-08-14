from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field

class ReportSummaryResponse(BaseModel):
    tenant_id: Optional[int] = None
    total_visitors: int = 0
    verified_visitors: int = 0
    blacklisted_visitors: int = 0
    total_visit_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    pending_requests: int = 0
    total_passes_issued: int = 0
    active_passes: int = 0
    total_checkins: int = 0
    total_checkouts: int = 0
    average_stay_duration_minutes: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class VisitorAnalyticsReportResponse(BaseModel):
    total_visitors: int = 0
    new_visitors_period: int = 0
    verified_count: int = 0
    blacklisted_count: int = 0
    by_company: Dict[str, int] = Field(default_factory=dict)
    by_verification_status: Dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class GateActivityReportResponse(BaseModel):
    total_checkins: int = 0
    total_checkouts: int = 0
    currently_on_site: int = 0
    verification_failures: int = 0
    manual_overrides: int = 0

    model_config = ConfigDict(from_attributes=True)
