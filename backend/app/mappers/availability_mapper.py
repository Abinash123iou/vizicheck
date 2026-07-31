from typing import List, Optional
from app.models.availability import HostAvailability, AvailabilityException
from app.schemas.availability import HostAvailabilityResponse, AvailabilityExceptionResponse


class AvailabilityMapper:
    """
    Data Mapper for converting HostAvailability and AvailabilityException entities to DTO responses.
    """

    @classmethod
    def to_response(cls, entity: HostAvailability) -> HostAvailabilityResponse:
        host_name = None
        host_email = None
        if entity.user:
            host_name = f"{entity.user.first_name} {entity.user.last_name}".strip()
            host_email = entity.user.email

        return HostAvailabilityResponse(
            id=entity.id,
            tenant_id=entity.tenant_id,
            user_id=entity.user_id,
            host_name=host_name,
            host_email=host_email,
            weekday=entity.weekday,
            start_time=entity.start_time.strftime("%H:%M:%S") if entity.start_time else "",
            end_time=entity.end_time.strftime("%H:%M:%S") if entity.end_time else "",
            break_start=entity.break_start.strftime("%H:%M:%S") if entity.break_start else None,
            break_end=entity.break_end.strftime("%H:%M:%S") if entity.break_end else None,
            max_visitors=entity.max_visitors,
            is_available=entity.is_available,
            effective_from=entity.effective_from,
            effective_until=entity.effective_until,
            recurrence_type=entity.recurrence_type,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @classmethod
    def to_response_list(cls, entities: List[HostAvailability]) -> List[HostAvailabilityResponse]:
        return [cls.to_response(e) for e in entities]

    @classmethod
    def to_exception_response(cls, entity: AvailabilityException) -> AvailabilityExceptionResponse:
        host_name = None
        if entity.user:
            host_name = f"{entity.user.first_name} {entity.user.last_name}".strip()

        return AvailabilityExceptionResponse(
            id=entity.id,
            tenant_id=entity.tenant_id,
            user_id=entity.user_id,
            host_name=host_name,
            title=entity.title,
            exception_type=entity.exception_type,
            start_date=entity.start_date,
            end_date=entity.end_date,
            is_full_day=entity.is_full_day,
            start_time=entity.start_time.strftime("%H:%M:%S") if entity.start_time else None,
            end_time=entity.end_time.strftime("%H:%M:%S") if entity.end_time else None,
            notes=entity.notes,
            created_at=entity.created_at
        )

    @classmethod
    def to_exception_response_list(cls, entities: List[AvailabilityException]) -> List[AvailabilityExceptionResponse]:
        return [cls.to_exception_response(e) for e in entities]
