from typing import Optional
from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Query
from app.models.tenant import Tenant, TenantStatus

class TenantFilters:
    """
    Specification helper to dynamically build SQLAlchemy query filters and sorting for Tenant queries.
    """

    @staticmethod
    def apply_filters(
        query: Query,
        search: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        is_deleted: bool = False
    ) -> Query:
        """
        Apply search, status, and soft-delete filters to SQLAlchemy query.
        """
        # Soft-delete filter
        if not is_deleted:
            query = query.filter(Tenant.is_deleted.is_(False))

        # Status filter
        if status is not None:
            query = query.filter(Tenant.status == status)

        # Multi-field search term filter (searches name, contact_email, slug, domain, code)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Tenant.name.ilike(search_term),
                    Tenant.contact_email.ilike(search_term),
                    Tenant.contact_person.ilike(search_term),
                    Tenant.slug.ilike(search_term),
                    Tenant.domain.ilike(search_term),
                    Tenant.code.ilike(search_term)
                )
            )

        return query

    @staticmethod
    def apply_sorting(query: Query, sort_by: str = "created_at", order: str = "desc") -> Query:
        """
        Apply sorting to SQLAlchemy query based on column name and direction.
        """
        sort_column_map = {
            "created_at": Tenant.created_at,
            "name": Tenant.name,
            "code": Tenant.code,
            "status": Tenant.status,
            "id": Tenant.id
        }

        col = sort_column_map.get(sort_by.lower(), Tenant.created_at)
        if order.lower() == "asc":
            return query.order_by(asc(col))
        return query.order_by(desc(col))
