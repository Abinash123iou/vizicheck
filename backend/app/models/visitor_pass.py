import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base
from app.models.mixins import SoftDeleteMixin


class PassStatus(str, enum.Enum):
    """
    Pass lifecycle statuses.
    """
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    USED = "USED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class VisitorPass(Base, SoftDeleteMixin):
    """
    VisitorPass domain model representing a physical/digital access pass
    generated for an approved Visit Request.
    """
    __tablename__ = "visitor_passes"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    visit_request_id = Column(Integer, ForeignKey("visit_requests.id"), nullable=False, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.id"), nullable=False, index=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    pass_code = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(Enum(PassStatus), default=PassStatus.ACTIVE, nullable=False, index=True)
    latest_qr_version = Column(Integer, default=1, nullable=False)
    
    valid_from = Column(DateTime, nullable=False, index=True)
    valid_until = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    visit_request = relationship("VisitRequest", foreign_keys=[visit_request_id])
    visitor = relationship("Visitor", foreign_keys=[visitor_id])
    host = relationship("User", foreign_keys=[host_id])
    revoked_by_user = relationship("User", foreign_keys=[revoked_by])
    creator = relationship("User", foreign_keys=[created_by])

    qr_tokens = relationship("QRToken", back_populates="pass_rel", cascade="all, delete-orphan")
    status_history = relationship("PassStatusHistory", back_populates="pass_rel", cascade="all, delete-orphan")


class PassStatusHistory(Base):
    """
    Historical log table tracking every state transition of a VisitorPass.
    """
    __tablename__ = "pass_status_history"

    id = Column(Integer, primary_key=True, index=True)
    pass_id = Column(Integer, ForeignKey("visitor_passes.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(Enum(PassStatus), nullable=True)
    new_status = Column(Enum(PassStatus), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remarks = Column(String(500), nullable=True)

    # Relationships
    pass_rel = relationship("VisitorPass", back_populates="status_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])
