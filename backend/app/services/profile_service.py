from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.constants.audit_actions import AuditActions
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.mappers.user_mapper import UserMapper
from app.schemas.profile import UserProfileResponse, UpdateProfileRequest

class ProfileService:
    """
    Service containing business logic for logged-in user profile self-management operations.
    """

    @classmethod
    def get_profile(cls, db: Session, current_user: User) -> UserProfileResponse:
        """
        Return profile details and active permissions of the authenticated user.
        """
        # Re-fetch user to ensure relationships (role, permissions, tenant) are fresh
        user = UserRepository.find_by_id(db, current_user.id) or current_user
        
        permissions = []
        if user.role and user.role.permissions:
            permissions = [p.code for p in user.role.permissions]

        return UserMapper.to_profile_response(user, permissions=permissions)

    @classmethod
    def update_profile(
        cls, 
        db: Session, 
        current_user: User, 
        request: UpdateProfileRequest, 
        ip_address: Optional[str] = None
    ) -> UserProfileResponse:
        """
        Update authenticated user's first_name, last_name, and phone.
        """
        old_value = {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone
        }

        update_data = request.model_dump(exclude_unset=True)
        updated_user = UserRepository.update(db, current_user, update_data)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PROFILE_UPDATED,
            module="USER_MANAGEMENT",
            entity_id=updated_user.id,
            ip_address=ip_address,
            old_value=old_value,
            new_value=update_data
        )

        permissions = []
        if updated_user.role and updated_user.role.permissions:
            permissions = [p.code for p in updated_user.role.permissions]

        return UserMapper.to_profile_response(updated_user, permissions=permissions)
