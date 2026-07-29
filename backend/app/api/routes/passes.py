from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.models.visitor_pass import PassStatus
from app.schemas.auth import ResponseEnvelope
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.pass_schema import (
    GeneratePassRequest,
    UpdatePassRequest,
    RevokePassRequest,
    PassResponse,
    QRResponse,
    PassPaginationRequest,
    PassStatisticsResponse
)
from app.services.pass_service import PassService

router = APIRouter(prefix="/passes", tags=["Visitor Passes & QR Code Management"])


@router.post("/generate/{visit_request_id}", response_model=ResponseEnvelope[PassResponse], status_code=status.HTTP_201_CREATED)
def generate_visitor_pass(
    visit_request_id: int,
    request: Request,
    request_data: Optional[GeneratePassRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_GENERATE))
):
    """
    Generate a new secure Visitor Pass & cryptographically signed QR Token for an approved visit request.
    """
    client_ip = request.client.host if request.client else None
    dto = PassService.generate_pass(
        db=db,
        current_user=current_user,
        visit_request_id=visit_request_id,
        request_data=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor pass generated successfully",
        data=dto
    )


@router.get("", response_model=ResponseEnvelope[EnhancedPaginationResponse[PassResponse]])
def list_passes(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search term across pass code, visitor, host"),
    status_filter: Optional[PassStatus] = Query(default=None, alias="status", description="Filter by pass status"),
    visitor_id: Optional[int] = Query(default=None, description="Filter by visitor ID"),
    host_id: Optional[int] = Query(default=None, description="Filter by host employee ID"),
    visit_request_id: Optional[int] = Query(default=None, description="Filter by visit request ID"),
    tenant_id: Optional[int] = Query(default=None, description="Filter by tenant ID (Super Admin only)"),
    is_deleted: bool = Query(default=False, description="Include soft deleted records"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_READ))
):
    """
    Retrieve paginated, searched, and filtered list of visitor passes.
    """
    params = PassPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        visitor_id=visitor_id,
        host_id=host_id,
        visit_request_id=visit_request_id,
        tenant_id=tenant_id,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = PassService.list_passes(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Visitor passes retrieved successfully",
        data=paginated_dto
    )


@router.get("/statistics", response_model=ResponseEnvelope[PassStatisticsResponse])
def get_pass_statistics(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID filter (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_READ))
):
    """
    Retrieve dashboard statistics and analytics metrics for visitor passes.
    """
    stats_dto = PassService.get_statistics(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Pass statistics retrieved successfully",
        data=stats_dto
    )


@router.get("/export")
def export_passes(
    search: Optional[str] = Query(default=None),
    status_filter: Optional[PassStatus] = Query(default=None, alias="status"),
    visitor_id: Optional[int] = Query(default=None),
    host_id: Optional[int] = Query(default=None),
    tenant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_EXPORT))
):
    """
    Export visitor passes matching search criteria into CSV format.
    """
    params = PassPaginationRequest(
        search=search,
        status=status_filter,
        visitor_id=visitor_id,
        host_id=host_id,
        tenant_id=tenant_id
    )
    csv_data = PassService.export_passes(db=db, current_user=current_user, params=params)
    filename = f"visitor_passes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/code/{pass_code}", response_model=ResponseEnvelope[PassResponse])
def get_pass_by_code(
    pass_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_READ))
):
    """
    Find visitor pass by human-readable pass code.
    """
    dto = PassService.get_pass_by_code(db=db, current_user=current_user, pass_code=pass_code)
    return ResponseEnvelope(
        success=True,
        message="Visitor pass retrieved successfully",
        data=dto
    )


@router.get("/{id}", response_model=ResponseEnvelope[PassResponse])
def get_pass(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_READ))
):
    """
    Retrieve details of a single visitor pass by ID.
    """
    dto = PassService.get_pass_by_id(db=db, current_user=current_user, pass_id=id)
    return ResponseEnvelope(
        success=True,
        message="Visitor pass retrieved successfully",
        data=dto
    )


@router.put("/{id}", response_model=ResponseEnvelope[PassResponse])
def update_pass(
    id: int,
    request_data: UpdatePassRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_UPDATE))
):
    """
    Update validity timestamps or notes of an existing visitor pass.
    """
    client_ip = request.client.host if request.client else None
    updated_dto = PassService.update_pass(
        db=db,
        current_user=current_user,
        pass_id=id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor pass updated successfully",
        data=updated_dto
    )


@router.delete("/{id}", response_model=ResponseEnvelope[PassResponse])
def delete_pass(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_DELETE))
):
    """
    Soft delete a visitor pass.
    """
    client_ip = request.client.host if request.client else None
    deleted_dto = PassService.delete_pass(
        db=db,
        current_user=current_user,
        pass_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor pass deleted successfully",
        data=deleted_dto
    )


@router.get("/{id}/qr", response_model=ResponseEnvelope[QRResponse])
def get_pass_qr(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.QR_VIEW))
):
    """
    Retrieve active cryptographically signed JWT QR Token and base64 rendering payload for a pass.
    """
    qr_dto = PassService.get_qr_info(db=db, current_user=current_user, pass_id=id)
    return ResponseEnvelope(
        success=True,
        message="QR token information retrieved successfully",
        data=qr_dto
    )


@router.post("/{id}/regenerate-qr", response_model=ResponseEnvelope[QRResponse])
def regenerate_pass_qr(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.QR_REGENERATE))
):
    """
    Regenerate QR token for a pass. Increments QR version and invalidates previous token versions.
    """
    client_ip = request.client.host if request.client else None
    qr_dto = PassService.regenerate_qr_token(
        db=db,
        current_user=current_user,
        pass_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="QR token regenerated successfully",
        data=qr_dto
    )


@router.patch("/{id}/revoke", response_model=ResponseEnvelope[PassResponse])
@router.post("/{id}/revoke", response_model=ResponseEnvelope[PassResponse])
def revoke_pass(
    id: int,
    revocation_data: RevokePassRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_REVOKE))
):
    """
    Manually revoke an active visitor pass (supports both PATCH and POST verbs with explicit reason).
    """
    client_ip = request.client.host if request.client else None
    revoked_dto = PassService.revoke_pass(
        db=db,
        current_user=current_user,
        pass_id=id,
        revocation_data=revocation_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor pass revoked successfully",
        data=revoked_dto
    )


@router.patch("/{id}/restore", response_model=ResponseEnvelope[PassResponse])
def restore_pass(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.PASS_RESTORE))
):
    """
    Restore a soft-deleted visitor pass.
    """
    client_ip = request.client.host if request.client else None
    restored_dto = PassService.restore_pass(
        db=db,
        current_user=current_user,
        pass_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Visitor pass restored successfully",
        data=restored_dto
    )
