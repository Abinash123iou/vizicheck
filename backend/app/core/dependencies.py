from typing import Generator, Optional
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from database.session import SessionLocal
from app.models.user import User
from app.core.auth import oauth2_scheme, extract_token_from_header
from app.core.jwt import decode_token
from app.core.exceptions import (
    AuthenticationException, 
    AuthorizationException,
    InvalidTokenException
)
# Roles check helper
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    Ensures that the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Dependency that extracts Authorization bearer token, validates signature/claims,
    and returns the authenticated user entity.
    """
    if not token:
        token = extract_token_from_header(request)

    if not token:
        raise AuthenticationException("Authentication required. Missing Authorization header")

    # Sanitize token string if duplicate 'Bearer' prefix was included
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "").strip()
    elif token.startswith("bearer "):
        token = token.replace("bearer ", "").strip()

    payload = decode_token(token)

    # Enforce access token type
    if payload.get("token_type") != "access":
        raise InvalidTokenException("Invalid token type. Access token required")

    # Check JTI session status if present
    jti = payload.get("jti")
    if jti:
        from app.repositories.security_repository import SecurityRepository
        session = SecurityRepository.get_session_by_token_jti(db, jti)
        if session and not session.is_active:
            raise InvalidTokenException("Session has been revoked")

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenException("Invalid token subject claim")

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise InvalidTokenException("Invalid user ID format in token claim")

    user = UserRepository.find_by_id(db, user_id=user_id)
    if not user:
        raise AuthenticationException("User associated with token not found")

    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency verifying that current user is active and associated tenant is active.
    """
    AuthService.verify_user_status(current_user)
    AuthService.verify_tenant_status(current_user)
    return current_user

def get_current_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency verifying that current user has SUPER_ADMIN role.
    """
    from app.core.permissions import SystemRoles
    if not current_user.role or current_user.role.name != SystemRoles.SUPER_ADMIN:
        raise AuthorizationException("Action requires Super Admin privileges")
    return current_user

def get_current_tenant_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency verifying that current user has TENANT_ADMIN or SUPER_ADMIN role.
    """
    from app.core.permissions import SystemRoles
    allowed_roles = [SystemRoles.SUPER_ADMIN, SystemRoles.TENANT_ADMIN]
    if not current_user.role or current_user.role.name not in allowed_roles:
        raise AuthorizationException("Action requires Tenant Admin privileges")
    return current_user

def get_current_security_officer(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency verifying that current user has SECURITY_OFFICER, TENANT_ADMIN, or SUPER_ADMIN role.
    """
    from app.core.permissions import SystemRoles
    allowed_roles = [
        SystemRoles.SUPER_ADMIN, 
        SystemRoles.TENANT_ADMIN, 
        SystemRoles.SECURITY_OFFICER
    ]
    if not current_user.role or current_user.role.name not in allowed_roles:
        raise AuthorizationException("Action requires Security Officer privileges")
    return current_user

