import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Enum, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from app.models.mixins import SoftDeleteMixin

class VisitRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"

class VisitRequest(Base, SoftDeleteMixin):
    __tablename__ = "visit_requests"
    __table_args__ = (
        Index("idx_visit_request_tenant_code", "tenant_id", "request_code", unique=True),
        Index("idx_visit_request_tenant_status", "tenant_id", "status"),
        Index("idx_visit_request_tenant_times", "tenant_id", "scheduled_start_time", "scheduled_end_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    request_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitors.id", ondelete="CASCADE"), nullable=False, index=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    scheduled_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    scheduled_end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    actual_checkin: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_checkout: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    additional_visitors_count: Mapped[int] = mapped_column(default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[VisitRequestStatus] = mapped_column(
        Enum(VisitRequestStatus, name="visit_request_status"),
        default=VisitRequestStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Audit & Approval tracking fields
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    rejected_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    cancelled_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(foreign_keys=[tenant_id])
    visitor: Mapped["Visitor"] = relationship(foreign_keys=[visitor_id])
    host: Mapped["User"] = relationship(foreign_keys=[host_id])
    approver: Mapped[Optional["User"]] = relationship(foreign_keys=[approved_by])
    rejecter: Mapped[Optional["User"]] = relationship(foreign_keys=[rejected_by])
    canceller: Mapped[Optional["User"]] = relationship(foreign_keys=[cancelled_by])
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by])
