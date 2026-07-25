from datetime import datetime
from typing import Optional
from sqlalchemy import or_, func, asc, desc
from sqlalchemy.orm import Query
from app.models.visitor import Visitor, VisitorStatus

class VisitorFilters:
    """
    Specification helper class to build dynamic SQLAlchemy query filters and sorting for Visitor entities.
    """

    @staticmethod
    def apply_filters(
        query: Query,
        tenant_id: Optional[int] = None,
        search: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        government_id_number: Optional[str] = None,
        visitor_code: Optional[str] = None,
        status: Optional[VisitorStatus] = None,
        verified: Optional[bool] = None,
        blacklisted: Optional[bool] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        is_deleted: bool = False
    ) -> Query:
        """
        Apply filter conditions to the given SQLAlchemy query.
        """
        # Tenant isolation boundary
        if tenant_id is not None:
            query = query.filter(Visitor.tenant_id == tenant_id)

        # Soft-delete filter
        if is_deleted is not None:
            query = query.filter(Visitor.is_deleted.is_(is_deleted))

        # Status filter
        if status:
            query = query.filter(Visitor.status == status)

        # Verification filter
        if verified is not None:
            query = query.filter(Visitor.verified.is_(verified))

        # Blacklist filter
        if blacklisted is not None:
            query = query.filter(Visitor.blacklisted.is_(blacklisted))

        # Specific field filters
        if phone:
            query = query.filter(Visitor.phone.ilike(f"%{phone.strip()}%"))

        if email:
            query = query.filter(Visitor.email.ilike(f"%{email.strip()}%"))

        if company:
            query = query.filter(Visitor.company.ilike(f"%{company.strip()}%"))

        if government_id_number:
            query = query.filter(Visitor.government_id_number.ilike(f"%{government_id_number.strip()}%"))

        if visitor_code:
            query = query.filter(Visitor.visitor_code.ilike(f"%{visitor_code.strip()}%"))

        if name:
            name_term = f"%{name.strip()}%"
            query = query.filter(
                or_(
                    Visitor.first_name.ilike(name_term),
                    Visitor.last_name.ilike(name_term),
                    func.concat(Visitor.first_name, ' ', Visitor.last_name).ilike(name_term)
                )
            )

        # Date range filter
        if created_from:
            query = query.filter(Visitor.created_at >= created_from)
        if created_to:
            query = query.filter(Visitor.created_at <= created_to)

        # General multi-field search term
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Visitor.first_name.ilike(search_term),
                    Visitor.last_name.ilike(search_term),
                    func.concat(Visitor.first_name, ' ', Visitor.last_name).ilike(search_term),
                    Visitor.phone.ilike(search_term),
                    Visitor.email.ilike(search_term),
                    Visitor.visitor_code.ilike(search_term),
                    Visitor.company.ilike(search_term),
                    Visitor.government_id_number.ilike(search_term)
                )
            )

        return query

    @staticmethod
    def apply_sorting(query: Query, sort_by: str = "created_at", order: str = "desc") -> Query:
        """
        Apply column sorting to the query.
        """
        sort_fields = {
            "id": Visitor.id,
            "created_at": Visitor.created_at,
            "updated_at": Visitor.updated_at,
            "first_name": Visitor.first_name,
            "last_name": Visitor.last_name,
            "visitor_code": Visitor.visitor_code,
            "phone": Visitor.phone,
            "email": Visitor.email,
            "company": Visitor.company,
            "status": Visitor.status,
            "verified": Visitor.verified,
            "blacklisted": Visitor.blacklisted
        }

        target_field = sort_fields.get(sort_by.lower(), Visitor.created_at)
        direction = asc if order.lower() == "asc" else desc
        return query.order_by(direction(target_field))
