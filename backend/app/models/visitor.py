import enum
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Date, DateTime, Enum, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from app.models.mixins import SoftDeleteMixin

class VisitorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    BLACKLISTED = "BLACKLISTED"

class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class VerificationMethod(str, enum.Enum):
    MANUAL = "MANUAL"
    OTP = "OTP"
    QR = "QR"
    AADHAAR = "AADHAAR"
    PASSPORT = "PASSPORT"
    DRIVING_LICENSE = "DRIVING_LICENSE"

class Visitor(Base, SoftDeleteMixin):
    __tablename__ = "visitors"
    __table_args__ = (
        Index("idx_visitor_tenant_code", "tenant_id", "visitor_code", unique=True),
        Index("idx_visitor_tenant_phone", "tenant_id", "phone"),
        Index("idx_visitor_tenant_email", "tenant_id", "email"),
        Index("idx_visitor_tenant_gov_id", "tenant_id", "government_id_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    visitor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    profile_photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    government_id_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    government_id_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    government_id_front: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    government_id_back: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    blacklisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blacklist_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="visitor_verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False
    )
    verification_method: Mapped[Optional[VerificationMethod]] = mapped_column(
        Enum(VerificationMethod, name="visitor_verification_method"),
        nullable=True
    )
    verification_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[VisitorStatus] = mapped_column(
        Enum(VisitorStatus, name="visitor_status"),
        default=VisitorStatus.ACTIVE,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(foreign_keys=[tenant_id])
    verifier: Mapped[Optional["User"]] = relationship(foreign_keys=[verified_by])
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by])
    deleter: Mapped[Optional["User"]] = relationship(foreign_keys=[deleted_by])
