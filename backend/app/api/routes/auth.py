from typing import Any, List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    ResponseEnvelope, 
    RefreshTokenRequest, 
    UserProfileResponse
)
from app.schemas.login import LoginRequest, LoginResponseData
from app.schemas.token import TokenResponseData
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request headers or client connection.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.post(
    "/login",
    response_model=ResponseEnvelope[LoginResponseData],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token pair"
)
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> ResponseEnvelope[LoginResponseData]:
    """
    Authenticate user using email and password.
    Returns access token, refresh token, and user profile information.
    """
    ip_address = get_client_ip(request)
    result = AuthService.login(db, login_data=login_data, ip_address=ip_address)
    return ResponseEnvelope[LoginResponseData](
        success=True,
        message="Login successful",
        data=result,
        errors=None
    )

@router.post(
    "/refresh",
    response_model=ResponseEnvelope[TokenResponseData],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using valid refresh token"
)
def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> ResponseEnvelope[TokenResponseData]:
    """
    Issue new access and refresh token pair using a valid refresh token.
    """
    ip_address = get_client_ip(request)
    result = AuthService.refresh_token(
        db, 
        refresh_token_str=refresh_data.refresh_token, 
        ip_address=ip_address
    )
    return ResponseEnvelope[TokenResponseData](
        success=True,
        message="Token refreshed successfully",
        data=result,
        errors=None
    )

@router.post(
    "/logout",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_200_OK,
    summary="Logout current user and log audit event"
)
def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseEnvelope[dict]:
    """
    Logout currently authenticated user and record logout in audit log.
    """
    ip_address = get_client_ip(request)
    AuthService.logout(db, user_id=current_user.id, ip_address=ip_address)
    return ResponseEnvelope[dict](
        success=True,
        message="Logout successful",
        data={"user_id": current_user.id},
        errors=None
    )

@router.get(
    "/me",
    response_model=ResponseEnvelope[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> ResponseEnvelope[UserProfileResponse]:
    """
    Retrieve profile details, assigned role, and permissions of the logged-in user.
    """
    permissions: List[str] = []
    if current_user.role and current_user.role.permissions:
        permissions = [p.code for p in current_user.role.permissions]

    user_profile = AuthService.build_user_profile(current_user, permissions)

    return ResponseEnvelope[UserProfileResponse](
        success=True,
        message="User profile retrieved successfully",
        data=user_profile,
        errors=None
    )
