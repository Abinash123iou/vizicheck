from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.auth import ResponseEnvelope
from app.schemas.profile import UserProfileResponse, UpdateProfileRequest
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ResponseEnvelope[UserProfileResponse])
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve authenticated user's profile information.
    """
    profile_dto = ProfileService.get_profile(db=db, current_user=current_user)
    return ResponseEnvelope(
        success=True,
        message="User profile retrieved successfully",
        data=profile_dto
    )

@router.put("", response_model=ResponseEnvelope[UserProfileResponse])
def update_profile(
    request_data: UpdateProfileRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update authenticated user's profile information (first_name, last_name, phone).
    """
    client_ip = request.client.host if request.client else None
    profile_dto = ProfileService.update_profile(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="User profile updated successfully",
        data=profile_dto
    )
