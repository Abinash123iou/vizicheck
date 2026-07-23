import math
from typing import List, Optional
from app.models.user import User
from app.schemas.user import UserResponse, EnhancedPaginationResponse
from app.schemas.profile import UserProfileResponse

class UserMapper:
    """
    Mapper class responsible for transforming SQLAlchemy User entities into response DTOs.
    """

    @staticmethod
    def to_user_response(user: User) -> UserResponse:
        """
        Convert User ORM entity to UserResponse DTO.
        """
        return UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            is_deleted=getattr(user, "is_deleted", False),
            role_id=user.role_id,
            role_name=user.role.name if user.role else "",
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name if user.tenant else None,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    @staticmethod
    def to_profile_response(user: User, permissions: Optional[List[str]] = None) -> UserProfileResponse:
        """
        Convert User ORM entity to UserProfileResponse DTO.
        """
        perms = permissions
        if perms is None:
            perms = []
            if user.role and user.role.permissions:
                perms = [p.code for p in user.role.permissions]

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
            permissions=perms,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    @classmethod
    def to_paginated_response(
        cls, 
        users: List[User], 
        total_records: int, 
        page: int, 
        page_size: int
    ) -> EnhancedPaginationResponse[UserResponse]:
        """
        Construct EnhancedPaginationResponse containing mapped UserResponse items and metadata.
        """
        items = [cls.to_user_response(user) for user in users]
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1 and total_pages > 0

        return EnhancedPaginationResponse(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            items=items
        )
