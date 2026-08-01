from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.models.user import User
from app.models.approval import ApprovalStatus, ApprovalType
from app.schemas.approval import (
    ApprovalCreate,
    ApprovalActionRequest,
    ApprovalResponse,
    ApprovalHistoryResponse,
    ApprovalStatsResponse
)
from app.services.approval_service import ApprovalService
from app.constants.permissions import Permissions
from app.utils.logger import get_logger

logger = get_logger("approvals_route")

router = APIRouter(prefix="/approvals", tags=["Approval Workflow Management"])


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission(Permissions.APPROVAL_CREATE))]
)
def create_approval_workflow(
    request_data: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Initialize a new approval workflow for a visit request.
    """
    logger.info(f"User '{current_user.email}' initializing approval workflow for request ID {request_data.request_id}")
    data = ApprovalService.create_approval_workflow(
        db=db,
        current_user=current_user,
        data=request_data
    )
    return {
        "success": True,
        "message": "Approval workflow created successfully",
        "data": data.model_dump(),
        "errors": None
    }


@router.get(
    "/pending",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.APPROVAL_READ))]
)
def list_pending_approvals(
    tenant_id: Optional[int] = Query(None, description="Filter by Tenant ID"),
    approver_id: Optional[int] = Query(None, description="Filter by current approver User ID"),
    approval_type: Optional[ApprovalType] = Query(None, description="Filter by Approval Type"),
    search: Optional[str] = Query(None, description="Search by code, visitor, or host"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List pending approvals assigned to current user or tenant with filters and pagination.
    """
    # Default approver filter to current_user if not super admin and no approver_id specified
    target_approver = approver_id
    if not current_user.is_super_admin and target_approver is None:
        target_approver = current_user.id

    items, total_count = ApprovalService.list_approvals(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        approver_id=target_approver,
        status=ApprovalStatus.PENDING,
        approval_type=approval_type,
        search=search,
        page=page,
        page_size=page_size
    )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "success": True,
        "message": "Pending approvals retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "pagination": {
                "total_records": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        },
        "errors": None
    }


@router.get(
    "/stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.APPROVAL_READ))]
)
def get_approval_statistics(
    tenant_id: Optional[int] = Query(None, description="Tenant ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve approval metrics summary for dashboard.
    """
    stats = ApprovalService.get_approval_stats(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id
    )
    return {
        "success": True,
        "message": "Approval statistics calculated successfully",
        "data": stats.model_dump(),
        "errors": None
    }


@router.patch(
    "/{id}/action",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.APPROVAL_ACTION))]
)
def action_approval(
    id: int = Path(..., description="Approval Workflow ID"),
    action_data: ApprovalActionRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform action (Approve, Reject, Delegate, Escalate) on an approval workflow step.
    """
    logger.info(f"User '{current_user.email}' actioning approval ID {id} with action '{action_data.action}'")
    data = ApprovalService.action_approval(
        db=db,
        current_user=current_user,
        approval_id=id,
        action_data=action_data
    )
    return {
        "success": True,
        "message": f"Approval workflow successfully processed with action '{action_data.action.value}'",
        "data": data.model_dump(),
        "errors": None
    }


@router.get(
    "/{id}/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.APPROVAL_READ))]
)
def get_approval_history_timeline(
    id: int = Path(..., description="Approval Workflow ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve audit history timeline for an approval workflow.
    """
    history = ApprovalService.get_approval_history(
        db=db,
        current_user=current_user,
        approval_id=id
    )
    return {
        "success": True,
        "message": "Approval history timeline retrieved successfully",
        "data": [item.model_dump() for item in history],
        "errors": None
    }


@router.get(
    "/{id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.APPROVAL_READ))]
)
def get_approval_details(
    id: int = Path(..., description="Approval Workflow ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve approval details by ID.
    """
    data = ApprovalService.get_approval_by_id(
        db=db,
        current_user=current_user,
        approval_id=id
    )
    return {
        "success": True,
        "message": "Approval details retrieved successfully",
        "data": data.model_dump(),
        "errors": None
    }
