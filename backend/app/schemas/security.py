from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class UserSessionResponse(BaseModel):
    id: int
    user_id: int
    tenant_id: Optional[int] = None
    token_jti: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    sessions: List[UserSessionResponse]
    total: int


class SecurityActivityResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    event_type: str
    severity: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityActivityListResponse(BaseModel):
    activities: List[SecurityActivityResponse]
    total: int
    page: int
    limit: int


class SecurityDashboardMetrics(BaseModel):
    total_active_sessions: int
    failed_logins_24h: int
    locked_accounts_count: int
    suspicious_activities_count: int


class SecurityDashboardResponse(BaseModel):
    metrics: SecurityDashboardMetrics
    recent_activities: List[SecurityActivityResponse]
