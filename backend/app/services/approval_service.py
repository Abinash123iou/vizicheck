from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.tenant import Tenant
from app.models.approval import Approval, ApprovalHistory, ApprovalStatus, ApprovalAction, ApprovalType
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.schemas.approval import (
    ApprovalCreate,
    ApprovalActionRequest,
    ApprovalResponse,
    ApprovalHistoryResponse,
    ApprovalStatsResponse
)
from app.repositories.approval_repository import ApprovalRepository
from app.validators.approval_validator import ApprovalValidator
from app.mappers.approval_mapper import ApprovalMapper
from app.repositories.audit_repository import AuditRepository
from app.constants.audit_actions import AuditActions
from app.core.exceptions import NotFoundException, BusinessRuleException
from app.services.pass_service import PassService
from app.utils.logger import get_logger

logger = get_logger("approval_service")


class ApprovalService:
    """
    Business logic orchestration service for Approval Workflow Engine.
    """

    MODULE_NAME = "APPROVAL_WORKFLOW_MANAGEMENT"

    @classmethod
    def _generate_approval_code(cls, db: Session, tenant_id: int) -> str:
        tenant = db.query(Tenant).filter_by(id=tenant_id).first()
        t_code = tenant.code if tenant else f"TEN-{tenant_id}"
        year = datetime.now().year
        
        count = db.query(Approval).filter(Approval.tenant_id == tenant_id).count() + 1
        return f"APP-{year}-{t_code}-{count:06d}"

    @classmethod
    def create_approval_workflow(
        cls,
        db: Session,
        current_user: User,
        data: ApprovalCreate
    ) -> ApprovalResponse:
        target_tenant_id = ApprovalValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=data.tenant_id
        )

        visit_req = ApprovalValidator.validate_approval_creation(
            db=db,
            request_id=data.request_id,
            target_tenant_id=target_tenant_id
        )

        # Default approver to host_id if not explicitly specified
        approver_id = data.current_approver_id or visit_req.host_id
        ApprovalValidator.validate_target_user(
            db=db,
            target_tenant_id=target_tenant_id,
            target_user_id=approver_id,
            role_label="Approver"
        )

        approval_code = cls._generate_approval_code(db=db, tenant_id=target_tenant_id)

        approval = Approval(
            tenant_id=target_tenant_id,
            request_id=data.request_id,
            approval_code=approval_code,
            approval_type=data.approval_type,
            current_step=1,
            total_steps=data.total_steps,
            current_approver_id=approver_id,
            status=ApprovalStatus.PENDING,
            expires_at=data.expires_at,
            notes=data.notes,
            created_by_id=current_user.id
        )

        created_approval = ApprovalRepository.create_approval(db=db, approval=approval)

        # Record Initial History Log
        history = ApprovalHistory(
            approval_id=created_approval.id,
            tenant_id=target_tenant_id,
            step_number=1,
            actor_id=current_user.id,
            action=ApprovalAction.CREATED,
            previous_status=ApprovalStatus.PENDING,
            new_status=ApprovalStatus.PENDING,
            comments=data.notes or "Approval workflow initialized"
        )
        ApprovalRepository.create_history_entry(db=db, history=history)

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.APPROVAL_CREATED,
            module=cls.MODULE_NAME,
            entity_id=created_approval.id,
            new_value={
                "approval_code": approval_code,
                "request_id": data.request_id,
                "approver_id": approver_id,
                "type": data.approval_type.value
            }
        )

        return ApprovalMapper.to_response(created_approval)

    @classmethod
    def action_approval(
        cls,
        db: Session,
        current_user: User,
        approval_id: int,
        action_data: ApprovalActionRequest
    ) -> ApprovalResponse:
        approval = ApprovalRepository.get_by_id(db=db, approval_id=approval_id)
        if not approval:
            raise NotFoundException(f"Approval workflow ID {approval_id} not found")

        ApprovalValidator.validate_tenant_boundary(current_user=current_user, target_tenant_id=approval.tenant_id)
        ApprovalValidator.validate_pending_status(approval)
        ApprovalValidator.validate_approval_action_authority(current_user=current_user, approval=approval)

        prev_status = approval.status
        action = action_data.action
        delegated_to_user_id = None

        if action == ApprovalAction.APPROVE:
            if approval.current_step >= approval.total_steps:
                # Final Approval
                approval.status = ApprovalStatus.APPROVED
                visit_req = approval.visit_request
                if visit_req:
                    visit_req.status = VisitRequestStatus.APPROVED
                    visit_req.approved_by = current_user.id
                    visit_req.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    visit_req.approval_notes = action_data.comments

                # Generate Visitor Pass & QR code automatically
                try:
                    PassService.generate_pass(
                        db=db,
                        current_user=current_user,
                        visit_request_id=approval.request_id
                    )
                    logger.info(f"Automatically generated visitor pass for visit request {approval.request_id}")
                except Exception as ex:
                    logger.warning(f"Pass generation note: {str(ex)}")
            else:
                # Intermediate Step Approval in Multi-Level Workflow
                approval.current_step += 1
                if action_data.target_user_id:
                    target_user = ApprovalValidator.validate_target_user(
                        db=db,
                        target_tenant_id=approval.tenant_id,
                        target_user_id=action_data.target_user_id,
                        role_label="Next Step Approver"
                    )
                    approval.current_approver_id = target_user.id

        elif action == ApprovalAction.REJECT:
            approval.status = ApprovalStatus.REJECTED
            visit_req = approval.visit_request
            if visit_req:
                visit_req.status = VisitRequestStatus.REJECTED
                visit_req.rejected_by = current_user.id
                visit_req.rejected_at = datetime.now(timezone.utc).replace(tzinfo=None)
                visit_req.rejection_reason = action_data.comments

        elif action == ApprovalAction.DELEGATE:
            if not action_data.target_user_id:
                raise BusinessRuleException("Target user ID must be provided when delegating an approval.")
            target_user = ApprovalValidator.validate_target_user(
                db=db,
                target_tenant_id=approval.tenant_id,
                target_user_id=action_data.target_user_id,
                role_label="Delegate"
            )
            approval.current_approver_id = target_user.id
            delegated_to_user_id = target_user.id
            approval.status = ApprovalStatus.DELEGATED

        elif action == ApprovalAction.ESCALATE:
            if not action_data.target_user_id:
                raise BusinessRuleException("Target user ID must be provided when escalating an approval.")
            target_user = ApprovalValidator.validate_target_user(
                db=db,
                target_tenant_id=approval.tenant_id,
                target_user_id=action_data.target_user_id,
                role_label="Escalation Manager"
            )
            approval.current_approver_id = target_user.id
            delegated_to_user_id = target_user.id
            approval.status = ApprovalStatus.ESCALATED

        elif action == ApprovalAction.CANCEL:
            approval.status = ApprovalStatus.CANCELLED
            visit_req = approval.visit_request
            if visit_req:
                visit_req.status = VisitRequestStatus.CANCELLED
                visit_req.cancelled_by = current_user.id
                visit_req.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
                visit_req.cancellation_reason = action_data.comments

        approval.updated_by_id = current_user.id
        updated_approval = ApprovalRepository.update_approval(db=db, approval=approval)

        # Log History Entry
        history = ApprovalHistory(
            approval_id=updated_approval.id,
            tenant_id=approval.tenant_id,
            step_number=approval.current_step,
            actor_id=current_user.id,
            action=action,
            previous_status=prev_status,
            new_status=updated_approval.status,
            comments=action_data.comments,
            delegated_to_id=delegated_to_user_id
        )
        ApprovalRepository.create_history_entry(db=db, history=history)

        # Audit Trail
        audit_action_map = {
            ApprovalAction.APPROVE: AuditActions.APPROVED,
            ApprovalAction.REJECT: AuditActions.REJECTED,
            ApprovalAction.DELEGATE: AuditActions.DELEGATED,
            ApprovalAction.ESCALATE: AuditActions.ESCALATED,
            ApprovalAction.CANCEL: AuditActions.CANCELLED
        }
        audit_act = audit_action_map.get(action, AuditActions.APPROVED)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=audit_act,
            module=cls.MODULE_NAME,
            entity_id=updated_approval.id,
            new_value={
                "approval_code": updated_approval.approval_code,
                "action": action.value,
                "new_status": updated_approval.status.value,
                "current_step": updated_approval.current_step
            }
        )

        return ApprovalMapper.to_response(updated_approval)

    @classmethod
    def get_approval_by_id(cls, db: Session, current_user: User, approval_id: int) -> ApprovalResponse:
        approval = ApprovalRepository.get_by_id(db=db, approval_id=approval_id)
        if not approval:
            raise NotFoundException(f"Approval workflow ID {approval_id} not found")

        ApprovalValidator.validate_tenant_boundary(current_user=current_user, target_tenant_id=approval.tenant_id)
        return ApprovalMapper.to_response(approval)

    @classmethod
    def list_approvals(
        cls,
        db: Session,
        current_user: User,
        tenant_id: Optional[int] = None,
        approver_id: Optional[int] = None,
        request_id: Optional[int] = None,
        status: Optional[ApprovalStatus] = None,
        approval_type: Optional[ApprovalType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ApprovalResponse], int]:
        target_tenant_id = ApprovalValidator.validate_tenant_boundary(current_user=current_user, target_tenant_id=tenant_id)

        items, total_count = ApprovalRepository.list_approvals(
            db=db,
            tenant_id=target_tenant_id,
            approver_id=approver_id,
            request_id=request_id,
            status=status,
            approval_type=approval_type,
            search=search,
            page=page,
            page_size=page_size
        )

        return ApprovalMapper.to_response_list(items), total_count

    @classmethod
    def get_approval_history(cls, db: Session, current_user: User, approval_id: int) -> List[ApprovalHistoryResponse]:
        approval = ApprovalRepository.get_by_id(db=db, approval_id=approval_id)
        if not approval:
            raise NotFoundException(f"Approval workflow ID {approval_id} not found")

        ApprovalValidator.validate_tenant_boundary(current_user=current_user, target_tenant_id=approval.tenant_id)
        histories = ApprovalRepository.get_approval_history(db=db, approval_id=approval_id)
        return ApprovalMapper.to_history_response_list(histories)

    @classmethod
    def get_approval_stats(cls, db: Session, current_user: User, tenant_id: Optional[int] = None) -> ApprovalStatsResponse:
        target_tenant_id = ApprovalValidator.validate_tenant_boundary(current_user=current_user, target_tenant_id=tenant_id)
        stats = ApprovalRepository.get_approval_stats(db=db, tenant_id=target_tenant_id)
        return ApprovalStatsResponse(**stats)

    @classmethod
    def expire_stale_approvals(cls, db: Session) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expired_list = ApprovalRepository.get_expired_pending_approvals(db=db, now=now)
        count = 0
        for app in expired_list:
            app.status = ApprovalStatus.EXPIRED
            if app.visit_request:
                app.visit_request.status = VisitRequestStatus.EXPIRED
            history = ApprovalHistory(
                approval_id=app.id,
                tenant_id=app.tenant_id,
                step_number=app.current_step,
                actor_id=app.current_approver_id,
                action=ApprovalAction.EXPIRE,
                previous_status=ApprovalStatus.PENDING,
                new_status=ApprovalStatus.EXPIRED,
                comments="Approval workflow automatically expired due to timeout"
            )
            db.add(history)
            count += 1
        db.commit()
        return count
