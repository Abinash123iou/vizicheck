from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_tenant_admin
)
from app.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["Audit Management"])

@router.get("", response_model=dict)
def list_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    tenant_id: Optional[int] = Query(None, description="Filter by tenant ID"),
    module: Optional[str] = Query(None, description="Filter by system module"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    start_date: Optional[datetime] = Query(None, description="Start timestamp"),
    end_date: Optional[datetime] = Query(None, description="End timestamp"),
    search: Optional[str] = Query(None, description="Search term across action, module, and IP"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    List audit logs with multi-tenant isolation, query parameters, search, and pagination.
    Requires Tenant Admin or Super Admin privileges.
    """
    result = AuditService.get_audit_logs(
        db,
        current_user=current_user,
        user_id=user_id,
        tenant_id=tenant_id,
        module=module,
        action=action,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        limit=limit
    )
    return {
        "success": True,
        "message": "Audit logs retrieved successfully",
        "data": result.model_dump(),
        "errors": None
    }

@router.get("/export")
def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format (csv or json)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    tenant_id: Optional[int] = Query(None, description="Filter by tenant ID"),
    module: Optional[str] = Query(None, description="Filter by system module"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    start_date: Optional[datetime] = Query(None, description="Start timestamp"),
    end_date: Optional[datetime] = Query(None, description="End timestamp"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Export audit logs into CSV or JSON format with multi-tenant isolation.
    Requires Tenant Admin or Super Admin privileges.
    """
    content, media_type, filename = AuditService.export_audit_logs(
        db,
        current_user=current_user,
        export_format=format,
        user_id=user_id,
        tenant_id=tenant_id,
        module=module,
        action=action,
        start_date=start_date,
        end_date=end_date
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return Response(
        content=content,
        media_type=media_type,
        headers=headers
    )
