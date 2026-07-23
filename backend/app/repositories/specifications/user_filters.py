from typing import Optional
from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Query
from app.models.user import User

class UserFilters:
    """
    Specification helper to dynamically build SQLAlchemy query filters and sorting for User queries.
    """

    @staticmethod
    def apply_filters(
        query: Query,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_deleted: bool = False
    ) -> Query:
        """
        Apply search, role, tenant, active status, and soft-delete filters to SQLAlchemy query.
        """
        # Soft-delete filter
        if not is_deleted:
            query = query.filter(User.is_deleted.is_(False))

        # Active status filter
        if is_active is not None:
            query = query.filter(User.is_active.is_(is_active))

        # Tenant filter
        if tenant_id is not None:
            query = query.filter(User.tenant_id == tenant_id)

        # Role filter
        if role_id is not None:
            query = query.filter(User.role_id == role_id)

        # Search term filter (searches first_name, last_name, email)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        return query

    @staticmethod
    def apply_sorting(query: Query, sort_by: str = "created_at", order: str = "desc") -> Query:
        """
        Apply sorting to SQLAlchemy query based on column name and direction.
        """
        sort_column_map = {
            "created_at": User.created_at,
            "email": User.email,
            "first_name": User.first_name,
            "last_name": User.last_name,
            "id": User.id
        }

        col = sort_column_map.get(sort_by.lower(), User.created_at)
        if order.lower() == "asc":
            return query.order_by(asc(col))
        return query.order_by(desc(col))
