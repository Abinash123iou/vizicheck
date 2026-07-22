from typing import List, Union
from fastapi import Depends
from app.models.user import User
from app.core.exceptions import AuthorizationException

class SystemRoles:
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    SECURITY_OFFICER = "SECURITY_OFFICER"
    VISITOR = "VISITOR"

class PermissionChecker:
    """
    FastAPI dependency to verify if the current user possesses a required permission.
    SUPER_ADMIN automatically bypasses individual permission checks.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: User) -> User:
        if not current_user or not current_user.role:
            raise AuthorizationException("User role not assigned or authenticated")

        # SUPER_ADMIN has full system privileges
        if current_user.role.name == SystemRoles.SUPER_ADMIN:
            return current_user

        user_permissions = [p.code for p in current_user.role.permissions] if current_user.role.permissions else []
        if self.required_permission not in user_permissions:
            raise AuthorizationException(
                f"Permission denied. Required permission: '{self.required_permission}'"
            )
        return current_user

class RoleChecker:
    """
    FastAPI dependency to verify if the current user belongs to one of the specified allowed roles.
    """
    def __init__(self, allowed_roles: Union[str, List[str]]):
        if isinstance(allowed_roles, str):
            self.allowed_roles = [allowed_roles]
        else:
            self.allowed_roles = allowed_roles

    def __call__(self, current_user: User) -> User:
        if not current_user or not current_user.role:
            raise AuthorizationException("User role not assigned or authenticated")

        if current_user.role.name not in self.allowed_roles:
            raise AuthorizationException(
                f"Access denied. Allowed roles: {', '.join(self.allowed_roles)}"
            )
        return current_user

def has_permission(required_permission: str):
    """
    Helper function to instantiate a PermissionChecker dependency.
    """
    return PermissionChecker(required_permission)

def has_role(allowed_roles: Union[str, List[str]]):
    """
    Helper function to instantiate a RoleChecker dependency.
    """
    return RoleChecker(allowed_roles)
