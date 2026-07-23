from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user, get_current_tenant_admin
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import ResponseEnvelope
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    PaginationRequest,
    EnhancedPaginationResponse,
    ChangePasswordRequest,
    ResetPasswordRequest
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=ResponseEnvelope[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(
    request_data: CreateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Create a new user account (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    user_dto = UserService.create_user(
        db=db, 
        current_user=current_user, 
        request=request_data, 
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User account created successfully",
        data=user_dto
    )

@router.get("", response_model=ResponseEnvelope[EnhancedPaginationResponse[UserResponse]])
def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search term for name or email"),
    role_id: Optional[int] = Query(default=None, description="Filter by Role ID"),
    tenant_id: Optional[int] = Query(default=None, description="Filter by Tenant ID"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    is_deleted: bool = Query(default=False, description="Include soft deleted records"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Retrieve paginated, searched, and filtered users (Super Admin & Tenant Admin only).
    """
    params = PaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        role_id=role_id,
        tenant_id=tenant_id,
        is_active=is_active,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = UserService.list_users(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Users retrieved successfully",
        data=paginated_dto
    )

@router.get("/roles", response_model=ResponseEnvelope[list])
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Retrieve list of system roles and their database IDs.
    """
    roles = db.query(Role).all()
    roles_data = [{"id": r.id, "name": r.name, "description": r.description} for r in roles]
    return ResponseEnvelope(
        success=True,
        message="Roles retrieved successfully",
        data=roles_data
    )

@router.get("/{user_id}", response_model=ResponseEnvelope[UserResponse])
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Retrieve details of a specific user by ID (Super Admin & Tenant Admin only).
    """
    user_dto = UserService.get_user_by_id(db=db, current_user=current_user, user_id=user_id)
    return ResponseEnvelope(
        success=True,
        message="User details retrieved successfully",
        data=user_dto
    )

@router.put("/{user_id}", response_model=ResponseEnvelope[UserResponse])
def update_user(
    user_id: int,
    request_data: UpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Update details of a user account (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    user_dto = UserService.update_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User account updated successfully",
        data=user_dto
    )

@router.delete("/{user_id}", response_model=ResponseEnvelope[None])
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Soft delete a user account (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    UserService.soft_delete_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User account soft-deleted successfully",
        data=None
    )

@router.patch("/{user_id}/activate", response_model=ResponseEnvelope[UserResponse])
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Activate a user account (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    user_dto = UserService.activate_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User account activated successfully",
        data=user_dto
    )

@router.patch("/{user_id}/deactivate", response_model=ResponseEnvelope[UserResponse])
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Deactivate a user account (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    user_dto = UserService.deactivate_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User account deactivated successfully",
        data=user_dto
    )

@router.patch("/{user_id}/restore", response_model=ResponseEnvelope[UserResponse])
def restore_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Restore a soft-deleted user account (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    user_dto = UserService.restore_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User account restored successfully",
        data=user_dto
    )

@router.patch("/change-password", response_model=ResponseEnvelope[None])
def change_password(
    request_data: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Change logged-in user's password.
    """
    client_ip = request.client.host if request.client else None
    UserService.change_password(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Password changed successfully",
        data=None
    )

@router.patch("/{user_id}/reset-password", response_model=ResponseEnvelope[None])
def reset_user_password(
    user_id: int,
    request_data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Reset password for a specified user (Super Admin & Tenant Admin only).
    """
    client_ip = request.client.host if request.client else None
    UserService.reset_password(
        db=db,
        current_user=current_user,
        user_id=user_id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User password reset successfully",
        data=None
    )
