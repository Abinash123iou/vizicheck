from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.approval import Approval, ApprovalStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.core.exceptions import (
    NotFoundException,
    AuthorizationException,
    BusinessRuleException
)


class ApprovalValidator:
    """
    Validation pipeline for Approval Workflow management.
    """

    @staticmethod
    def validate_tenant_boundary(current_user: User, target_tenant_id: Optional[int]) -> int:
        if current_user.is_super_admin:
            if target_tenant_id is not None:
                return target_tenant_id
            if current_user.tenant_id:
                return current_user.tenant_id
            raise BusinessRuleException("Super admin must provide a tenant_id parameter.")
        
        if target_tenant_id is not None and target_tenant_id != current_user.tenant_id:
            raise AuthorizationException("Access denied. You cannot manage approvals for another tenant.")
        
        if not current_user.tenant_id:
            raise AuthorizationException("User is not associated with any active tenant.")
            
        return current_user.tenant_id

    @staticmethod
    def validate_approval_creation(db: Session, request_id: int, target_tenant_id: int) -> VisitRequest:
        visit_req = db.query(VisitRequest).filter(
            VisitRequest.id == request_id,
            VisitRequest.tenant_id == target_tenant_id,
            VisitRequest.is_deleted == False
        ).first()

        if not visit_req:
            raise NotFoundException(f"Visit Request ID {request_id} not found for tenant {target_tenant_id}")

        if visit_req.status != VisitRequestStatus.PENDING:
            raise BusinessRuleException(f"Cannot create approval for Visit Request in status '{visit_req.status.value}' (Must be PENDING)")

        # Check existing active approval
        existing_approval = db.query(Approval).filter(
            Approval.tenant_id == target_tenant_id,
            Approval.request_id == request_id,
            Approval.status == ApprovalStatus.PENDING,
            Approval.is_deleted == False
        ).first()

        if existing_approval:
            raise BusinessRuleException(f"Visit Request ID {request_id} already has an active pending approval workflow (Code: {existing_approval.approval_code})")

        return visit_req

    @staticmethod
    def validate_pending_status(approval: Approval) -> None:
        if approval.status != ApprovalStatus.PENDING:
            raise BusinessRuleException(f"Cannot action approval workflow ID {approval.id} because its current status is '{approval.status.value}'")

    @staticmethod
    def validate_approval_action_authority(current_user: User, approval: Approval) -> None:
        if current_user.is_super_admin:
            return

        if current_user.tenant_id != approval.tenant_id:
            raise AuthorizationException("Access denied. Tenant boundary mismatch.")

        # User must be the assigned current approver, host, or have admin privilege
        is_assigned_approver = (current_user.id == approval.current_approver_id)
        is_host = (approval.visit_request and current_user.id == approval.visit_request.host_id)
        is_admin = False
        if hasattr(current_user, "role") and current_user.role:
            is_admin = current_user.role.name in ["TENANT_ADMIN", "SUPER_ADMIN", "RECEPTIONIST"]

        if not (is_assigned_approver or is_host or is_admin):
            raise AuthorizationException("Access denied. You are not authorized to action this approval step.")

    @staticmethod
    def validate_target_user(db: Session, target_tenant_id: int, target_user_id: int, role_label: str = "Target Approver") -> User:
        user = db.query(User).filter(
            User.id == target_user_id,
            User.tenant_id == target_tenant_id,
            User.is_active == True,
            User.is_deleted == False
        ).first()

        if not user:
            raise NotFoundException(f"{role_label} User ID {target_user_id} not found or inactive in tenant {target_tenant_id}")

        return user
