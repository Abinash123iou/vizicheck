import re
from typing import Optional
from sqlalchemy.orm import Session
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.core.exceptions import (
    ValidationException, 
    ConflictException, 
    BusinessRuleException
)

class TenantValidator:
    """
    Validation layer for Tenant business rules and uniqueness constraints.
    """

    @staticmethod
    def validate_company_email(email: str) -> str:
        """
        Verify email format and normalize.
        """
        if not email or "@" not in email:
            raise ValidationException("Invalid company contact email format")
        return email.strip().lower()

    @staticmethod
    def validate_name_uniqueness(db: Session, name: str, exclude_tenant_id: Optional[int] = None) -> str:
        """
        Ensure tenant name is unique across all organizations.
        """
        normalized_name = name.strip()
        existing = db.query(Tenant).filter(Tenant.name.ilike(normalized_name)).first()

        if existing and (exclude_tenant_id is None or existing.id != exclude_tenant_id):
            raise ConflictException(f"A tenant with the name '{normalized_name}' already exists")

        return normalized_name

    @staticmethod
    def validate_slug_uniqueness(db: Session, slug: Optional[str], exclude_tenant_id: Optional[int] = None) -> Optional[str]:
        """
        Ensure slug is unique and properly formatted if provided.
        """
        if not slug or not slug.strip():
            return None

        normalized_slug = slug.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", normalized_slug):
            raise ValidationException("Slug must contain only lowercase alphanumeric characters and hyphens")

        existing = db.query(Tenant).filter(Tenant.slug == normalized_slug).first()
        if existing and (exclude_tenant_id is None or existing.id != exclude_tenant_id):
            raise ConflictException(f"A tenant with the slug '{normalized_slug}' already exists")

        return normalized_slug

    @staticmethod
    def validate_domain_uniqueness(db: Session, domain: Optional[str], exclude_tenant_id: Optional[int] = None) -> Optional[str]:
        """
        Ensure custom domain is unique and valid format if provided.
        """
        if not domain or not domain.strip():
            return None

        normalized_domain = domain.strip().lower()
        existing = db.query(Tenant).filter(Tenant.domain == normalized_domain).first()
        if existing and (exclude_tenant_id is None or existing.id != exclude_tenant_id):
            raise ConflictException(f"A tenant with domain '{normalized_domain}' already exists")

        return normalized_domain

    @staticmethod
    def validate_status_transition(current_status: TenantStatus, new_status: TenantStatus) -> None:
        """
        Enforce valid state transitions for TenantStatus lifecycle.
        """
        if current_status == new_status:
            return

        # ARCHIVED tenants cannot be directly activated without explicit restoration
        if current_status == TenantStatus.ARCHIVED and new_status == TenantStatus.ACTIVE:
            raise BusinessRuleException("Archived tenants must be un-archived or restored before activation")

    @staticmethod
    def validate_deletion_safety(db: Session, tenant: Tenant) -> None:
        """
        Prevent soft-deleting system/default tenant or active tenant with active users.
        """
        # Block deleting default system tenant
        if tenant.id == 1 or tenant.name.lower() in ["default tenant", "system tenant", "system"]:
            raise BusinessRuleException("Default system tenant cannot be deleted")

        # Block deleting tenant with active users
        active_user_count = db.query(User).filter(
            User.tenant_id == tenant.id,
            User.is_active.is_(True),
            User.is_deleted.is_(False)
        ).count()

        if active_user_count > 0:
            raise BusinessRuleException(
                f"Cannot delete tenant '{tenant.name}'. It currently has {active_user_count} active user account(s)"
            )
