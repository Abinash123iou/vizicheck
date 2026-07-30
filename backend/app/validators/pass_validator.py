from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.core.exceptions import ValidationException, AuthorizationException, NotFoundException, ConflictException
from app.core.permissions import SystemRoles
from app.repositories.pass_repository import PassRepository


class PassValidator:
    """
    Validation service providing strict business logic checks, tenant boundary isolation,
    duplicate pass prevention, validity window sanity, and state machine transitions.
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
            if request_tenant_id:
                target_tenant_id = request_tenant_id
            elif current_user.tenant_id:
                target_tenant_id = current_user.tenant_id
            elif db is not None:
                active_tenant = db.query(Tenant).filter(Tenant.status == TenantStatus.ACTIVE).first()
                if not active_tenant:
                    active_tenant = db.query(Tenant).first()
                if active_tenant:
                    target_tenant_id = active_tenant.id
                else:
                    raise NotFoundException("No tenant organization exists in database. Please create a tenant first.")
            else:
                target_tenant_id = 1
        else:
            if not current_user.tenant_id:
                raise AuthorizationException("Authenticated user is not assigned to any tenant organization")
            if request_tenant_id and request_tenant_id != current_user.tenant_id:
                raise AuthorizationException("Access denied. Cannot access passes outside your tenant organization")
            target_tenant_id = current_user.tenant_id

        if db is not None:
            tenant = db.query(Tenant).filter(Tenant.id == target_tenant_id).first()
            if not tenant:
                raise NotFoundException(f"Tenant with ID {target_tenant_id} not found")
            if tenant.status != TenantStatus.ACTIVE:
                raise ValidationException(f"Tenant organization '{tenant.name}' is not ACTIVE")

        return target_tenant_id


    @classmethod
    def validate_visit_request_for_pass(cls, db: Session, visit_request_id: int, tenant_id: int) -> VisitRequest:
        """
        Ensure visit request exists, belongs to tenant, and is in APPROVED status.
        """
        visit_request = db.query(VisitRequest).filter(VisitRequest.id == visit_request_id).first()
        if not visit_request or visit_request.is_deleted:
            raise NotFoundException(f"Visit request with ID {visit_request_id} not found")

        if visit_request.tenant_id != tenant_id:
            raise AuthorizationException("Visit request does not belong to your tenant organization")

        if visit_request.status != VisitRequestStatus.APPROVED:
            raise ValidationException(
                f"Cannot generate pass for visit request '{visit_request.request_code}'. "
                f"Request status is '{visit_request.status.value}', but must be 'APPROVED'."
            )

        return visit_request

    @classmethod
    def validate_no_duplicate_pass(cls, db: Session, visit_request_id: int, tenant_id: int) -> None:
        """
        Prevent duplicate pass creation for an approved visit request.
        Raises 409 Conflict if an active, pending, or used pass already exists.
        """
        existing_pass = PassRepository.find_active_existing_pass_for_request(
            db=db, 
            visit_request_id=visit_request_id, 
            tenant_id=tenant_id
        )
        if existing_pass:
            raise ConflictException(
                f"Pass Already Exists: An active visitor pass ({existing_pass.pass_code}) "
                f"in '{existing_pass.status.value}' state already exists for Visit Request ID {visit_request_id}."
            )

    @classmethod
    def validate_pass_validity_times(
        cls, 
        valid_from: datetime, 
        valid_until: datetime
    ) -> None:
        """
        Validate pass validity window sanity.
        """
        vf_naive = valid_from.replace(tzinfo=None) if valid_from.tzinfo else valid_from
        vu_naive = valid_until.replace(tzinfo=None) if valid_until.tzinfo else valid_until

        if vu_naive <= vf_naive:
            raise ValidationException("Pass valid_until timestamp must be strictly after valid_from timestamp")

    @classmethod
    def validate_state_transition(
        cls, 
        visitor_pass: VisitorPass, 
        target_action: str, 
        revocation_reason: Optional[str] = None
    ) -> None:
        """
        Validate state machine transitions for pass operations (REVOKE, UPDATE, REGENERATE, RESTORE).
        """
        current_status = visitor_pass.status

        if target_action == "REVOKE":
            if current_status in [PassStatus.COMPLETED, PassStatus.REVOKED, PassStatus.EXPIRED]:
                raise ValidationException(f"Cannot revoke pass in '{current_status.value}' state. Pass is already terminated.")
            if not revocation_reason or not revocation_reason.strip():
                raise ValidationException("Revocation reason is required when revoking a visitor pass")

        elif target_action == "UPDATE":
            if current_status in [PassStatus.COMPLETED, PassStatus.REVOKED, PassStatus.EXPIRED]:
                raise ValidationException(f"Cannot update pass details in '{current_status.value}' state.")

        elif target_action == "REGENERATE_QR":
            if current_status != PassStatus.ACTIVE:
                raise ValidationException(f"Cannot regenerate QR token for pass in '{current_status.value}' state. Pass must be ACTIVE.")

        elif target_action == "RESTORE":
            if not visitor_pass.is_deleted:
                raise ValidationException("Visitor pass is not deleted and cannot be restored")
