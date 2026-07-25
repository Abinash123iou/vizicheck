from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.models.visitor import VisitorStatus
from app.schemas.auth import ResponseEnvelope
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.visitor import (
    CreateVisitorRequest,
    UpdateVisitorRequest,
    VerifyVisitorRequest,
    BlacklistVisitorRequest,
    VisitorResponse,
    VisitorActivityResponse,
    VisitorPaginationRequest,
    VisitorStatisticsResponse
)
from app.services.visitor_service import VisitorService

router = APIRouter(prefix="/visitors", tags=["Visitors"])


@router.post("", response_model=ResponseEnvelope[VisitorResponse], status_code=status.HTTP_201_CREATED)
def create_visitor(
    request_data: CreateVisitorRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_CREATE))
):
    """
    Register a new visitor record in the organization.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.create_visitor(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor registered successfully",
        data=visitor_dto
    )


@router.get("", response_model=ResponseEnvelope[EnhancedPaginationResponse[VisitorResponse]])
def list_visitors(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="General multi-field search"),
    phone: Optional[str] = Query(default=None, description="Filter by phone"),
    email: Optional[str] = Query(default=None, description="Filter by email"),
    company: Optional[str] = Query(default=None, description="Filter by company"),
    government_id_number: Optional[str] = Query(default=None, description="Filter by Government ID"),
    visitor_code: Optional[str] = Query(default=None, description="Filter by visitor code"),
    status_filter: Optional[VisitorStatus] = Query(default=None, alias="status", description="Filter by visitor status"),
    verified: Optional[bool] = Query(default=None, description="Filter by verification state"),
    blacklisted: Optional[bool] = Query(default=None, description="Filter by blacklist state"),
    tenant_id: Optional[int] = Query(default=None, description="Filter by tenant ID (Super Admin only)"),
    created_from: Optional[datetime] = Query(default=None, description="Created date range start"),
    created_to: Optional[datetime] = Query(default=None, description="Created date range end"),
    is_deleted: bool = Query(default=False, description="Include soft-deleted records"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_READ))
):
    """
    Retrieve paginated, searched, and filtered list of visitors.
    """
    params = VisitorPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        phone=phone,
        email=email,
        company=company,
        government_id_number=government_id_number,
        visitor_code=visitor_code,
        status=status_filter,
        verified=verified,
        blacklisted=blacklisted,
        tenant_id=tenant_id,
        created_from=created_from,
        created_to=created_to,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = VisitorService.list_visitors(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Visitors retrieved successfully",
        data=paginated_dto
    )


@router.get("/statistics", response_model=ResponseEnvelope[VisitorStatisticsResponse])
def get_visitor_statistics(
    tenant_id: Optional[int] = Query(default=None, description="Filter statistics by tenant ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_READ))
):
    """
    Retrieve dashboard statistics for visitor management.
    """
    stats_dto = VisitorService.get_statistics(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Visitor statistics retrieved successfully",
        data=stats_dto
    )


@router.get("/export")
def export_visitors(
    search: Optional[str] = Query(default=None, description="Search term filter"),
    status_filter: Optional[VisitorStatus] = Query(default=None, alias="status", description="Status filter"),
    verified: Optional[bool] = Query(default=None, description="Verified state filter"),
    blacklisted: Optional[bool] = Query(default=None, description="Blacklist state filter"),
    is_deleted: bool = Query(default=False, description="Include soft deleted records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_EXPORT))
):
    """
    Export visitor list as a downloadable CSV file.
    """
    csv_content = VisitorService.export_visitors_csv(
        db=db,
        current_user=current_user,
        search=search,
        status=status_filter,
        verified=verified,
        blacklisted=blacklisted,
        is_deleted=is_deleted
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=visitors_export.csv"}
    )


@router.get("/code/{visitor_code}", response_model=ResponseEnvelope[VisitorResponse])
def get_visitor_by_code(
    visitor_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_READ))
):
    """
    Lookup visitor profile details by unique visitor code.
    """
    visitor_dto = VisitorService.get_visitor_by_code(db=db, current_user=current_user, visitor_code=visitor_code)
    return ResponseEnvelope(
        success=True,
        message="Visitor details retrieved successfully",
        data=visitor_dto
    )


@router.get("/{id}", response_model=ResponseEnvelope[VisitorResponse])
def get_visitor_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_READ))
):
    """
    Retrieve details of a visitor profile by ID.
    """
    visitor_dto = VisitorService.get_visitor_by_id(db=db, current_user=current_user, visitor_id=id)
    return ResponseEnvelope(
        success=True,
        message="Visitor details retrieved successfully",
        data=visitor_dto
    )


@router.get("/{id}/activity", response_model=ResponseEnvelope[List[VisitorActivityResponse]])
def get_visitor_activity_timeline(
    id: int,
    limit: int = Query(default=50, ge=1, le=100, description="Max activity logs to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_READ))
):
    """
    Retrieve audit activity timeline for a visitor entity.
    """
    activity_dto = VisitorService.get_visitor_activity(db=db, current_user=current_user, visitor_id=id, limit=limit)
    return ResponseEnvelope(
        success=True,
        message="Visitor activity timeline retrieved successfully",
        data=activity_dto
    )


@router.put("/{id}", response_model=ResponseEnvelope[VisitorResponse])
def update_visitor(
    id: int,
    request_data: UpdateVisitorRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_UPDATE))
):
    """
    Update visitor profile information.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.update_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor details updated successfully",
        data=visitor_dto
    )


@router.delete("/{id}", response_model=ResponseEnvelope[None])
def delete_visitor(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_DELETE))
):
    """
    Soft delete a visitor record.
    """
    client_ip = request.client.host if request.client else None
    VisitorService.soft_delete_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor soft-deleted successfully",
        data=None
    )


@router.patch("/{id}/restore", response_model=ResponseEnvelope[VisitorResponse])
def restore_visitor(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_RESTORE))
):
    """
    Restore a soft-deleted visitor record.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.restore_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor restored successfully",
        data=visitor_dto
    )


@router.patch("/{id}/verify", response_model=ResponseEnvelope[VisitorResponse])
def verify_visitor(
    id: int,
    request_data: VerifyVisitorRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_VERIFY))
):
    """
    Verify a visitor's identity proof and profile.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.verify_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor identity verified successfully",
        data=visitor_dto
    )


@router.patch("/{id}/blacklist", response_model=ResponseEnvelope[VisitorResponse])
def blacklist_visitor(
    id: int,
    request_data: BlacklistVisitorRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_BLACKLIST))
):
    """
    Blacklist a visitor record with mandatory reason.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.blacklist_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor blacklisted successfully",
        data=visitor_dto
    )


@router.patch("/{id}/remove-blacklist", response_model=ResponseEnvelope[VisitorResponse])
def remove_blacklist_visitor(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_BLACKLIST))
):
    """
    Remove blacklist status from a visitor.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.remove_blacklist(
        db=db,
        current_user=current_user,
        visitor_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Blacklist status removed from visitor successfully",
        data=visitor_dto
    )


@router.patch("/{id}/activate", response_model=ResponseEnvelope[VisitorResponse])
def activate_visitor(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_STATUS))
):
    """
    Activate a visitor record.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.activate_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor activated successfully",
        data=visitor_dto
    )


@router.patch("/{id}/deactivate", response_model=ResponseEnvelope[VisitorResponse])
def deactivate_visitor(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.VISITOR_STATUS))
):
    """
    Deactivate a visitor record.
    """
    client_ip = request.client.host if request.client else None
    visitor_dto = VisitorService.deactivate_visitor(
        db=db,
        current_user=current_user,
        visitor_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor deactivated successfully",
        data=visitor_dto
    )
