from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.tenant import TenantStatus
from app.constants.roles import Roles
from app.constants.audit_actions import AuditActions
from app.core.exceptions import (
    NotFoundException, 
    AuthorizationException, 
    ValidationException
)
from app.repositories.tenant_repository import TenantRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.tenant_validator import TenantValidator
from app.mappers.tenant_mapper import TenantMapper
from app.services.export_service import ExportService
from app.schemas.tenant import (
    CreateTenantRequest,
    UpdateTenantRequest,
    TenantResponse,
    TenantPaginationRequest,
    EnhancedPaginationResponse,
    TenantStatisticsResponse,
    TenantActivityResponse
)

class TenantService:
    """
    Business logic layer for Tenant Management System incorporating
    uniqueness validations, tenant isolation, audit logging, export, and analytics.
    """

    @classmethod
    def verify_super_admin(cls, current_user: User) -> None:
        """
        Verify that caller possesses Super Admin privileges for administrative mutations.
        """
        is_super_admin = current_user.role and current_user.role.name == Roles.SUPER_ADMIN
        if not is_super_admin:
            raise AuthorizationException("Action requires Super Admin privileges")

    @classmethod
    def verify_tenant_access(cls, current_user: User, target_tenant_id: int) -> None:
        """
        Enforce strict multi-tenant isolation.
        Non-Super Admin users can only access their assigned tenant.
        """
        is_super_admin = current_user.role and current_user.role.name == Roles.SUPER_ADMIN
        if not is_super_admin:
            if current_user.tenant_id != target_tenant_id:
                raise AuthorizationException("Access denied. You can only manage your own organization")

    @classmethod
    def create_tenant(
        cls,
        db: Session,
        current_user: User,
        request: CreateTenantRequest,
        ip_address: Optional[str] = None
    ) -> TenantResponse:
        """
        Create a new tenant organization after validating uniqueness rules.
        """
        cls.verify_super_admin(current_user)

        normalized_email = TenantValidator.validate_company_email(request.contact_email)
        normalized_name = TenantValidator.validate_name_uniqueness(db, request.name)
        normalized_slug = TenantValidator.validate_slug_uniqueness(db, request.slug)
        normalized_domain = TenantValidator.validate_domain_uniqueness(db, request.domain)

        tenant_data = {
            "name": normalized_name,
            "slug": normalized_slug,
            "domain": normalized_domain,
            "description": request.description,
            "contact_person": request.contact_person,
            "contact_email": normalized_email,
            "contact_phone": request.contact_phone,
            "status": TenantStatus.ACTIVE
        }

        settings_data = request.settings.model_dump() if request.settings else None

        tenant = TenantRepository.create(
            db=db, 
            tenant_data=tenant_data, 
            settings_data=settings_data, 
            creator_id=current_user.id
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.TENANT_CREATED,
            module="TENANT_MANAGEMENT",
            entity_id=tenant.id,
            ip_address=ip_address,
            new_value={"code": tenant.code, "name": tenant.name, "contact_email": tenant.contact_email}
        )

        user_count = TenantRepository.get_tenant_user_count(db, tenant.id)
        return TenantMapper.to_tenant_response(tenant, user_count)

    @classmethod
    def get_tenant_by_id(cls, db: Session, current_user: User, tenant_id: int) -> TenantResponse:
        """
        Retrieve tenant by ID after enforcing access authorization.
        """
        cls.verify_tenant_access(current_user, tenant_id)

        tenant = TenantRepository.find_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundException(f"Tenant organization with ID '{tenant_id}' not found")

        user_count = TenantRepository.get_tenant_user_count(db, tenant.id)
        return TenantMapper.to_tenant_response(tenant, user_count)

    @classmethod
    def list_tenants(
        cls,
        db: Session,
        current_user: User,
        params: TenantPaginationRequest
    ) -> EnhancedPaginationResponse[TenantResponse]:
        """
        Retrieve paginated list of tenants filtered by search, status, and soft-delete flag.
        Enforces tenant isolation for non-Super Admin callers.
        """
        is_super_admin = current_user.role and current_user.role.name == Roles.SUPER_ADMIN
        
        # If caller is not Super Admin, force search to caller's own tenant
        if not is_super_admin:
            tenant = TenantRepository.find_by_id(db, current_user.tenant_id or 0)
            tenants = [tenant] if tenant else []
            total_records = len(tenants)
            user_counts_map = {t.id: TenantRepository.get_tenant_user_count(db, t.id) for t in tenants}
            return TenantMapper.to_paginated_response(
                tenants=tenants,
                user_counts_map=user_counts_map,
                total_records=total_records,
                page=1,
                page_size=params.page_size
            )

        tenants, total_records = TenantRepository.list_tenants_paginated(
            db=db,
            search=params.search,
            status=params.status,
            is_deleted=params.is_deleted,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            order=params.order
        )

        user_counts_map = {t.id: TenantRepository.get_tenant_user_count(db, t.id) for t in tenants}

        return TenantMapper.to_paginated_response(
            tenants=tenants,
            user_counts_map=user_counts_map,
            total_records=total_records,
            page=params.page,
            page_size=params.page_size
        )

    @classmethod
    def update_tenant(
        cls,
        db: Session,
        current_user: User,
        tenant_id: int,
        request: UpdateTenantRequest,
        ip_address: Optional[str] = None
    ) -> TenantResponse:
        """
        Update details and settings of a tenant organization.
        """
        cls.verify_tenant_access(current_user, tenant_id)

        tenant = TenantRepository.find_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundException(f"Tenant organization with ID '{tenant_id}' not found")

        update_data = {}
        if request.name is not None:
            update_data["name"] = TenantValidator.validate_name_uniqueness(db, request.name, exclude_tenant_id=tenant_id)
        if request.slug is not None:
            update_data["slug"] = TenantValidator.validate_slug_uniqueness(db, request.slug, exclude_tenant_id=tenant_id)
        if request.domain is not None:
            update_data["domain"] = TenantValidator.validate_domain_uniqueness(db, request.domain, exclude_tenant_id=tenant_id)
        if request.contact_email is not None:
            update_data["contact_email"] = TenantValidator.validate_company_email(request.contact_email)
        if request.contact_person is not None:
            update_data["contact_person"] = request.contact_person
        if request.contact_phone is not None:
            update_data["contact_phone"] = request.contact_phone
        if request.description is not None:
            update_data["description"] = request.description

        settings_data = request.settings.model_dump(exclude_unset=True) if request.settings else None

        old_value = {
            "name": tenant.name,
            "contact_email": tenant.contact_email,
            "status": tenant.status.value
        }

        updated_tenant = TenantRepository.update(
            db=db,
            tenant=tenant,
            update_data=update_data,
            settings_data=settings_data,
            updater_id=current_user.id
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.TENANT_UPDATED,
            module="TENANT_MANAGEMENT",
            entity_id=updated_tenant.id,
            ip_address=ip_address,
            old_value=old_value,
            new_value=update_data
        )

        user_count = TenantRepository.get_tenant_user_count(db, updated_tenant.id)
        return TenantMapper.to_tenant_response(updated_tenant, user_count)

    @classmethod
    def activate_tenant(
        cls,
        db: Session,
        current_user: User,
        tenant_id: int,
        ip_address: Optional[str] = None
    ) -> TenantResponse:
        """
        Activate suspended or pending tenant account.
        """
        cls.verify_super_admin(current_user)

        tenant = TenantRepository.find_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundException(f"Tenant organization with ID '{tenant_id}' not found")

        TenantValidator.validate_status_transition(tenant.status, TenantStatus.ACTIVE)

        old_status = tenant.status.value
        updated_tenant = TenantRepository.update_status(
            db=db, 
            tenant=tenant, 
            status=TenantStatus.ACTIVE, 
            updater_id=current_user.id
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.TENANT_ACTIVATED,
            module="TENANT_MANAGEMENT",
            entity_id=tenant_id,
            ip_address=ip_address,
            old_value={"status": old_status},
            new_value={"status": TenantStatus.ACTIVE.value}
        )

        user_count = TenantRepository.get_tenant_user_count(db, updated_tenant.id)
        return TenantMapper.to_tenant_response(updated_tenant, user_count)

    @classmethod
    def suspend_tenant(
        cls,
        db: Session,
        current_user: User,
        tenant_id: int,
        ip_address: Optional[str] = None
    ) -> TenantResponse:
        """
        Suspend active tenant organization.
        """
        cls.verify_super_admin(current_user)

        tenant = TenantRepository.find_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundException(f"Tenant organization with ID '{tenant_id}' not found")

        old_status = tenant.status.value
        updated_tenant = TenantRepository.update_status(
            db=db, 
            tenant=tenant, 
            status=TenantStatus.SUSPENDED, 
            updater_id=current_user.id
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.TENANT_SUSPENDED,
            module="TENANT_MANAGEMENT",
            entity_id=tenant_id,
            ip_address=ip_address,
            old_value={"status": old_status},
            new_value={"status": TenantStatus.SUSPENDED.value}
        )

        user_count = TenantRepository.get_tenant_user_count(db, updated_tenant.id)
        return TenantMapper.to_tenant_response(updated_tenant, user_count)

    @classmethod
    def soft_delete_tenant(
        cls,
        db: Session,
        current_user: User,
        tenant_id: int,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Soft delete tenant organization after safety checks.
        """
        cls.verify_super_admin(current_user)

        tenant = TenantRepository.find_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundException(f"Tenant organization with ID '{tenant_id}' not found")

        TenantValidator.validate_deletion_safety(db, tenant)

        TenantRepository.soft_delete(db=db, tenant=tenant, deleter_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.TENANT_DELETED,
            module="TENANT_MANAGEMENT",
            entity_id=tenant_id,
            ip_address=ip_address,
            old_value={"name": tenant.name, "is_deleted": False},
            new_value={"is_deleted": True}
        )

    @classmethod
    def restore_tenant(
        cls,
        db: Session,
        current_user: User,
        tenant_id: int,
        ip_address: Optional[str] = None
    ) -> TenantResponse:
        """
        Restore soft-deleted tenant account.
        """
        cls.verify_super_admin(current_user)

        tenant = TenantRepository.find_by_id(db, tenant_id, include_deleted=True)
        if not tenant or not tenant.is_deleted:
            raise NotFoundException(f"Soft-deleted tenant organization with ID '{tenant_id}' not found")

        restored_tenant = TenantRepository.restore(db=db, tenant=tenant, updater_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.TENANT_RESTORED,
            module="TENANT_MANAGEMENT",
            entity_id=tenant_id,
            ip_address=ip_address,
            old_value={"is_deleted": True},
            new_value={"is_deleted": False}
        )

        user_count = TenantRepository.get_tenant_user_count(db, restored_tenant.id)
        return TenantMapper.to_tenant_response(restored_tenant, user_count)

    @classmethod
    def get_statistics(cls, db: Session, current_user: User) -> TenantStatisticsResponse:
        """
        Retrieve system dashboard metrics across all tenants.
        """
        cls.verify_super_admin(current_user)
        stats_dict = TenantRepository.get_statistics(db)
        return TenantMapper.to_statistics_response(stats_dict)

    @classmethod
    def export_tenants_csv(
        cls,
        db: Session,
        current_user: User,
        search: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        is_deleted: bool = False
    ) -> str:
        """
        Generate CSV string containing tenant records.
        """
        cls.verify_super_admin(current_user)
        tenants = TenantRepository.get_all_tenants(db, search=search, status=status, is_deleted=is_deleted)

        headers = ["ID", "Code", "Name", "Slug", "Domain", "Contact Person", "Contact Email", "Contact Phone", "Status", "Created At"]
        rows = [
            {
                "ID": t.id,
                "Code": t.code,
                "Name": t.name,
                "Slug": t.slug or "",
                "Domain": t.domain or "",
                "Contact Person": t.contact_person,
                "Contact Email": t.contact_email,
                "Contact Phone": t.contact_phone or "",
                "Status": t.status.value,
                "Created At": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
            }
            for t in tenants
        ]

        return ExportService.generate_csv(headers, rows)

    @classmethod
    def get_activity_timeline(
        cls,
        db: Session,
        current_user: User,
        tenant_id: int,
        limit: int = 50
    ) -> List[TenantActivityResponse]:
        """
        Retrieve activity log history for a specific tenant.
        """
        cls.verify_tenant_access(current_user, tenant_id)

        tenant = TenantRepository.find_by_id(db, tenant_id)
        if not tenant:
            raise NotFoundException(f"Tenant organization with ID '{tenant_id}' not found")

        audit_logs = AuditRepository.get_entity_activity_timeline(
            db=db, 
            module="TENANT_MANAGEMENT", 
            entity_id=tenant_id, 
            limit=limit
        )

        return [TenantMapper.to_activity_response(log) for log in audit_logs]
