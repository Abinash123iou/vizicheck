import re
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.constants.roles import Roles
from app.core.exceptions import (
    ValidationException, 
    ConflictException, 
    AuthorizationException, 
    BusinessRuleException
)

class UserValidator:
    """
    Validation layer for user management business rules and constraints.
    """

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Enforce strong password policy:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 numeric digit
        - At least 1 special character
        """
        if not password or len(password) < 8:
            raise ValidationException("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            raise ValidationException("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValidationException("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            raise ValidationException("Password must contain at least one numeric digit")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            raise ValidationException("Password must contain at least one special character")

    @staticmethod
    def validate_email_uniqueness(db: Session, email: str, exclude_user_id: Optional[int] = None) -> str:
        """
        Normalize email address and verify that it is not registered to another user.
        """
        normalized_email = email.strip().lower()
        existing = db.query(User).filter(User.email == normalized_email).first()

        if existing and (exclude_user_id is None or existing.id != exclude_user_id):
            raise ConflictException("A user with this email address already exists")

        return normalized_email

    @staticmethod
    def validate_role_assignment(current_user: User, target_role_id: int, db: Session) -> Role:
        """
        Verify target role existence and ensure non-Super Admins cannot assign SUPER_ADMIN role.
        """
        role = db.query(Role).filter(Role.id == target_role_id).first()
        if not role:
            raise ValidationException(f"Target role ID '{target_role_id}' does not exist")

        is_super_admin = current_user.role and current_user.role.name == Roles.SUPER_ADMIN
        if not is_super_admin and role.name == Roles.SUPER_ADMIN:
            raise AuthorizationException("Only Super Admins can assign the SUPER_ADMIN role")

        return role

    @staticmethod
    def validate_tenant_boundary(current_user: User, target_tenant_id: Optional[int]) -> Optional[int]:
        """
        Verify tenant assignment boundaries.
        Tenant Admins can only assign users to their own tenant_id.
        """
        is_super_admin = current_user.role and current_user.role.name == Roles.SUPER_ADMIN
        
        if not is_super_admin:
            # If current user is Tenant Admin, mandate target_tenant_id equals current_user.tenant_id
            if current_user.tenant_id is not None:
                if target_tenant_id is not None and target_tenant_id != current_user.tenant_id:
                    raise AuthorizationException("Tenant Admins cannot assign users to a different tenant")
                return current_user.tenant_id

        return target_tenant_id

    @staticmethod
    def validate_user_access(current_user: User, target_user: User) -> None:
        """
        Verify authorization to view/modify target user account.
        Tenant Admins cannot access users of other tenants or Super Admin accounts.
        """
        is_super_admin = current_user.role and current_user.role.name == Roles.SUPER_ADMIN
        if is_super_admin:
            return

        # Tenant boundary check
        if target_user.tenant_id != current_user.tenant_id:
            raise AuthorizationException("Access denied. Target user belongs to a different tenant")

        # Privilege elevation check
        if target_user.role and target_user.role.name == Roles.SUPER_ADMIN:
            raise AuthorizationException("Tenant Admins cannot manage Super Admin accounts")

    @staticmethod
    def validate_self_delete(current_user_id: int, target_user_id: int) -> None:
        """
        Prevent users from deleting their own account via user management APIs.
        """
        if current_user_id == target_user_id:
            raise BusinessRuleException("Users cannot delete their own account")
