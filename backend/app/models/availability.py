import enum
from datetime import date, time, datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Date, Time, DateTime, Enum, ForeignKey, Integer, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from app.models.mixins import SoftDeleteMixin


class Weekday(str, enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class RecurrenceType(str, enum.Enum):
    WEEKLY = "WEEKLY"
    DAILY = "DAILY"
    ONCE = "ONCE"
    CUSTOM = "CUSTOM"


class ExceptionType(str, enum.Enum):
    HOLIDAY = "HOLIDAY"
    PERSONAL_LEAVE = "PERSONAL_LEAVE"
    SICK_LEAVE = "SICK_LEAVE"
    EMERGENCY_LEAVE = "EMERGENCY_LEAVE"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"


class HostAvailability(Base, SoftDeleteMixin):
    """
    Host availability schedule defining working hours, breaks, and capacity per weekday.
    """
    __tablename__ = "host_availability"
    __table_args__ = (
        Index("idx_availability_tenant_user", "tenant_id", "user_id"),
        Index("idx_availability_tenant_user_weekday", "tenant_id", "user_id", "weekday"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    weekday: Mapped[Weekday] = mapped_column(
        Enum(Weekday, name="availability_weekday"),
        nullable=False,
        index=True
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    break_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    break_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    max_visitors: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    recurrence_type: Mapped[RecurrenceType] = mapped_column(
        Enum(RecurrenceType, name="availability_recurrence_type"),
        default=RecurrenceType.WEEKLY,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id])
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    updated_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_id])


class AvailabilityException(Base, SoftDeleteMixin):
    """
    Supporting table for public holidays, personal leave, sick leave, and maintenance days.
    """
    __tablename__ = "availability_exceptions"
    __table_args__ = (
        Index("idx_exception_tenant_user", "tenant_id", "user_id"),
        Index("idx_exception_dates", "tenant_id", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    exception_type: Mapped[ExceptionType] = mapped_column(
        Enum(ExceptionType, name="availability_exception_type"),
        default=ExceptionType.HOLIDAY,
        nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    is_full_day: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", foreign_keys=[tenant_id])
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
