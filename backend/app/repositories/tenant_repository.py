from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_settings import TenantSettings
from app.models.user import User
from app.repositories.specifications.tenant_filters import TenantFilters

class TenantRepository:
    """
    Database access layer for Tenant and TenantSettings entities.
    """

    @staticmethod
    def generate_next_code(db: Session) -> str:
        """
        Generate next unique sequential tenant code (e.g. TEN-000001).
        """
        max_id_query = db.query(func.max(Tenant.id)).scalar() or 0
        next_id = max_id_query + 1
        return f"TEN-{next_id:06d}"

    @staticmethod
    def find_by_id(db: Session, tenant_id: int, include_deleted: bool = False) -> Optional[Tenant]:
        """
        Find tenant by ID with eagerly loaded settings.
        """
        query = db.query(Tenant).options(joinedload(Tenant.settings)).filter(Tenant.id == tenant_id)
        if not include_deleted:
            query = query.filter(Tenant.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_code(db: Session, code: str, include_deleted: bool = True) -> Optional[Tenant]:
        """
        Find tenant by code.
        """
        query = db.query(Tenant).filter(Tenant.code == code.strip().upper())
        if not include_deleted:
            query = query.filter(Tenant.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_name(db: Session, name: str, include_deleted: bool = True) -> Optional[Tenant]:
        """
        Find tenant by name.
        """
        query = db.query(Tenant).filter(Tenant.name.ilike(name.strip()))
        if not include_deleted:
            query = query.filter(Tenant.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_slug(db: Session, slug: str, include_deleted: bool = True) -> Optional[Tenant]:
        """
        Find tenant by slug.
        """
        query = db.query(Tenant).filter(Tenant.slug == slug.strip().lower())
        if not include_deleted:
            query = query.filter(Tenant.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_domain(db: Session, domain: str, include_deleted: bool = True) -> Optional[Tenant]:
        """
        Find tenant by custom domain.
        """
        query = db.query(Tenant).filter(Tenant.domain == domain.strip().lower())
        if not include_deleted:
            query = query.filter(Tenant.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def create(db: Session, tenant_data: dict, settings_data: Optional[dict] = None, creator_id: Optional[int] = None) -> Tenant:
        """
        Persist a new Tenant entity along with its TenantSettings.
        """
        if "code" not in tenant_data or not tenant_data["code"]:
            tenant_data["code"] = TenantRepository.generate_next_code(db)

        tenant = Tenant(**tenant_data, created_by_id=creator_id)
        db.add(tenant)
        db.flush()

        settings_payload = settings_data or {}
        settings = TenantSettings(tenant_id=tenant.id, **settings_payload)
        db.add(settings)

        db.commit()
        db.refresh(tenant)
        return TenantRepository.find_by_id(db, tenant.id, include_deleted=True) or tenant

    @staticmethod
    def update(
        db: Session, 
        tenant: Tenant, 
        update_data: dict, 
        settings_data: Optional[dict] = None, 
        updater_id: Optional[int] = None
    ) -> Tenant:
        """
        Update Tenant fields and associated TenantSettings.
        """
        for key, value in update_data.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)

        tenant.updated_by_id = updater_id
        tenant.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        if settings_data and tenant.settings:
            for s_key, s_value in settings_data.items():
                if hasattr(tenant.settings, s_key) and s_value is not None:
                    setattr(tenant.settings, s_key, s_value)
            tenant.settings.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        elif settings_data and not tenant.settings:
            new_settings = TenantSettings(tenant_id=tenant.id, **settings_data)
            db.add(new_settings)

        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return TenantRepository.find_by_id(db, tenant.id, include_deleted=True) or tenant

    @staticmethod
    def soft_delete(db: Session, tenant: Tenant, deleter_id: Optional[int] = None) -> Tenant:
        """
        Soft delete tenant record.
        """
        tenant.delete()
        tenant.deleted_by_id = deleter_id
        tenant.updated_by_id = deleter_id
        tenant.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def restore(db: Session, tenant: Tenant, updater_id: Optional[int] = None) -> Tenant:
        """
        Restore soft-deleted tenant record.
        """
        tenant.restore()
        tenant.deleted_by_id = None
        tenant.updated_by_id = updater_id
        tenant.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def update_status(db: Session, tenant: Tenant, status: TenantStatus, updater_id: Optional[int] = None) -> Tenant:
        """
        Update tenant status (ACTIVE, SUSPENDED, etc.).
        """
        tenant.status = status
        tenant.updated_by_id = updater_id
        tenant.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def list_tenants_paginated(
        db: Session,
        search: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        is_deleted: bool = False,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> Tuple[List[Tenant], int]:
        """
        Retrieve paginated tenants with dynamic filter specifications and total count.
        """
        base_query = db.query(Tenant).options(joinedload(Tenant.settings))

        filtered_query = TenantFilters.apply_filters(
            query=base_query,
            search=search,
            status=status,
            is_deleted=is_deleted
        )

        total_records = filtered_query.count()
        sorted_query = TenantFilters.apply_sorting(filtered_query, sort_by=sort_by, order=order)

        offset = (page - 1) * page_size
        paginated_tenants = sorted_query.offset(offset).limit(page_size).all()

        return paginated_tenants, total_records

    @staticmethod
    def get_all_tenants(
        db: Session,
        search: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        is_deleted: bool = False
    ) -> List[Tenant]:
        """
        Retrieve all matching tenants for CSV/Excel export.
        """
        base_query = db.query(Tenant).options(joinedload(Tenant.settings))
        filtered_query = TenantFilters.apply_filters(
            query=base_query,
            search=search,
            status=status,
            is_deleted=is_deleted
        )
        return TenantFilters.apply_sorting(filtered_query).all()

    @staticmethod
    def get_tenant_user_count(db: Session, tenant_id: int) -> int:
        """
        Get count of all non-deleted users belonging to a tenant.
        """
        return db.query(User).filter(
            User.tenant_id == tenant_id,
            User.is_deleted.is_(False)
        ).count()

    @staticmethod
    def get_active_user_count(db: Session, tenant_id: int) -> int:
        """
        Get count of active users belonging to a tenant.
        """
        return db.query(User).filter(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
            User.is_deleted.is_(False)
        ).count()

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """
        Gather system-wide statistics for tenants, users, and activities.
        """
        total_tenants = db.query(Tenant).filter(Tenant.is_deleted.is_(False)).count()
        active_tenants = db.query(Tenant).filter(Tenant.status == TenantStatus.ACTIVE, Tenant.is_deleted.is_(False)).count()
        inactive_tenants = db.query(Tenant).filter(Tenant.status == TenantStatus.INACTIVE, Tenant.is_deleted.is_(False)).count()
        pending_tenants = db.query(Tenant).filter(Tenant.status == TenantStatus.PENDING, Tenant.is_deleted.is_(False)).count()
        suspended_tenants = db.query(Tenant).filter(Tenant.status == TenantStatus.SUSPENDED, Tenant.is_deleted.is_(False)).count()
        archived_tenants = db.query(Tenant).filter(Tenant.status == TenantStatus.ARCHIVED, Tenant.is_deleted.is_(False)).count()
        deleted_tenants = db.query(Tenant).filter(Tenant.is_deleted.is_(True)).count()

        total_users = db.query(User).filter(User.is_deleted.is_(False)).count()
        
        # Security Officers count
        from app.models.role import Role
        so_role = db.query(Role).filter_by(name="SECURITY_OFFICER").first()
        so_count = db.query(User).filter(User.role_id == so_role.id, User.is_deleted.is_(False)).count() if so_role else 0

        return {
            "tenant_overview": {
                "total": total_tenants,
                "active": active_tenants,
                "inactive": inactive_tenants,
                "pending": pending_tenants,
                "suspended": suspended_tenants,
                "archived": archived_tenants,
                "deleted": deleted_tenants,
            },
            "user_stats": {
                "total_users": total_users,
                "security_officers": so_count,
            },
            "visitor_stats": {
                "total_visitors": 0,
                "today_visitors": 0,
                "check_ins": 0,
                "check_outs": 0,
            },
            "request_stats": {
                "pending_requests": 0,
                "approved_requests": 0,
                "rejected_requests": 0,
            },
            "pass_stats": {
                "passes_generated": 0,
            }
        }
