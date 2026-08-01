from datetime import datetime
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Query
from app.models.approval import Approval, ApprovalStatus, ApprovalType, ApprovalHistory
from app.models.visit_request import VisitRequest
from app.models.user import User
from app.models.visitor import Visitor


class ApprovalFilterSpecification:
    """
    Specification query filter builder for Approval & ApprovalHistory queries.
    """

    @staticmethod
    def apply_approval_filters(
        query: Query,
        tenant_id: int,
        approver_id: Optional[int] = None,
        request_id: Optional[int] = None,
        status: Optional[ApprovalStatus] = None,
        approval_type: Optional[ApprovalType] = None,
        search: Optional[str] = None
    ) -> Query:
        query = query.filter(
            Approval.tenant_id == tenant_id,
            Approval.is_deleted == False
        )

        if approver_id is not None:
            query = query.filter(Approval.current_approver_id == approver_id)

        if request_id is not None:
            query = query.filter(Approval.request_id == request_id)

        if status is not None:
            query = query.filter(Approval.status == status)

        if approval_type is not None:
            query = query.filter(Approval.approval_type == approval_type)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.join(Approval.visit_request).outerjoin(VisitRequest.visitor).outerjoin(VisitRequest.host).filter(
                or_(
                    Approval.approval_code.ilike(term),
                    VisitRequest.request_code.ilike(term),
                    Visitor.first_name.ilike(term),
                    Visitor.last_name.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term)
                )
            )

        return query
