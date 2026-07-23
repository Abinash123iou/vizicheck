from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from app.models.user import User
from app.models.role import Role
from app.repositories.specifications.user_filters import UserFilters

class UserRepository:
    """
    Database access layer for User entity.
    Communicates strictly with the database and returns SQLAlchemy models.
    """

    @staticmethod
    def find_by_email(db: Session, email: str, include_deleted: bool = False) -> Optional[User]:
        """
        Find a user by email with eagerly loaded role, permissions, and tenant.
        """
        query = db.query(User).options(
            joinedload(User.role).joinedload(Role.permissions),
            joinedload(User.tenant)
        ).filter(User.email == email.strip().lower())

        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))

        return query.first()

    @staticmethod
    def find_by_id(db: Session, user_id: int, include_deleted: bool = False) -> Optional[User]:
        """
        Find a user by ID with eagerly loaded role, permissions, and tenant.
        """
        query = db.query(User).options(
            joinedload(User.role).joinedload(Role.permissions),
            joinedload(User.tenant)
        ).filter(User.id == user_id)

        if not include_deleted:
            query = query.filter(User.is_deleted.is_(False))

        return query.first()

    @staticmethod
    def create(db: Session, user_data: dict) -> User:
        """
        Persist a new User model instance.
        """
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        # Re-fetch with eager loaded relationships
        return UserRepository.find_by_id(db, user.id, include_deleted=True) or user

    @staticmethod
    def update(db: Session, user: User, update_data: dict) -> User:
        """
        Update fields on an existing User model instance.
        """
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserRepository.find_by_id(db, user.id, include_deleted=True) or user

    @staticmethod
    def soft_delete(db: Session, user: User) -> User:
        """
        Soft delete user record by setting is_deleted=True and timestamp.
        """
        user.delete()
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def restore(db: Session, user: User) -> User:
        """
        Restore soft-deleted user record by setting is_deleted=False.
        """
        user.restore()
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def activate(db: Session, user: User) -> User:
        """
        Set user active status to True.
        """
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def deactivate(db: Session, user: User) -> User:
        """
        Set user active status to False.
        """
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, password_hash: str) -> User:
        """
        Update user password hash.
        """
        user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_last_login(db: Session, user_id: int) -> None:
        """
        Update last_login timestamp for a user.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.query(User).filter(User.id == user_id).update(
            {User.last_login: now}, 
            synchronize_session=False
        )
        db.commit()

    @staticmethod
    def get_users_paginated(
        db: Session,
        tenant_id: Optional[int] = None,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_deleted: bool = False,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> Tuple[List[User], int]:
        """
        Retrieve paginated list of users with dynamic filter specifications and total count.
        """
        base_query = db.query(User).options(
            joinedload(User.role).joinedload(Role.permissions),
            joinedload(User.tenant)
        )

        filtered_query = UserFilters.apply_filters(
            query=base_query,
            search=search,
            role_id=role_id,
            tenant_id=tenant_id,
            is_active=is_active,
            is_deleted=is_deleted
        )

        total_records = filtered_query.count()

        sorted_query = UserFilters.apply_sorting(filtered_query, sort_by=sort_by, order=order)

        offset = (page - 1) * page_size
        paginated_users = sorted_query.offset(offset).limit(page_size).all()

        return paginated_users, total_records
