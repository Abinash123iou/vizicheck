from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.approval import ApprovalStatus, ApprovalAction, ApprovalType


class ApprovalCreate(BaseModel):
    request_id: int = Field(..., description="ID of the Visit Request to approve")
    tenant_id: Optional[int] = Field(None, description="Tenant ID (inferred if omitted)")
    approval_type: ApprovalType = Field(ApprovalType.SINGLE_LEVEL, description="Single or multi-level workflow")
    total_steps: int = Field(1, ge=1, le=5, description="Total steps in workflow")
    current_approver_id: Optional[int] = Field(None, description="Host / Approver User ID (defaults to Visit Request host)")
    expires_at: Optional[datetime] = Field(None, description="Approval expiration timestamp")
    notes: Optional[str] = Field(None, max_length=500, description="Workflow notes")


class ApprovalActionRequest(BaseModel):
    action: ApprovalAction = Field(..., description="Action to perform: APPROVE, REJECT, DELEGATE, ESCALATE")
    comments: Optional[str] = Field(None, max_length=500, description="Reason / comments for action")
    target_user_id: Optional[int] = Field(None, description="Target User ID for DELEGATE or ESCALATE")


class ApprovalHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approval_id: int
    tenant_id: int
    step_number: int
    actor_id: int
    actor_name: Optional[str] = None
    action: ApprovalAction
    previous_status: ApprovalStatus
    new_status: ApprovalStatus
    comments: Optional[str] = None
    delegated_to_id: Optional[int] = None
    delegated_to_name: Optional[str] = None
    created_at: datetime


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    request_id: int
    request_code: Optional[str] = None
    visitor_name: Optional[str] = None
    host_id: Optional[int] = None
    host_name: Optional[str] = None
    approval_code: str
    approval_type: ApprovalType
    current_step: int
    total_steps: int
    current_approver_id: int
    current_approver_name: Optional[str] = None
    status: ApprovalStatus
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    history: Optional[List[ApprovalHistoryResponse]] = None



class ApprovalStatsResponse(BaseModel):
    tenant_id: int
    total_approvals: int
    pending_count: int
    approved_count: int
    rejected_count: int
    delegated_count: int
    escalated_count: int
    expired_count: int
