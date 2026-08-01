from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.approval import Approval, ApprovalHistory, ApprovalStatus, ApprovalType, ApprovalAction
from app.repositories.specifications.approval_filters import ApprovalFilterSpecification


class ApprovalRepository:
    """
    Repository layer for managing Approval and ApprovalHistory database operations.
    """

    @classmethod
    def create_approval(cls, db: Session, approval: Approval) -> Approval:
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return approval

    @classmethod
    def get_by_id(cls, db: Session, approval_id: int) -> Optional[Approval]:
        return db.query(Approval).options(
            joinedload(Approval.visit_request),
            joinedload(Approval.current_approver),
            joinedload(Approval.history_entries)
        ).filter(
            Approval.id == approval_id,
            Approval.is_deleted == False
        ).first()

    @classmethod
    def get_by_code(cls, db: Session, tenant_id: int, approval_code: str) -> Optional[Approval]:
        return db.query(Approval).filter(
            Approval.tenant_id == tenant_id,
            Approval.approval_code == approval_code,
            Approval.is_deleted == False
        ).first()

    @classmethod
    def get_by_request_id(cls, db: Session, tenant_id: int, request_id: int) -> Optional[Approval]:
        return db.query(Approval).options(
            joinedload(Approval.visit_request),
            joinedload(Approval.current_approver),
            joinedload(Approval.history_entries)
        ).filter(
            Approval.tenant_id == tenant_id,
            Approval.request_id == request_id,
            Approval.is_deleted == False
        ).order_by(Approval.created_at.desc()).first()

    @classmethod
    def update_approval(cls, db: Session, approval: Approval) -> Approval:
        db.commit()
        db.refresh(approval)
        return approval

    @classmethod
    def create_history_entry(cls, db: Session, history: ApprovalHistory) -> ApprovalHistory:
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    @classmethod
    def get_approval_history(cls, db: Session, approval_id: int) -> List[ApprovalHistory]:
        return db.query(ApprovalHistory).options(
            joinedload(ApprovalHistory.actor),
            joinedload(ApprovalHistory.delegated_to)
        ).filter(
            ApprovalHistory.approval_id == approval_id
        ).order_by(ApprovalHistory.created_at.asc()).all()

    @classmethod
    def list_approvals(
        cls,
        db: Session,
        tenant_id: int,
        approver_id: Optional[int] = None,
        request_id: Optional[int] = None,
        status: Optional[ApprovalStatus] = None,
        approval_type: Optional[ApprovalType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Approval], int]:
        base_query = db.query(Approval).options(
            joinedload(Approval.visit_request),
            joinedload(Approval.current_approver)
        )

        filtered_query = ApprovalFilterSpecification.apply_approval_filters(
            query=base_query,
            tenant_id=tenant_id,
            approver_id=approver_id,
            request_id=request_id,
            status=status,
            approval_type=approval_type,
            search=search
        )

        total_count = filtered_query.count()
        offset = (page - 1) * page_size
        items = filtered_query.order_by(Approval.created_at.desc()).offset(offset).limit(page_size).all()

        return items, total_count

    @classmethod
    def get_approval_stats(cls, db: Session, tenant_id: int, approver_id: Optional[int] = None) -> Dict[str, int]:
        query = db.query(Approval.status, func.count(Approval.id)).filter(
            Approval.tenant_id == tenant_id,
            Approval.is_deleted == False
        )
        if approver_id is not None:
            query = query.filter(Approval.current_approver_id == approver_id)

        status_counts = dict(query.group_by(Approval.status).all())

        total = sum(status_counts.values())
        return {
            "tenant_id": tenant_id,
            "total_approvals": total,
            "pending_count": status_counts.get(ApprovalStatus.PENDING, 0),
            "approved_count": status_counts.get(ApprovalStatus.APPROVED, 0),
            "rejected_count": status_counts.get(ApprovalStatus.REJECTED, 0),
            "delegated_count": status_counts.get(ApprovalStatus.DELEGATED, 0),
            "escalated_count": status_counts.get(ApprovalStatus.ESCALATED, 0),
            "expired_count": status_counts.get(ApprovalStatus.EXPIRED, 0),
        }

    @classmethod
    def get_expired_pending_approvals(cls, db: Session, now: datetime) -> List[Approval]:
        return db.query(Approval).filter(
            Approval.status == ApprovalStatus.PENDING,
            Approval.expires_at.isnot(None),
            Approval.expires_at <= now,
            Approval.is_deleted == False
        ).all()
