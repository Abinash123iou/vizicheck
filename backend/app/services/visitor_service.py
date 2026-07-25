from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.visitor import VisitorStatus, VerificationMethod
from app.constants.audit_actions import AuditActions
from app.core.exceptions import NotFoundException, ValidationException
from app.core.permissions import SystemRoles
from app.repositories.visitor_repository import VisitorRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.visitor_validator import VisitorValidator
from app.mappers.visitor_mapper import VisitorMapper
from app.services.export_service import ExportService
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

class VisitorService:
    """
    Business logic orchestration layer for Visitor Management.
    Handles CRUD operations, tenant boundary security, validation, export generation, and audit logging.
    """

    MODULE_NAME = "VISITOR_MANAGEMENT"

    @classmethod
    def create_visitor(
        cls,
        db: Session,
        current_user: User,
        request: CreateVisitorRequest,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Register a new visitor record. Validates tenant boundaries, phone/email format, and triple uniqueness.
        """
        target_tenant_id = VisitorValidator.validate_tenant_boundary(current_user, request.tenant_id, db=db)
        if not target_tenant_id:
            raise ValidationException("Tenant ID must be specified when creating a visitor as Super Admin (e.g. 'tenant_id': 1 in JSON body)")

        clean_phone = VisitorValidator.validate_phone(request.phone)
        clean_email = VisitorValidator.validate_email(request.email)
        VisitorValidator.validate_emergency_contact(request.emergency_contact_name, request.emergency_contact_phone)
        VisitorValidator.validate_date_of_birth(request.date_of_birth)

        VisitorValidator.validate_duplicate_visitor(
            db=db,
            tenant_id=target_tenant_id,
            phone=clean_phone,
            email=clean_email,
            government_id_number=request.government_id_number
        )

        visitor_data = request.model_dump()
        visitor_data["tenant_id"] = target_tenant_id
        visitor_data["phone"] = clean_phone
        visitor_data["email"] = clean_email

        visitor = VisitorRepository.create(db, visitor_data, creator_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_CREATED,
            module=cls.MODULE_NAME,
            entity_id=visitor.id,
            ip_address=ip_address,
            new_value={
                "visitor_code": visitor.visitor_code,
                "first_name": visitor.first_name,
                "last_name": visitor.last_name,
                "phone": visitor.phone,
                "tenant_id": visitor.tenant_id
            }
        )

        return VisitorMapper.to_visitor_response(visitor)

    @classmethod
    def get_visitor_by_id(cls, db: Session, current_user: User, visitor_id: int) -> VisitorResponse:
        """
        Retrieve details of a visitor by primary key ID.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)
        return VisitorMapper.to_visitor_response(visitor)

    @classmethod
    def get_visitor_by_code(cls, db: Session, current_user: User, visitor_code: str) -> VisitorResponse:
        """
        Retrieve visitor by tenant-aware visitor code.
        """
        effective_tenant_id = current_user.tenant_id if current_user.role and current_user.role.name != SystemRoles.SUPER_ADMIN else None
        visitor = VisitorRepository.find_by_code(db, visitor_code, tenant_id=effective_tenant_id)
        if not visitor:
            raise NotFoundException(f"Visitor with code '{visitor_code}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)
        return VisitorMapper.to_visitor_response(visitor)

    @classmethod
    def get_visitor_activity(cls, db: Session, current_user: User, visitor_id: int, limit: int = 50) -> List[VisitorActivityResponse]:
        """
        Retrieve audit activity timeline for a visitor entity.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id, include_deleted=True)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)
        logs = AuditRepository.get_entity_activity_timeline(db, module=cls.MODULE_NAME, entity_id=visitor_id, limit=limit)
        return VisitorMapper.to_activity_response_list(logs)

    @classmethod
    def list_visitors(
        cls,
        db: Session,
        current_user: User,
        params: VisitorPaginationRequest
    ) -> EnhancedPaginationResponse[VisitorResponse]:
        """
        Retrieve paginated visitors matching search and filter conditions with tenant boundary security.
        """
        effective_tenant_id = params.tenant_id
        if current_user.role and current_user.role.name != SystemRoles.SUPER_ADMIN:
            effective_tenant_id = current_user.tenant_id

        visitors, total_count = VisitorRepository.list_visitors_paginated(
            db=db,
            tenant_id=effective_tenant_id,
            search=params.search,
            phone=params.phone,
            email=params.email,
            company=params.company,
            government_id_number=params.government_id_number,
            visitor_code=params.visitor_code,
            status=params.status,
            verified=params.verified,
            blacklisted=params.blacklisted,
            created_from=params.created_from,
            created_to=params.created_to,
            is_deleted=params.is_deleted,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            order=params.order
        )

        return VisitorMapper.to_paginated_response(
            visitors=visitors,
            total_records=total_count,
            page=params.page,
            page_size=params.page_size
        )

    @classmethod
    def update_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        request: UpdateVisitorRequest,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Update visitor profile details.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)

        if request.phone:
            request.phone = VisitorValidator.validate_phone(request.phone)
        if request.email:
            request.email = VisitorValidator.validate_email(request.email)
        if request.emergency_contact_phone:
            VisitorValidator.validate_emergency_contact(request.emergency_contact_name, request.emergency_contact_phone)
        if request.date_of_birth:
            VisitorValidator.validate_date_of_birth(request.date_of_birth)

        # Check duplicate if phone, email or gov ID changed
        phone_to_check = request.phone if request.phone else visitor.phone
        email_to_check = request.email if request.email else visitor.email
        gov_to_check = request.government_id_number if request.government_id_number else visitor.government_id_number

        VisitorValidator.validate_duplicate_visitor(
            db=db,
            tenant_id=visitor.tenant_id,
            phone=phone_to_check,
            email=email_to_check,
            government_id_number=gov_to_check,
            exclude_visitor_id=visitor.id
        )

        old_value = {
            "first_name": visitor.first_name,
            "last_name": visitor.last_name,
            "phone": visitor.phone,
            "email": visitor.email,
            "company": visitor.company
        }

        update_data = request.model_dump(exclude_unset=True)
        updated_visitor = VisitorRepository.update(db, visitor, update_data, updater_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_UPDATED,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value=old_value,
            new_value=update_data
        )

        return VisitorMapper.to_visitor_response(updated_visitor)

    @classmethod
    def soft_delete_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Soft delete visitor record.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)

        VisitorRepository.soft_delete(db, visitor, deleter_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_DELETED,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value={"visitor_code": visitor.visitor_code, "is_deleted": False},
            new_value={"is_deleted": True}
        )

    @classmethod
    def restore_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Restore soft-deleted visitor record.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id, include_deleted=True)
        if not visitor or not visitor.is_deleted:
            raise NotFoundException(f"Soft-deleted visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)

        restored_visitor = VisitorRepository.restore(db, visitor, updater_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_RESTORED,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value={"is_deleted": True},
            new_value={"is_deleted": False}
        )

        return VisitorMapper.to_visitor_response(restored_visitor)

    @classmethod
    def verify_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        request: VerifyVisitorRequest,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Verify visitor identity proof/profile.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)
        VisitorValidator.validate_blacklist_rules(visitor, "verify")

        verified_visitor = VisitorRepository.verify_visitor(
            db=db,
            visitor=visitor,
            verification_method=request.verification_method,
            verifier_id=current_user.id,
            notes=request.notes
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_VERIFIED,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value={"verified": False},
            new_value={"verified": True, "method": request.verification_method.value}
        )

        return VisitorMapper.to_visitor_response(verified_visitor)

    @classmethod
    def blacklist_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        request: BlacklistVisitorRequest,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Blacklist a visitor record with mandatory/optional reason.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)

        if request.blacklisted and not request.reason:
            raise ValidationException("A valid reason must be provided when blacklisting a visitor")

        updated_visitor = VisitorRepository.blacklist_visitor(
            db=db,
            visitor=visitor,
            blacklisted=request.blacklisted,
            reason=request.reason,
            updater_id=current_user.id
        )

        action = AuditActions.VISITOR_BLACKLISTED if request.blacklisted else AuditActions.VISITOR_BLACKLIST_REMOVED

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=action,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value={"blacklisted": visitor.blacklisted},
            new_value={"blacklisted": request.blacklisted, "reason": request.reason}
        )

        return VisitorMapper.to_visitor_response(updated_visitor)

    @classmethod
    def remove_blacklist(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Remove blacklist status from a visitor.
        """
        req = BlacklistVisitorRequest(blacklisted=False, reason=None)
        return cls.blacklist_visitor(db, current_user, visitor_id, req, ip_address)

    @classmethod
    def activate_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Activate visitor record.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)
        VisitorValidator.validate_blacklist_rules(visitor, "activate")

        updated_visitor = VisitorRepository.update_status(db, visitor, VisitorStatus.ACTIVE, updater_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_ACTIVATED,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value={"status": visitor.status.value},
            new_value={"status": VisitorStatus.ACTIVE.value}
        )

        return VisitorMapper.to_visitor_response(updated_visitor)

    @classmethod
    def deactivate_visitor(
        cls,
        db: Session,
        current_user: User,
        visitor_id: int,
        ip_address: Optional[str] = None
    ) -> VisitorResponse:
        """
        Deactivate visitor record.
        """
        visitor = VisitorRepository.find_by_id(db, visitor_id)
        if not visitor:
            raise NotFoundException(f"Visitor with ID '{visitor_id}' not found")

        VisitorValidator.validate_visitor_access(current_user, visitor)

        updated_visitor = VisitorRepository.update_status(db, visitor, VisitorStatus.INACTIVE, updater_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISITOR_DEACTIVATED,
            module=cls.MODULE_NAME,
            entity_id=visitor_id,
            ip_address=ip_address,
            old_value={"status": visitor.status.value},
            new_value={"status": VisitorStatus.INACTIVE.value}
        )

        return VisitorMapper.to_visitor_response(updated_visitor)

    @classmethod
    def get_statistics(
        cls,
        db: Session,
        current_user: User,
        tenant_id: Optional[int] = None
    ) -> VisitorStatisticsResponse:
        """
        Retrieve dashboard statistics for visitor management.
        """
        effective_tenant_id = VisitorValidator.validate_tenant_boundary(current_user, tenant_id)
        stats = VisitorRepository.get_statistics(db, tenant_id=effective_tenant_id)
        return VisitorMapper.to_statistics_response(stats)

    @classmethod
    def export_visitors_csv(
        cls,
        db: Session,
        current_user: User,
        search: Optional[str] = None,
        status: Optional[VisitorStatus] = None,
        verified: Optional[bool] = None,
        blacklisted: Optional[bool] = None,
        is_deleted: bool = False
    ) -> str:
        """
        Export visitor list matching filter parameters as a CSV payload.
        """
        effective_tenant_id = current_user.tenant_id if current_user.role and current_user.role.name != SystemRoles.SUPER_ADMIN else None
        visitors = VisitorRepository.get_all_visitors_for_export(
            db=db,
            tenant_id=effective_tenant_id,
            search=search,
            status=status,
            verified=verified,
            blacklisted=blacklisted,
            is_deleted=is_deleted
        )
        return ExportService.export_visitors_csv(visitors)
