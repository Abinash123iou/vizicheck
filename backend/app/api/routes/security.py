from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_active_user,
    get_current_security_officer
)
from app.models.user import User
from app.services.security_service import SecurityService
from app.schemas.security import (
    SessionListResponse,
    UserSessionResponse,
    SecurityActivityListResponse,
    SecurityDashboardResponse
)

router = APIRouter(prefix="/security", tags=["Security Management"])

@router.get("/sessions", response_model=dict)
def list_active_sessions(
    user_id: Optional[int] = Query(None, description="Filter active sessions by user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List active user sessions.
    - Super Admins can list any user's sessions or all active sessions.
    - Tenant Admins and Security Officers can list active sessions in their tenant.
    - Standard Users can list their own active sessions.
    """
    result = SecurityService.get_active_sessions(db, current_user=current_user, user_id=user_id)
    return {
        "success": True,
        "message": "Active sessions retrieved successfully",
        "data": result.model_dump(),
        "errors": None
    }

@router.delete("/sessions/{id}", response_model=dict)
def revoke_session(
    id: int = Path(..., description="ID of the session to revoke"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Revoke a specific active session by ID.
    - Users can revoke their own sessions.
    - Tenant Admins, Security Officers, and Super Admins can revoke sessions of users in their scope.
    """
    revoked_session = SecurityService.revoke_session(db, current_user=current_user, session_id=id)
    return {
        "success": True,
        "message": f"Session {id} successfully revoked",
        "data": revoked_session.model_dump(),
        "errors": None
    }

@router.get("/activity", response_model=dict)
def get_security_activity_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    tenant_id: Optional[int] = Query(None, description="Filter by tenant ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. LOGIN_SUCCESS, LOGIN_FAILED, ACCOUNT_LOCKED, SUSPICIOUS_ACTIVITY)"),
    severity: Optional[str] = Query(None, description="Filter by severity level (LOW, MEDIUM, HIGH, CRITICAL)"),
    start_date: Optional[datetime] = Query(None, description="Filter logs starting from date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs up to date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_security_officer)
):
    """
    Get security activity logs with pagination and filters.
    Requires Security Officer, Tenant Admin, or Super Admin privileges.
    """
    result = SecurityService.get_security_activities(
        db,
        current_user=current_user,
        user_id=user_id,
        tenant_id=tenant_id,
        event_type=event_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )
    return {
        "success": True,
        "message": "Security activity logs retrieved successfully",
        "data": result.model_dump(),
        "errors": None
    }

@router.get("/dashboard", response_model=dict)
def get_security_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_security_officer)
):
    """
    Get security dashboard metrics (active sessions, 24h failed logins, locked accounts, suspicious activities).
    Requires Security Officer, Tenant Admin, or Super Admin privileges.
    """
    result = SecurityService.get_security_dashboard(db, current_user=current_user)
    return {
        "success": True,
        "message": "Security dashboard data retrieved successfully",
        "data": result.model_dump(),
        "errors": None
    }
