from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models.user import User
from app.models.role import Role

class UserRepository:
    """
    Database access layer for User entity.
    Communicates strictly with the database and returns SQLAlchemy models.
    """

    @staticmethod
    def find_by_email(db: Session, email: str) -> Optional[User]:
        """
        Find an active (non-soft-deleted) user by email with eagerly loaded role, permissions, and tenant.
        """
        return (
            db.query(User)
            .options(
                joinedload(User.role).joinedload(Role.permissions),
                joinedload(User.tenant)
            )
            .filter(
                User.email == email.strip().lower(),
                User.is_deleted.is_(False)
            )
            .first()
        )

    @staticmethod
    def find_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Find an active (non-soft-deleted) user by ID with eagerly loaded role, permissions, and tenant.
        """
        return (
            db.query(User)
            .options(
                joinedload(User.role).joinedload(Role.permissions),
                joinedload(User.tenant)
            )
            .filter(
                User.id == user_id,
                User.is_deleted.is_(False)
            )
            .first()
        )

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
