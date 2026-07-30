import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base
from app.models.mixins import SoftDeleteMixin


class VerificationStatus(str, enum.Enum):
    """
    Enum representing verification results during QR scans or gate checks.
    """
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    WRONG_TENANT = "WRONG_TENANT"
    ALREADY_CHECKED_IN = "ALREADY_CHECKED_IN"
    UNKNOWN_QR = "UNKNOWN_QR"
    PASS_EXPIRED = "PASS_EXPIRED"
    REQUEST_INVALID = "REQUEST_INVALID"
    VISITOR_INACTIVE = "VISITOR_INACTIVE"
    NOT_CHECKED_IN = "NOT_CHECKED_IN"


GateVerificationStatus = VerificationStatus



class CheckInStatus(str, enum.Enum):
    """
    Lifecycle status of a check-in record.
    """
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    UNDONE = "UNDONE"
    EXPIRED = "EXPIRED"


class CheckIn(Base, SoftDeleteMixin):
    """
    CheckIn domain model representing visitor entry/exit events,
    gate device metadata, and attendance tracking.
    """
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    pass_id = Column(Integer, ForeignKey("visitor_passes.id"), nullable=False, index=True)
    visit_request_id = Column(Integer, ForeignKey("visit_requests.id"), nullable=False, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.id"), nullable=False, index=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    checkin_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    checkout_time = Column(DateTime, nullable=True, index=True)
    status = Column(Enum(CheckInStatus), default=CheckInStatus.CHECKED_IN, nullable=False, index=True)

    # Gate Device Authenticated Metadata
    gate_device_id = Column(String(100), nullable=True, default="DEV-GATE-01")
    scanner_name = Column(String(100), nullable=True, default="Main Gate Scanner 1")
    scanner_ip = Column(String(50), nullable=True)
    scanner_location = Column(String(200), nullable=True, default="Main Gate Entrance")
    scanner_version = Column(String(50), nullable=True, default="v1.0.0")
    gate_name = Column(String(100), nullable=True, default="Main Gate")
    gate_number = Column(String(50), nullable=True, default="Gate 1")

    # Verification Method & Guard Actions
    verification_method = Column(String(50), default="QR_SCAN", nullable=False)
    checked_in_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_out_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checkin_notes = Column(Text, nullable=True)
    checkout_notes = Column(Text, nullable=True)

    is_manual_checkin = Column(Boolean, default=False, nullable=False)
    is_manual_checkout = Column(Boolean, default=False, nullable=False)
    manual_checkin_reason = Column(String(500), nullable=True)
    manual_checkout_reason = Column(String(500), nullable=True)

    # Automatically computed Attendance Duration
    visit_duration_minutes = Column(Float, nullable=True)
    visit_duration_seconds = Column(Integer, nullable=True)

    # Undo status tracking
    is_undone = Column(Boolean, default=False, nullable=False)
    undone_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    undone_at = Column(DateTime, nullable=True)
    undone_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    visitor_pass = relationship("VisitorPass", foreign_keys=[pass_id])
    visit_request = relationship("VisitRequest", foreign_keys=[visit_request_id])
    visitor = relationship("Visitor", foreign_keys=[visitor_id])
    host = relationship("User", foreign_keys=[host_id])
    checked_in_by_user = relationship("User", foreign_keys=[checked_in_by])
    checked_out_by_user = relationship("User", foreign_keys=[checked_out_by])
    undone_by_user = relationship("User", foreign_keys=[undone_by])


class ScanLog(Base):
    """
    Log of all QR scan attempts (both SUCCESS and FAILED) for security analytics.
    """
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    pass_id = Column(Integer, ForeignKey("visitor_passes.id"), nullable=True, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.id"), nullable=True, index=True)

    gate_device_id = Column(String(100), nullable=True)
    scanner_name = Column(String(100), nullable=True)
    scanner_ip = Column(String(50), nullable=True)

    qr_token = Column(Text, nullable=True)
    scan_result = Column(Enum(VerificationStatus), nullable=False, index=True)
    reason = Column(String(500), nullable=False)
    ip_address = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    visitor_pass = relationship("VisitorPass", foreign_keys=[pass_id])
    visitor = relationship("Visitor", foreign_keys=[visitor_id])


class GateEventHistory(Base):
    """
    Historical log table tracking every gate activity (CHECK_IN, CHECK_OUT, UNDO, MANUAL, OVERSTAY).
    """
    __tablename__ = "gate_event_history"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    checkin_id = Column(Integer, ForeignKey("checkins.id"), nullable=True, index=True)
    pass_id = Column(Integer, ForeignKey("visitor_passes.id"), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    gate_device_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    checkin = relationship("CheckIn", foreign_keys=[checkin_id])
    visitor_pass = relationship("VisitorPass", foreign_keys=[pass_id])
    performed_by_user = relationship("User", foreign_keys=[performed_by])
