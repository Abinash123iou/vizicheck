from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.models.visit_request import VisitRequestStatus
from app.schemas.auth import ResponseEnvelope
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.request import (
    CreateVisitRequest,
    UpdateVisitRequest,
    ApprovalRequest,
    RejectRequest,
    CancelRequest,
    VisitRequestResponse,
    VisitRequestPaginationRequest,
    VisitRequestStatisticsResponse,
    VisitRequestCalendarResponse
)
from app.services.request_service import RequestService

router = APIRouter(prefix="/visit-requests", tags=["Visit Requests"])


@router.post("", response_model=ResponseEnvelope[VisitRequestResponse], status_code=status.HTTP_201_CREATED)
def create_visit_request(
    request_data: CreateVisitRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_CREATE))
):
    """
    Submit a new Visit Request for visitor approval workflow.
    """
    client_ip = request.client.host if request.client else None
    dto = RequestService.create_request(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request submitted successfully",
        data=dto
    )


@router.get("", response_model=ResponseEnvelope[EnhancedPaginationResponse[VisitRequestResponse]])
def list_visit_requests(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search term"),
    status_filter: Optional[VisitRequestStatus] = Query(default=None, alias="status", description="Filter by request status"),
    visitor_id: Optional[int] = Query(default=None, description="Filter by visitor ID"),
    host_id: Optional[int] = Query(default=None, description="Filter by host ID"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    request_code: Optional[str] = Query(default=None, description="Filter by request code"),
    start_date: Optional[datetime] = Query(default=None, description="Filter by scheduled start date range start"),
    end_date: Optional[datetime] = Query(default=None, description="Filter by scheduled start date range end"),
    tenant_id: Optional[int] = Query(default=None, description="Filter by tenant ID (Super Admin only)"),
    is_deleted: bool = Query(default=False, description="Include soft deleted records"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_READ))
):
    """
    Retrieve paginated, searched, and filtered list of visit requests.
    """
    params = VisitRequestPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        visitor_id=visitor_id,
        host_id=host_id,
        department=department,
        request_code=request_code,
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = RequestService.list_requests(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Visit requests retrieved successfully",
        data=paginated_dto
    )


@router.get("/statistics", response_model=ResponseEnvelope[VisitRequestStatisticsResponse])
def get_visit_request_statistics(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID filter (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_READ))
):
    """
    Retrieve summary statistics and analytics for visit requests.
    """
    stats_dto = RequestService.get_statistics(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Visit request statistics retrieved successfully",
        data=stats_dto
    )


@router.get("/export")
def export_visit_requests(
    search: Optional[str] = Query(default=None),
    status_filter: Optional[VisitRequestStatus] = Query(default=None, alias="status"),
    visitor_id: Optional[int] = Query(default=None),
    host_id: Optional[int] = Query(default=None),
    department: Optional[str] = Query(default=None),
    tenant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_EXPORT))
):
    """
    Export visit requests matching search criteria into CSV format.
    """
    params = VisitRequestPaginationRequest(
        search=search,
        status=status_filter,
        visitor_id=visitor_id,
        host_id=host_id,
        department=department,
        tenant_id=tenant_id
    )
    csv_data = RequestService.export_requests(db=db, current_user=current_user, params=params)
    filename = f"visit_requests_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/pending", response_model=ResponseEnvelope[List[VisitRequestResponse]])
def get_pending_visit_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_READ))
):
    """
    Retrieve list of pending visit requests awaiting approval for the current host or tenant.
    """
    pending_list = RequestService.get_pending_requests(db=db, current_user=current_user)
    return ResponseEnvelope(
        success=True,
        message="Pending visit requests retrieved successfully",
        data=pending_list
    )


@router.get("/my-requests", response_model=ResponseEnvelope[List[VisitRequestResponse]])
def get_my_visit_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve visit requests created by or hosting the authenticated user.
    """
    my_list = RequestService.get_my_requests(db=db, current_user=current_user)
    return ResponseEnvelope(
        success=True,
        message="User's visit requests retrieved successfully",
        data=my_list
    )


@router.get("/calendar", response_model=ResponseEnvelope[VisitRequestCalendarResponse])
def get_visit_requests_calendar(
    start_date: Optional[datetime] = Query(default=None, description="Calendar window start date"),
    end_date: Optional[datetime] = Query(default=None, description="Calendar window end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_READ))
):
    """
    Retrieve visit requests feed grouped by date for calendar visualization.
    """
    calendar_dto = RequestService.get_calendar(
        db=db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request calendar retrieved successfully",
        data=calendar_dto
    )


@router.get("/{id}", response_model=ResponseEnvelope[VisitRequestResponse])
def get_visit_request(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_READ))
):
    """
    Retrieve details of a single visit request by ID.
    """
    dto = RequestService.get_request_by_id(db=db, current_user=current_user, request_id=id)
    return ResponseEnvelope(
        success=True,
        message="Visit request retrieved successfully",
        data=dto
    )


@router.put("/{id}", response_model=ResponseEnvelope[VisitRequestResponse])
def update_visit_request(
    id: int,
    request_data: UpdateVisitRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_UPDATE))
):
    """
    Update details of an existing pending visit request.
    """
    client_ip = request.client.host if request.client else None
    updated_dto = RequestService.update_request(
        db=db,
        current_user=current_user,
        request_id=id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request updated successfully",
        data=updated_dto
    )


@router.delete("/{id}", response_model=ResponseEnvelope[VisitRequestResponse])
def delete_visit_request(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_DELETE))
):
    """
    Soft delete a visit request.
    """
    client_ip = request.client.host if request.client else None
    deleted_dto = RequestService.delete_request(
        db=db,
        current_user=current_user,
        request_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request deleted successfully",
        data=deleted_dto
    )


@router.patch("/{id}/approve", response_model=ResponseEnvelope[VisitRequestResponse])
@router.post("/{id}/approve", response_model=ResponseEnvelope[VisitRequestResponse])
def approve_visit_request(
    id: int,
    request: Request,
    approval_data: Optional[ApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_APPROVE))
):
    """
    Approve a pending visit request (supports both PATCH and POST verbs with optional approval remarks).
    Triggers QR pass generation and visitor notifications.
    """
    client_ip = request.client.host if request.client else None
    approved_dto = RequestService.approve_request(
        db=db,
        current_user=current_user,
        request_id=id,
        approval_data=approval_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request approved successfully",
        data=approved_dto
    )


@router.patch("/{id}/reject", response_model=ResponseEnvelope[VisitRequestResponse])
@router.post("/{id}/reject", response_model=ResponseEnvelope[VisitRequestResponse])
def reject_visit_request(
    id: int,
    rejection_data: RejectRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_REJECT))
):
    """
    Reject a pending visit request (supports both PATCH and POST verbs with explicit rejection reason).
    """
    client_ip = request.client.host if request.client else None
    rejected_dto = RequestService.reject_request(
        db=db,
        current_user=current_user,
        request_id=id,
        rejection_data=rejection_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request rejected successfully",
        data=rejected_dto
    )


@router.patch("/{id}/cancel", response_model=ResponseEnvelope[VisitRequestResponse])
@router.post("/{id}/cancel", response_model=ResponseEnvelope[VisitRequestResponse])
def cancel_visit_request(
    id: int,
    cancel_data: CancelRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_CANCEL))
):
    """
    Cancel a pending or approved visit request (supports both PATCH and POST verbs with explicit cancellation reason).
    """
    client_ip = request.client.host if request.client else None
    cancelled_dto = RequestService.cancel_request(
        db=db,
        current_user=current_user,
        request_id=id,
        cancel_data=cancel_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request cancelled successfully",
        data=cancelled_dto
    )


@router.patch("/{id}/restore", response_model=ResponseEnvelope[VisitRequestResponse])
def restore_visit_request(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISIT_REQUEST_RESTORE))
):
    """
    Restore a soft-deleted visit request.
    """
    client_ip = request.client.host if request.client else None
    restored_dto = RequestService.restore_request(
        db=db,
        current_user=current_user,
        request_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visit request restored successfully",
        data=restored_dto
    )
