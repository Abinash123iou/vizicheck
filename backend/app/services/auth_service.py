from typing import List, Optional
from sqlalchemy.orm import Session
from config import settings
from app.models.user import User
from app.models.tenant import TenantStatus
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    decode_token
)
from app.core.exceptions import (
    AuthenticationException,
    UserInactiveException,
    TenantInactiveException,
    InvalidTokenException,
    ExpiredTokenException
)
from app.repositories.user_repository import UserRepository
from app.repositories.auth_repository import AuthRepository
from app.schemas.login import LoginRequest, LoginResponseData
from app.schemas.token import TokenResponseData
from app.schemas.auth import UserProfileResponse

class AuthService:
    """
    Service containing business logic for authentication, RBAC claim generation,
    status validation, token lifecycle management, and audit logging.
    """

    @classmethod
    def login(
        cls, 
        db: Session, 
        login_data: LoginRequest, 
        ip_address: Optional[str] = None
    ) -> LoginResponseData:
        """
        Execute user login flow:
        1. Find user by email
        2. Verify password
        3. Verify user active status
        4. Verify tenant active status
        5. Generate JWT tokens
        6. Update last login timestamp
        7. Record audit log
        8. Return LoginResponseData DTO
        """
        user = UserRepository.find_by_email(db, email=login_data.email)
        
        # Invalid email or password failure
        if not user or not verify_password(login_data.password, user.password_hash):
            user_id = user.id if user else None
            AuthRepository.create_audit_log(
                db, 
                user_id=user_id, 
                action="LOGIN_FAILED", 
                ip_address=ip_address,
                new_value={"email": login_data.email, "reason": "Invalid credentials"}
            )
            raise AuthenticationException("Invalid email or password")

        # User active status check
        cls.verify_user_status(user)

        # Tenant active status check
        cls.verify_tenant_status(user)

        # Build permissions list from role
        permissions: List[str] = []
        if user.role and user.role.permissions:
            permissions = [p.code for p in user.role.permissions]

        # Generate JWT access and refresh tokens
        access_token, refresh_token = cls.generate_tokens_for_user(user, permissions)

        # Update last login timestamp
        UserRepository.update_last_login(db, user_id=user.id)

        # Audit log success
        AuthRepository.create_audit_log(
            db, 
            user_id=user.id, 
            action="LOGIN_SUCCESS", 
            ip_address=ip_address
        )

        user_profile = cls.build_user_profile(user, permissions)

        return LoginResponseData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_profile
        )

    @classmethod
    def logout(
        cls, 
        db: Session, 
        user_id: int, 
        ip_address: Optional[str] = None
    ) -> None:
        """
        Execute logout audit logging.
        """
        AuthRepository.create_audit_log(
            db, 
            user_id=user_id, 
            action="LOGOUT", 
            ip_address=ip_address
        )

    @classmethod
    def refresh_token(
        cls, 
        db: Session, 
        refresh_token_str: str, 
        ip_address: Optional[str] = None
    ) -> TokenResponseData:
        """
        Refresh access and refresh token pair using a valid refresh token.
        """
        payload = decode_token(refresh_token_str)

        # Verify token_type claim is 'refresh'
        if payload.get("token_type") != "refresh":
            raise InvalidTokenException("Invalid token type. Refresh token required")

        sub = payload.get("sub")
        if not sub:
            raise InvalidTokenException("Invalid token subject")

        try:
            user_id = int(sub)
        except (ValueError, TypeError):
            raise InvalidTokenException("Invalid user ID in token claim")

        user = UserRepository.find_by_id(db, user_id=user_id)
        if not user:
            raise AuthenticationException("User account associated with token not found")

        # Status checks
        cls.verify_user_status(user)
        cls.verify_tenant_status(user)

        # Extract permissions
        permissions: List[str] = []
        if user.role and user.role.permissions:
            permissions = [p.code for p in user.role.permissions]

        # Generate fresh tokens
        access_token, new_refresh_token = cls.generate_tokens_for_user(user, permissions)

        # Record audit log
        AuthRepository.create_audit_log(
            db, 
            user_id=user.id, 
            action="TOKEN_REFRESH", 
            ip_address=ip_address
        )

        return TokenResponseData(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    @classmethod
    def verify_user_status(cls, user: User) -> None:
        """
        Verify user is active and not soft-deleted.
        """
        if user.is_deleted or not user.is_active:
            raise UserInactiveException("User account is inactive or disabled")

    @classmethod
    def verify_tenant_status(cls, user: User) -> None:
        """
        Verify tenant associated with user is active.
        """
        if user.tenant_id and user.tenant:
            if user.tenant.is_deleted or user.tenant.status != TenantStatus.ACTIVE:
                raise TenantInactiveException("Tenant organization is inactive or suspended")

    @classmethod
    def generate_tokens_for_user(
        cls, 
        user: User, 
        permissions: List[str]
    ) -> tuple[str, str]:
        """
        Helper method to construct token claims and issue JWT pair.
        Never stores password, password hash, phone, or unnecessary sensitive data.
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if user.role else "VISITOR",
            "tenant_id": user.tenant_id,
            "permissions": permissions
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return access_token, refresh_token

    @classmethod
    def build_user_profile(cls, user: User, permissions: List[str]) -> UserProfileResponse:
        """
        Construct UserProfileResponse DTO from User model.
        """
        return UserProfileResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            role_id=user.role_id,
            role_name=user.role.name if user.role else "",
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name if user.tenant else None,
            permissions=permissions,
            last_login=user.last_login,
            created_at=user.created_at
        )
