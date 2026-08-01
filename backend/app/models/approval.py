import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Enum, ForeignKey, DateTime, Integer, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from app.models.mixins import SoftDeleteMixin


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"
    ESCALATED = "ESCALATED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalAction(str, enum.Enum):
    CREATED = "CREATED"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DELEGATE = "DELEGATE"
    ESCALATE = "ESCALATE"
    REMIND = "REMIND"
    EXPIRE = "EXPIRE"
    CANCEL = "CANCEL"


class ApprovalType(str, enum.Enum):
    SINGLE_LEVEL = "SINGLE_LEVEL"
    MULTI_LEVEL = "MULTI_LEVEL"


class Approval(Base, SoftDeleteMixin):
    __tablename__ = "approvals"
    __table_args__ = (
        Index("idx_approval_tenant_code", "tenant_id", "approval_code", unique=True),
        Index("idx_approval_tenant_status", "tenant_id", "status"),
        Index("idx_approval_request", "tenant_id", "request_id"),
        Index("idx_approval_approver", "tenant_id", "current_approver_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("visit_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    approval_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    approval_type: Mapped[ApprovalType] = mapped_column(
        Enum(ApprovalType, name="approval_type"),
        default=ApprovalType.SINGLE_LEVEL,
        nullable=False
    )
    
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    current_approver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status"),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(foreign_keys=[tenant_id])
    visit_request: Mapped["VisitRequest"] = relationship(foreign_keys=[request_id])
    current_approver: Mapped["User"] = relationship(foreign_keys=[current_approver_id])
    history_entries: Mapped[List["ApprovalHistory"]] = relationship("ApprovalHistory", back_populates="approval", cascade="all, delete-orphan")


class ApprovalHistory(Base):
    __tablename__ = "approval_histories"
    __table_args__ = (
        Index("idx_approval_history_tenant_approval", "tenant_id", "approval_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    approval_id: Mapped[int] = mapped_column(ForeignKey("approvals.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    step_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, name="approval_action"),
        nullable=False
    )
    previous_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_history_prev_status"),
        nullable=False
    )
    new_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_history_new_status"),
        nullable=False
    )
    
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delegated_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    approval: Mapped["Approval"] = relationship("Approval", back_populates="history_entries")
    actor: Mapped["User"] = relationship(foreign_keys=[actor_id])
    delegated_to: Mapped[Optional["User"]] = relationship(foreign_keys=[delegated_to_id])
