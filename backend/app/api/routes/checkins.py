from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.models.checkin import CheckInStatus
from app.schemas.auth import ResponseEnvelope
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.checkin_schema import (
    QRCheckInRequest,
    ManualCheckInRequest,
    QRCheckOutRequest,
    ManualCheckOutRequest,
    UndoCheckInRequest,
    CheckInResponse,
    ScanLogResponse,
    CheckInPaginationRequest,
    CheckInStatisticsResponse,
    LiveDashboardResponse
)
from app.services.checkin_service import CheckInService

router = APIRouter(tags=["Gate Security & Check-In/Out Management"])


# --- Check-In & Check-Out Execution Endpoints ---

@router.post("/checkin/scan", response_model=ResponseEnvelope[CheckInResponse], status_code=status.HTTP_201_CREATED)
def scan_checkin(
    request_data: QRCheckInRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_CREATE))
):
    """
    Scan visitor QR code and execute entry check-in via 12-stage enterprise validation pipeline.
    """
    client_ip = request.client.host if request.client else None
    dto = CheckInService.scan_checkin(
        db=db,
        current_user=current_user,
        request_data=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor check-in recorded successfully",
        data=dto
    )


@router.post("/checkin/manual", response_model=ResponseEnvelope[CheckInResponse], status_code=status.HTTP_201_CREATED)
def manual_checkin(
    request_data: ManualCheckInRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_MANUAL))
):
    """
    Perform manual check-in override for a visitor with required justification reason.
    """
    client_ip = request.client.host if request.client else None
    dto = CheckInService.manual_checkin(
        db=db,
        current_user=current_user,
        request_data=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Manual check-in override recorded successfully",
        data=dto
    )


@router.post("/checkout/scan", response_model=ResponseEnvelope[CheckInResponse])
def scan_checkout(
    request_data: QRCheckOutRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKOUT_CREATE))
):
    """
    Scan visitor QR code and execute exit check-out with automatic attendance duration calculation.
    """
    client_ip = request.client.host if request.client else None
    dto = CheckInService.scan_checkout(
        db=db,
        current_user=current_user,
        request_data=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor check-out recorded successfully",
        data=dto
    )


@router.post("/checkout/manual", response_model=ResponseEnvelope[CheckInResponse])
def manual_checkout(
    request_data: ManualCheckOutRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKOUT_MANUAL))
):
    """
    Perform manual check-out override for a visitor.
    """
    client_ip = request.client.host if request.client else None
    dto = CheckInService.manual_checkout(
        db=db,
        current_user=current_user,
        request_data=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Manual check-out override recorded successfully",
        data=dto
    )


# --- Dashboard & Activity Timeline Endpoints ---

@router.get("/checkins/live-dashboard", response_model=ResponseEnvelope[LiveDashboardResponse])
def get_live_dashboard(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.GATE_DASHBOARD_VIEW))
):
    """
    Retrieve real-time Live Security Dashboard metrics including current occupancy,
    peak occupancy, visitors inside by gate & department, and recent timeline activities.
    """
    dashboard_dto = CheckInService.get_live_dashboard(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Live gate dashboard metrics retrieved successfully",
        data=dashboard_dto
    )


@router.get("/checkins", response_model=ResponseEnvelope[EnhancedPaginationResponse[CheckInResponse]])
def list_checkins(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search across visitor name, phone, host, gate"),
    status_filter: Optional[CheckInStatus] = Query(default=None, alias="status", description="Filter by check-in status"),
    gate_name: Optional[str] = Query(default=None, description="Filter by gate name"),
    visitor_id: Optional[int] = Query(default=None, description="Filter by visitor ID"),
    host_id: Optional[int] = Query(default=None, description="Filter by host employee ID"),
    start_date: Optional[datetime] = Query(default=None, description="Start check-in timestamp"),
    end_date: Optional[datetime] = Query(default=None, description="End check-in timestamp"),
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID (Super Admin only)"),
    sort_by: str = Query(default="checkin_time", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_READ))
):
    """
    Retrieve paginated, searched, and filtered gate check-in activity timeline.
    """
    params = CheckInPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        gate_name=gate_name,
        visitor_id=visitor_id,
        host_id=host_id,
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = CheckInService.list_checkins(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Check-in records retrieved successfully",
        data=paginated_dto
    )


@router.get("/checkins/active", response_model=ResponseEnvelope[EnhancedPaginationResponse[CheckInResponse]])
def get_active_visitors(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    gate_name: Optional[str] = Query(default=None),
    tenant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_READ))
):
    """
    Get list of visitors currently checked inside facility.
    """
    params = CheckInPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        gate_name=gate_name,
        tenant_id=tenant_id
    )
    paginated_dto = CheckInService.get_active_visitors(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Active visitors inside facility retrieved successfully",
        data=paginated_dto
    )


@router.get("/checkins/statistics", response_model=ResponseEnvelope[CheckInStatisticsResponse])
def get_checkin_statistics(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_READ))
):
    """
    Retrieve statistics summary for check-in operations.
    """
    stats_dto = CheckInService.get_statistics(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Check-in statistics retrieved successfully",
        data=stats_dto
    )


@router.get("/checkins/scan-logs", response_model=ResponseEnvelope[List[ScanLogResponse]])
def list_scan_logs(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.SCAN_LOGS_VIEW))
):
    """
    Retrieve security scan attempt logs (both SUCCESS and FAILED scans) for security analytics.
    """
    logs_dto = CheckInService.list_scan_logs(db=db, current_user=current_user, limit=limit)
    return ResponseEnvelope(
        success=True,
        message="Scan logs retrieved successfully",
        data=logs_dto
    )


@router.get("/checkins/export")
def export_checkins_csv(
    search: Optional[str] = Query(default=None),
    status_filter: Optional[CheckInStatus] = Query(default=None, alias="status"),
    gate_name: Optional[str] = Query(default=None),
    tenant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_EXPORT))
):
    """
    Export gate check-in records to CSV format file.
    """
    params = CheckInPaginationRequest(
        search=search,
        status=status_filter,
        gate_name=gate_name,
        tenant_id=tenant_id
    )
    csv_content = CheckInService.export_checkins_csv(db=db, current_user=current_user, params=params)
    filename = f"checkins_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/checkins/{id}", response_model=ResponseEnvelope[CheckInResponse])
def get_checkin_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_READ))
):
    """
    Retrieve details of a specific check-in record by ID.
    """
    dto = CheckInService.get_checkin_by_id(db=db, current_user=current_user, checkin_id=id)
    return ResponseEnvelope(
        success=True,
        message="Check-in record details retrieved successfully",
        data=dto
    )


@router.patch("/checkins/{id}/undo", response_model=ResponseEnvelope[CheckInResponse])
def undo_checkin(
    id: int,
    request_data: UndoCheckInRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.CHECKIN_UNDO))
):
    """
    Revert visitor check-in state (Admin only). Reverts pass to ACTIVE and visit request to APPROVED.
    """
    client_ip = request.client.host if request.client else None
    dto = CheckInService.undo_checkin(
        db=db,
        current_user=current_user,
        checkin_id=id,
        request_data=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Check-in record state reverted successfully",
        data=dto
    )
