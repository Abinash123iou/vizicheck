from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.constants.roles import Roles
from app.constants.audit_actions import AuditActions
from app.core.exceptions import NotFoundException, ValidationException
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.user_validator import UserValidator
from app.mappers.user_mapper import UserMapper
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    PaginationRequest,
    EnhancedPaginationResponse,
    ChangePasswordRequest,
    ResetPasswordRequest
)

class UserService:
    """
    Service containing business logic for administrative user management operations,
    incorporating validation rules, repository access, mapping, and audit logging.
    """

    @classmethod
    def create_user(
        cls, 
        db: Session, 
        current_user: User, 
        request: CreateUserRequest, 
        ip_address: Optional[str] = None
    ) -> UserResponse:
        """
        Create a new user account after validating email uniqueness, password strength,
        role assignment permissions, and tenant boundaries.
        """
        normalized_email = UserValidator.validate_email_uniqueness(db, request.email)
        UserValidator.validate_password_strength(request.password)
        UserValidator.validate_role_assignment(current_user, request.role_id, db)
        target_tenant_id = UserValidator.validate_tenant_boundary(current_user, request.tenant_id)

        password_hash = hash_password(request.password)

        user_data = {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "email": normalized_email,
            "password_hash": password_hash,
            "phone": request.phone,
            "role_id": request.role_id,
            "tenant_id": target_tenant_id,
            "is_active": True
        }

        user = UserRepository.create(db, user_data)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.USER_CREATED,
            module="USER_MANAGEMENT",
            entity_id=user.id,
            ip_address=ip_address,
            new_value={"email": user.email, "role_id": user.role_id, "tenant_id": user.tenant_id}
        )

        return UserMapper.to_user_response(user)

    @classmethod
    def get_user_by_id(cls, db: Session, current_user: User, user_id: int) -> UserResponse:
        """
        Retrieve a single active user by ID after verifying tenant access authorization.
        """
        user = UserRepository.find_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")

        UserValidator.validate_user_access(current_user, user)
        return UserMapper.to_user_response(user)

    @classmethod
    def list_users(
        cls, 
        db: Session, 
        current_user: User, 
        params: PaginationRequest
    ) -> EnhancedPaginationResponse[UserResponse]:
        """
        Retrieve paginated list of users filtered by role, tenant, status, search, and sorting.
        Enforces tenant isolation for non-Super Admin callers.
        """
        effective_tenant_id = params.tenant_id
        if current_user.role and current_user.role.name != Roles.SUPER_ADMIN:
            effective_tenant_id = current_user.tenant_id

        users, total_count = UserRepository.get_users_paginated(
            db=db,
            tenant_id=effective_tenant_id,
            search=params.search,
            role_id=params.role_id,
            is_active=params.is_active,
            is_deleted=params.is_deleted,
            page=params.page,
            page_size=params.page_size,
            sort_by=params.sort_by,
            order=params.order
        )

        return UserMapper.to_paginated_response(
            users=users,
            total_records=total_count,
            page=params.page,
            page_size=params.page_size
        )

    @classmethod
    def update_user(
        cls, 
        db: Session, 
        current_user: User, 
        user_id: int, 
        request: UpdateUserRequest, 
        ip_address: Optional[str] = None
    ) -> UserResponse:
        """
        Update user profile details, role, or tenant association.
        """
        user = UserRepository.find_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")

        UserValidator.validate_user_access(current_user, user)

        if request.role_id is not None:
            UserValidator.validate_role_assignment(current_user, request.role_id, db)

        if request.tenant_id is not None:
            UserValidator.validate_tenant_boundary(current_user, request.tenant_id)

        old_value = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role_id": user.role_id,
            "tenant_id": user.tenant_id
        }

        update_data = request.model_dump(exclude_unset=True)
        updated_user = UserRepository.update(db, user, update_data)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.USER_UPDATED,
            module="USER_MANAGEMENT",
            entity_id=updated_user.id,
            ip_address=ip_address,
            old_value=old_value,
            new_value=update_data
        )

        return UserMapper.to_user_response(updated_user)

    @classmethod
    def soft_delete_user(
        cls, 
        db: Session, 
        current_user: User, 
        user_id: int, 
        ip_address: Optional[str] = None
    ) -> None:
        """
        Soft delete user record after verifying self-delete prevention and authorization.
        """
        user = UserRepository.find_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")

        UserValidator.validate_self_delete(current_user.id, user_id)
        UserValidator.validate_user_access(current_user, user)

        UserRepository.soft_delete(db, user)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.USER_DELETED,
            module="USER_MANAGEMENT",
            entity_id=user_id,
            ip_address=ip_address,
            old_value={"email": user.email, "is_deleted": False},
            new_value={"is_deleted": True}
        )

    @classmethod
    def restore_user(
        cls, 
        db: Session, 
        current_user: User, 
        user_id: int, 
        ip_address: Optional[str] = None
    ) -> UserResponse:
        """
        Restore soft-deleted user account.
        """
        user = UserRepository.find_by_id(db, user_id, include_deleted=True)
        if not user or not user.is_deleted:
            raise NotFoundException(f"Soft-deleted user with ID '{user_id}' not found")

        UserValidator.validate_user_access(current_user, user)

        restored_user = UserRepository.restore(db, user)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.USER_RESTORED,
            module="USER_MANAGEMENT",
            entity_id=user_id,
            ip_address=ip_address,
            old_value={"is_deleted": True},
            new_value={"is_deleted": False}
        )

        return UserMapper.to_user_response(restored_user)

    @classmethod
    def activate_user(
        cls, 
        db: Session, 
        current_user: User, 
        user_id: int, 
        ip_address: Optional[str] = None
    ) -> UserResponse:
        """
        Activate disabled user account.
        """
        user = UserRepository.find_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")

        UserValidator.validate_user_access(current_user, user)

        activated_user = UserRepository.activate(db, user)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.USER_ACTIVATED,
            module="USER_MANAGEMENT",
            entity_id=user_id,
            ip_address=ip_address,
            old_value={"is_active": False},
            new_value={"is_active": True}
        )

        return UserMapper.to_user_response(activated_user)

    @classmethod
    def deactivate_user(
        cls, 
        db: Session, 
        current_user: User, 
        user_id: int, 
        ip_address: Optional[str] = None
    ) -> UserResponse:
        """
        Deactivate active user account.
        """
        user = UserRepository.find_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")

        UserValidator.validate_user_access(current_user, user)

        deactivated_user = UserRepository.deactivate(db, user)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.USER_DEACTIVATED,
            module="USER_MANAGEMENT",
            entity_id=user_id,
            ip_address=ip_address,
            old_value={"is_active": True},
            new_value={"is_active": False}
        )

        return UserMapper.to_user_response(deactivated_user)

    @classmethod
    def change_password(
        cls, 
        db: Session, 
        current_user: User, 
        request: ChangePasswordRequest, 
        ip_address: Optional[str] = None
    ) -> None:
        """
        Allow logged-in user to change their password after verifying current password.
        """
        if not verify_password(request.current_password, current_user.password_hash):
            raise ValidationException("Current password is incorrect")

        UserValidator.validate_password_strength(request.new_password)
        new_password_hash = hash_password(request.new_password)

        UserRepository.update_password(db, current_user, new_password_hash)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASSWORD_CHANGED,
            module="USER_MANAGEMENT",
            entity_id=current_user.id,
            ip_address=ip_address
        )

    @classmethod
    def reset_password(
        cls, 
        db: Session, 
        current_user: User, 
        user_id: int, 
        request: ResetPasswordRequest, 
        ip_address: Optional[str] = None
    ) -> None:
        """
        Allow administrator to reset another user's password.
        """
        user = UserRepository.find_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"User with ID '{user_id}' not found")

        UserValidator.validate_user_access(current_user, user)
        UserValidator.validate_password_strength(request.new_password)

        new_password_hash = hash_password(request.new_password)
        UserRepository.update_password(db, user, new_password_hash)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASSWORD_RESET,
            module="USER_MANAGEMENT",
            entity_id=user.id,
            ip_address=ip_address
        )
