from datetime import datetime
from typing import Optional
from sqlalchemy import or_, func, asc, desc
from sqlalchemy.orm import Query
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.visitor import Visitor
from app.models.user import User

class PassFilters:
    """
    Specification helper class to build dynamic SQLAlchemy query filters and sorting for VisitorPass entities.
    """

    @staticmethod
    def apply_filters(
        query: Query,
        tenant_id: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[PassStatus] = None,
        visitor_id: Optional[int] = None,
        host_id: Optional[int] = None,
        visit_request_id: Optional[int] = None,
        is_deleted: bool = False
    ) -> Query:
        """
        Apply filter conditions to the given VisitorPass SQLAlchemy query.
        """
        # Tenant isolation boundary
        if tenant_id is not None:
            query = query.filter(VisitorPass.tenant_id == tenant_id)

        # Soft-delete filter
        if is_deleted is not None:
            query = query.filter(VisitorPass.is_deleted.is_(is_deleted))

        # Status filter
        if status:
            query = query.filter(VisitorPass.status == status)

        # Foreign Key filters
        if visitor_id is not None:
            query = query.filter(VisitorPass.visitor_id == visitor_id)

        if host_id is not None:
            query = query.filter(VisitorPass.host_id == host_id)

        if visit_request_id is not None:
            query = query.filter(VisitorPass.visit_request_id == visit_request_id)

        # Multi-field search query across VisitorPass, Visitor, and Host
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.outerjoin(Visitor, VisitorPass.visitor_id == Visitor.id)\
                         .outerjoin(User, VisitorPass.host_id == User.id)\
                         .filter(
                             or_(
                                 VisitorPass.pass_code.ilike(term),
                                 VisitorPass.uuid.ilike(term),
                                 Visitor.first_name.ilike(term),
                                 Visitor.last_name.ilike(term),
                                 func.concat(Visitor.first_name, ' ', Visitor.last_name).ilike(term),
                                 Visitor.phone.ilike(term),
                                 Visitor.email.ilike(term),
                                 Visitor.company.ilike(term),
                                 User.first_name.ilike(term),
                                 User.last_name.ilike(term),
                                 User.email.ilike(term)
                             )
                         )

        return query

    @staticmethod
    def apply_sorting(query: Query, sort_by: str = "created_at", order: str = "desc") -> Query:
        """
        Apply column sorting to the query.
        """
        sort_fields = {
            "id": VisitorPass.id,
            "created_at": VisitorPass.created_at,
            "updated_at": VisitorPass.updated_at,
            "valid_from": VisitorPass.valid_from,
            "valid_until": VisitorPass.valid_until,
            "status": VisitorPass.status,
            "pass_code": VisitorPass.pass_code
        }

        sort_column = sort_fields.get(sort_by.lower(), VisitorPass.created_at)
        if order.lower() == "asc":
            return query.order_by(asc(sort_column))
        return query.order_by(desc(sort_column))
