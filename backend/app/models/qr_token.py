from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base


class QRToken(Base):
    """
    QRToken model representing cryptographically signed JWT tokens
    and versions linked to a VisitorPass.
    """
    __tablename__ = "qr_tokens"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    pass_id = Column(Integer, ForeignKey("visitor_passes.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    pass_rel = relationship("VisitorPass", back_populates="qr_tokens")
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
