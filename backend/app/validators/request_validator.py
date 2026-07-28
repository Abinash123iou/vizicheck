from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.visitor import Visitor
from app.models.tenant import Tenant, TenantStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.core.exceptions import ValidationException, AuthorizationException, NotFoundException
from app.core.permissions import SystemRoles
from app.repositories.request_repository import RequestRepository

class RequestValidator:
    """
    Validation service providing strict business logic checks, tenant isolation enforcement,
    host & visitor eligibility, schedule sanity checks, duplicate overlap prevention, and state transitions.
    """

    @classmethod
    def validate_tenant_boundary(
        cls, 
        current_user: User, 
        request_tenant_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> int:
        """
        Verify tenant access boundary based on user role and ensure tenant is active.
        """
        if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN:
            target_tenant_id = request_tenant_id or current_user.tenant_id or 1
        else:
            if not current_user.tenant_id:
                raise AuthorizationException("Authenticated user is not assigned to any tenant organization")
            if request_tenant_id and request_tenant_id != current_user.tenant_id:
                raise AuthorizationException("Access denied. Cannot create or access visit requests outside your tenant organization")
            target_tenant_id = current_user.tenant_id

        if db is not None:
            tenant = db.query(Tenant).filter(Tenant.id == target_tenant_id).first()
            if not tenant:
                raise NotFoundException(f"Tenant with ID {target_tenant_id} not found")
            if tenant.status != TenantStatus.ACTIVE:
                raise ValidationException(f"Tenant organization '{tenant.name}' is not ACTIVE")

        return target_tenant_id

    @classmethod
    def validate_visitor_eligibility(cls, db: Session, visitor_id: int, tenant_id: int) -> Visitor:
        """
        Ensure visitor exists, belongs to tenant, is not soft-deleted, and is not blacklisted.
        """
        visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
        if not visitor or visitor.is_deleted:
            raise NotFoundException(f"Visitor with ID {visitor_id} not found")

        if visitor.tenant_id != tenant_id:
            raise AuthorizationException("Visitor does not belong to the current tenant organization")

        if visitor.blacklisted:
            reason_suffix = f": {visitor.blacklist_reason}" if visitor.blacklist_reason else "."
            raise ValidationException(f"Visitor '{visitor.first_name} {visitor.last_name}' is blacklisted and cannot be invited{reason_suffix}")

        return visitor

    @classmethod
    def validate_host_eligibility(cls, db: Session, host_id: int, tenant_id: int) -> User:
        """
        Ensure host user exists, belongs to tenant, is not soft-deleted, and is active.
        """
        host = db.query(User).filter(User.id == host_id).first()
        if not host or host.is_deleted:
            raise NotFoundException(f"Host employee with ID {host_id} not found")

        if host.tenant_id != tenant_id and host.role.name != SystemRoles.SUPER_ADMIN:
            raise AuthorizationException("Host employee does not belong to the current tenant organization")

        if not host.is_active:
            raise ValidationException(f"Host employee '{host.first_name} {host.last_name}' account is inactive")

        return host

    @classmethod
    def validate_scheduled_times(
        cls, 
        start_time: datetime, 
        end_time: datetime, 
        allow_past_override: bool = False
    ) -> None:
        """
        Validate scheduled visit window: start < end and start not in past.
        """
        start_naive = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
        end_naive = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time

        if end_naive <= start_naive:
            raise ValidationException("Scheduled end time must be after scheduled start time")

        now = datetime.now() - timedelta(minutes=5)  # 5-min buffer for clock drift
        if not allow_past_override and start_naive < now:
            raise ValidationException("Scheduled visit start time cannot be in the past")

    @classmethod
    def validate_no_overlapping_booking(
        cls, 
        db: Session, 
        tenant_id: int, 
        visitor_id: int, 
        start_time: datetime, 
        end_time: datetime, 
        exclude_id: Optional[int] = None
    ) -> None:
        """
        Ensure visitor does not already have an active/pending visit request overlapping with requested slot.
        """
        start_naive = start_time.replace(tzinfo=None) if start_time and start_time.tzinfo else start_time
        end_naive = end_time.replace(tzinfo=None) if end_time and end_time.tzinfo else end_time

        overlapping = RequestRepository.check_overlapping_request(
            db=db,
            tenant_id=tenant_id,
            visitor_id=visitor_id,
            start_time=start_naive,
            end_time=end_naive,
            exclude_id=exclude_id
        )
        if overlapping:
            raise ValidationException(
                f"Visitor already has an active visit request ({overlapping.request_code}) "
                f"overlapping between {overlapping.scheduled_start_time} and {overlapping.scheduled_end_time}"
            )

    @classmethod
    def validate_state_transition(
        cls, 
        visit_request: VisitRequest, 
        target_action: str, 
        rejection_reason: Optional[str] = None, 
        cancellation_reason: Optional[str] = None
    ) -> None:
        """
        Validate state machine transitions for approve, reject, cancel, restore.
        """
        current_status = visit_request.status

        if target_action == "APPROVE":
            if current_status != VisitRequestStatus.PENDING:
                raise ValidationException(f"Cannot approve request in '{current_status.value}' state. Only PENDING requests can be approved.")

        elif target_action == "REJECT":
            if current_status != VisitRequestStatus.PENDING:
                raise ValidationException(f"Cannot reject request in '{current_status.value}' state. Only PENDING requests can be rejected.")
            if not rejection_reason or not rejection_reason.strip():
                raise ValidationException("Rejection reason is required when rejecting a visit request")

        elif target_action == "CANCEL":
            if current_status not in [VisitRequestStatus.PENDING, VisitRequestStatus.APPROVED]:
                raise ValidationException(f"Cannot cancel request in '{current_status.value}' state. Only PENDING or APPROVED requests can be cancelled.")
            if not cancellation_reason or not cancellation_reason.strip():
                raise ValidationException("Cancellation reason is required when cancelling a visit request")

        elif target_action == "RESTORE":
            if not visit_request.is_deleted:
                raise ValidationException("Visit request is not deleted and cannot be restored")
