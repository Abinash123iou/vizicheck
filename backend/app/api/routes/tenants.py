from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_super_admin, get_current_tenant_admin
from app.models.user import User
from app.models.tenant import TenantStatus
from app.schemas.auth import ResponseEnvelope
from app.schemas.tenant import (
    CreateTenantRequest,
    UpdateTenantRequest,
    TenantResponse,
    TenantPaginationRequest,
    EnhancedPaginationResponse,
    TenantStatisticsResponse,
    TenantActivityResponse
)
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("", response_model=ResponseEnvelope[TenantResponse], status_code=status.HTTP_201_CREATED)
def create_tenant(
    request_data: CreateTenantRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Create a new tenant organization (Super Admin only).
    """
    client_ip = request.client.host if request.client else None
    tenant_dto = TenantService.create_tenant(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant organization created successfully",
        data=tenant_dto
    )

@router.get("", response_model=ResponseEnvelope[EnhancedPaginationResponse[TenantResponse]])
def list_tenants(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search by name, email, slug, domain, code"),
    status_filter: Optional[TenantStatus] = Query(default=None, alias="status", description="Filter by tenant status"),
    is_deleted: bool = Query(default=False, description="Include soft-deleted records"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Retrieve paginated, searched, and filtered tenants.
    """
    params = TenantPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = TenantService.list_tenants(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Tenants retrieved successfully",
        data=paginated_dto
    )

@router.get("/statistics", response_model=ResponseEnvelope[TenantStatisticsResponse])
def get_tenant_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Retrieve aggregated dashboard statistics across all tenants (Super Admin only).
    """
    stats_dto = TenantService.get_statistics(db=db, current_user=current_user)
    return ResponseEnvelope(
        success=True,
        message="Tenant statistics retrieved successfully",
        data=stats_dto
    )

@router.get("/export")
def export_tenants(
    search: Optional[str] = Query(default=None, description="Search filter"),
    status_filter: Optional[TenantStatus] = Query(default=None, alias="status", description="Status filter"),
    is_deleted: bool = Query(default=False, description="Include soft deleted records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Export tenant list as downloadable CSV file (Super Admin only).
    """
    csv_content = TenantService.export_tenants_csv(
        db=db,
        current_user=current_user,
        search=search,
        status=status_filter,
        is_deleted=is_deleted
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tenants_export.csv"}
    )

@router.get("/{tenant_id}", response_model=ResponseEnvelope[TenantResponse])
def get_tenant_by_id(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Retrieve details of a specific tenant by ID.
    """
    tenant_dto = TenantService.get_tenant_by_id(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Tenant details retrieved successfully",
        data=tenant_dto
    )

@router.get("/{tenant_id}/activity", response_model=ResponseEnvelope[List[TenantActivityResponse]])
def get_tenant_activity_timeline(
    tenant_id: int,
    limit: int = Query(default=50, ge=1, le=100, description="Max audit log entries to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Retrieve audit activity timeline for a tenant.
    """
    activity_dto = TenantService.get_activity_timeline(
        db=db, 
        current_user=current_user, 
        tenant_id=tenant_id, 
        limit=limit
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant activity timeline retrieved successfully",
        data=activity_dto
    )

@router.put("/{tenant_id}", response_model=ResponseEnvelope[TenantResponse])
def update_tenant(
    tenant_id: int,
    request_data: UpdateTenantRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Update tenant details and configuration settings.
    """
    client_ip = request.client.host if request.client else None
    tenant_dto = TenantService.update_tenant(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant organization updated successfully",
        data=tenant_dto
    )

@router.delete("/{tenant_id}", response_model=ResponseEnvelope[None])
def delete_tenant(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Soft delete a tenant organization (Super Admin only).
    """
    client_ip = request.client.host if request.client else None
    TenantService.soft_delete_tenant(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant organization soft-deleted successfully",
        data=None
    )

@router.patch("/{tenant_id}/activate", response_model=ResponseEnvelope[TenantResponse])
def activate_tenant(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Activate a suspended or pending tenant account (Super Admin only).
    """
    client_ip = request.client.host if request.client else None
    tenant_dto = TenantService.activate_tenant(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant organization activated successfully",
        data=tenant_dto
    )

@router.patch("/{tenant_id}/suspend", response_model=ResponseEnvelope[TenantResponse])
def suspend_tenant(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Suspend an active tenant organization (Super Admin only).
    """
    client_ip = request.client.host if request.client else None
    tenant_dto = TenantService.suspend_tenant(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant organization suspended successfully",
        data=tenant_dto
    )

@router.patch("/{tenant_id}/restore", response_model=ResponseEnvelope[TenantResponse])
def restore_tenant(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Restore a soft-deleted tenant organization (Super Admin only).
    """
    client_ip = request.client.host if request.client else None
    tenant_dto = TenantService.restore_tenant(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Tenant organization restored successfully",
        data=tenant_dto
    )
