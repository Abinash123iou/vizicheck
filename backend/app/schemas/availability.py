from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.availability import Weekday, RecurrenceType, ExceptionType


class HostAvailabilityCreate(BaseModel):
    """Schema for creating a host availability schedule."""
    tenant_id: Optional[int] = Field(None, description="Target Tenant ID (derived from user context if omitted)")
    user_id: int = Field(..., description="Target Host User ID")
    weekday: Weekday = Field(..., description="Day of the week (MONDAY..SUNDAY)")
    start_time: time = Field(..., description="Working hours start time (e.g. 09:00:00)")
    end_time: time = Field(..., description="Working hours end time (e.g. 17:00:00)")
    break_start: Optional[time] = Field(None, description="Lunch/break start time (e.g. 13:00:00)")
    break_end: Optional[time] = Field(None, description="Lunch/break end time (e.g. 14:00:00)")
    max_visitors: int = Field(5, ge=1, le=100, description="Maximum visitor slots per hour/slot")
    is_available: bool = Field(True, description="Whether host is available on this day")
    effective_from: Optional[date] = Field(None, description="Schedule start validity date")
    effective_until: Optional[date] = Field(None, description="Schedule end validity date")
    recurrence_type: RecurrenceType = Field(RecurrenceType.WEEKLY, description="Recurrence type")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

    model_config = ConfigDict(from_attributes=True)


class HostAvailabilityUpdate(BaseModel):
    """Schema for updating an existing host availability schedule."""
    weekday: Optional[Weekday] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    max_visitors: Optional[int] = Field(None, ge=1, le=100)
    is_available: Optional[bool] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    recurrence_type: Optional[RecurrenceType] = None
    notes: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class HostAvailabilityResponse(BaseModel):
    """Schema for host availability schedule response."""
    id: int
    tenant_id: int
    user_id: int
    host_name: Optional[str] = None
    host_email: Optional[str] = None
    weekday: Weekday
    start_time: str
    end_time: str
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    max_visitors: int
    is_available: bool
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    recurrence_type: RecurrenceType
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AvailabilityExceptionCreate(BaseModel):
    """Schema for creating a holiday, leave, or maintenance exception."""
    tenant_id: Optional[int] = Field(None, description="Tenant ID")
    user_id: Optional[int] = Field(None, description="Host User ID (NULL for tenant-wide company holiday)")
    title: str = Field(..., min_length=2, max_length=255, description="Exception title/reason")
    exception_type: ExceptionType = Field(ExceptionType.HOLIDAY, description="Category of exception")
    start_date: date = Field(..., description="Exception start date")
    end_date: date = Field(..., description="Exception end date")
    is_full_day: bool = Field(True, description="Whether exception applies to full working day")
    start_time: Optional[time] = Field(None, description="Start time if partial day")
    end_time: Optional[time] = Field(None, description="End time if partial day")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


class AvailabilityExceptionResponse(BaseModel):
    """Schema for exception response."""
    id: int
    tenant_id: int
    user_id: Optional[int] = None
    host_name: Optional[str] = None
    title: str
    exception_type: ExceptionType
    start_date: date
    end_date: date
    is_full_day: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeSlot(BaseModel):
    """Schema for a calculated available booking slot."""
    start_time: str
    end_time: str
    is_available: bool
    reason: Optional[str] = None
    remaining_capacity: int = 5


class HostSlotCheckResponse(BaseModel):
    """Schema for host available slots on a target date."""
    host_id: int
    host_name: str
    date: date
    weekday: Weekday
    is_working_day: bool
    working_start: Optional[str] = None
    working_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    slots: List[TimeSlot] = []
