from datetime import datetime
from typing import Optional
from sqlalchemy import or_, func, asc, desc
from sqlalchemy.orm import Query
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor import Visitor
from app.models.user import User

class RequestFilters:
    """
    Specification helper class to build dynamic SQLAlchemy query filters and sorting for VisitRequest entities.
    """

    @staticmethod
    def apply_filters(
        query: Query,
        tenant_id: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[VisitRequestStatus] = None,
        visitor_id: Optional[int] = None,
        host_id: Optional[int] = None,
        department: Optional[str] = None,
        request_code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_deleted: bool = False
    ) -> Query:
        """
        Apply filter conditions to the given VisitRequest SQLAlchemy query.
        """
        # Tenant isolation boundary
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)

        # Soft-delete filter
        if is_deleted is not None:
            query = query.filter(VisitRequest.is_deleted.is_(is_deleted))

        # Status filter
        if status:
            query = query.filter(VisitRequest.status == status)

        # Foreign Key filters
        if visitor_id is not None:
            query = query.filter(VisitRequest.visitor_id == visitor_id)

        if host_id is not None:
            query = query.filter(VisitRequest.host_id == host_id)

        # Field filters
        if department:
            query = query.filter(VisitRequest.department.ilike(f"%{department.strip()}%"))

        if request_code:
            query = query.filter(VisitRequest.request_code.ilike(f"%{request_code.strip()}%"))

        # Date range filter (scheduled_start_time)
        if start_date:
            s_naive = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
            query = query.filter(VisitRequest.scheduled_start_time >= s_naive)

        if end_date:
            e_naive = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
            query = query.filter(VisitRequest.scheduled_start_time <= e_naive)

        # Multi-field search query across VisitRequest, Visitor, and Host
        if search and search.strip():
            term = f"%{search.strip()}%"
            # Join Visitor and Host tables for comprehensive text search
            query = query.outerjoin(Visitor, VisitRequest.visitor_id == Visitor.id)\
                         .outerjoin(User, VisitRequest.host_id == User.id)\
                         .filter(
                             or_(
                                 VisitRequest.request_code.ilike(term),
                                 VisitRequest.purpose.ilike(term),
                                 VisitRequest.department.ilike(term),
                                 Visitor.first_name.ilike(term),
                                 Visitor.last_name.ilike(term),
                                 func.concat(Visitor.first_name, ' ', Visitor.last_name).ilike(term),
                                 Visitor.phone.ilike(term),
                                 Visitor.email.ilike(term),
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
            "id": VisitRequest.id,
            "created_at": VisitRequest.created_at,
            "updated_at": VisitRequest.updated_at,
            "scheduled_start_time": VisitRequest.scheduled_start_time,
            "scheduled_end_time": VisitRequest.scheduled_end_time,
            "status": VisitRequest.status,
            "request_code": VisitRequest.request_code,
            "purpose": VisitRequest.purpose,
            "department": VisitRequest.department
        }

        target_field = sort_fields.get(sort_by.lower(), VisitRequest.created_at)
        direction = asc if order.lower() == "asc" else desc
        return query.order_by(direction(target_field))
