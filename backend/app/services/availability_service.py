from datetime import date, time, datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.availability import HostAvailability, AvailabilityException, Weekday, RecurrenceType
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.schemas.availability import (
    HostAvailabilityCreate,
    HostAvailabilityUpdate,
    HostAvailabilityResponse,
    AvailabilityExceptionCreate,
    AvailabilityExceptionResponse,
    HostSlotCheckResponse,
    TimeSlot
)
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.availability_validator import AvailabilityValidator
from app.mappers.availability_mapper import AvailabilityMapper
from app.constants.audit_actions import AuditActions
from app.core.exceptions import NotFoundException, BusinessRuleException



class AvailabilityService:
    """
    Business service layer managing host working availability schedules, holiday/leave exceptions, conflict detection, and slot generation.
    """

    @classmethod
    def create_availability(
        cls,
        db: Session,
        current_user: User,
        data: HostAvailabilityCreate
    ) -> HostAvailabilityResponse:
        """
        Create a new host availability schedule with full business validation.
        """
        target_tenant_id = AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=data.tenant_id
        )

        host = AvailabilityValidator.validate_host_user(
            db=db,
            target_tenant_id=target_tenant_id,
            host_id=data.user_id
        )

        AvailabilityValidator.validate_management_permissions(
            current_user=current_user,
            target_tenant_id=target_tenant_id,
            host_id=data.user_id
        )

        AvailabilityValidator.validate_time_boundaries(
            start_time=data.start_time,
            end_time=data.end_time,
            break_start=data.break_start,
            break_end=data.break_end
        )

        AvailabilityValidator.validate_effective_dates(
            effective_from=data.effective_from,
            effective_until=data.effective_until
        )

        AvailabilityValidator.validate_schedule_overlap(
            db=db,
            tenant_id=target_tenant_id,
            user_id=data.user_id,
            weekday=data.weekday,
            start_time=data.start_time,
            end_time=data.end_time,
            effective_from=data.effective_from,
            effective_until=data.effective_until
        )

        availability = HostAvailability(
            tenant_id=target_tenant_id,
            user_id=data.user_id,
            weekday=data.weekday,
            start_time=data.start_time,
            end_time=data.end_time,
            break_start=data.break_start,
            break_end=data.break_end,
            max_visitors=data.max_visitors,
            is_available=data.is_available,
            effective_from=data.effective_from,
            effective_until=data.effective_until,
            recurrence_type=data.recurrence_type,
            notes=data.notes,
            created_by_id=current_user.id
        )

        created_item = AvailabilityRepository.create_availability(db=db, availability=availability)

        # Log Audit Trail
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.AVAILABILITY_CREATED,
            module="AVAILABILITY_MANAGEMENT",
            entity_id=created_item.id,
            new_value={
                "host_id": data.user_id,
                "weekday": data.weekday.value,
                "start_time": str(data.start_time),
                "end_time": str(data.end_time)
            }
        )


        return AvailabilityMapper.to_response(created_item)

    @classmethod
    def list_availabilities(
        cls,
        db: Session,
        current_user: User,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        weekday: Optional[Weekday] = None,
        is_available: Optional[bool] = None,
        target_date: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[HostAvailabilityResponse], int]:
        target_tenant_id = AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=tenant_id
        )

        items, total_count = AvailabilityRepository.list_availabilities(
            db=db,
            tenant_id=target_tenant_id,
            user_id=user_id,
            weekday=weekday,
            is_available=is_available,
            target_date=target_date,
            search=search,
            page=page,
            page_size=page_size
        )

        return AvailabilityMapper.to_response_list(items), total_count

    @classmethod
    def get_availability(
        cls,
        db: Session,
        current_user: User,
        availability_id: int
    ) -> HostAvailabilityResponse:
        item = AvailabilityRepository.get_by_id(db=db, availability_id=availability_id)
        if not item:
            raise NotFoundException(f"Availability schedule ID {availability_id} not found")

        AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=item.tenant_id
        )

        return AvailabilityMapper.to_response(item)

    @classmethod
    def update_availability(
        cls,
        db: Session,
        current_user: User,
        availability_id: int,
        data: HostAvailabilityUpdate
    ) -> HostAvailabilityResponse:
        item = AvailabilityRepository.get_by_id(db=db, availability_id=availability_id)
        if not item:
            raise NotFoundException(f"Availability schedule ID {availability_id} not found")

        AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=item.tenant_id
        )

        AvailabilityValidator.validate_management_permissions(
            current_user=current_user,
            target_tenant_id=item.tenant_id,
            host_id=item.user_id
        )

        new_weekday = data.weekday if data.weekday is not None else item.weekday
        new_start_time = data.start_time if data.start_time is not None else item.start_time
        new_end_time = data.end_time if data.end_time is not None else item.end_time
        new_break_start = data.break_start if data.break_start is not None else item.break_start
        new_break_end = data.break_end if data.break_end is not None else item.break_end
        new_eff_from = data.effective_from if data.effective_from is not None else item.effective_from
        new_eff_until = data.effective_until if data.effective_until is not None else item.effective_until

        AvailabilityValidator.validate_time_boundaries(
            start_time=new_start_time,
            end_time=new_end_time,
            break_start=new_break_start,
            break_end=new_break_end
        )

        AvailabilityValidator.validate_effective_dates(
            effective_from=new_eff_from,
            effective_until=new_eff_until
        )

        AvailabilityValidator.validate_schedule_overlap(
            db=db,
            tenant_id=item.tenant_id,
            user_id=item.user_id,
            weekday=new_weekday,
            start_time=new_start_time,
            end_time=new_end_time,
            effective_from=new_eff_from,
            effective_until=new_eff_until,
            exclude_id=item.id
        )

        if data.weekday is not None:
            item.weekday = data.weekday
        if data.start_time is not None:
            item.start_time = data.start_time
        if data.end_time is not None:
            item.end_time = data.end_time
        if data.break_start is not None:
            item.break_start = data.break_start
        if data.break_end is not None:
            item.break_end = data.break_end
        if data.max_visitors is not None:
            item.max_visitors = data.max_visitors
        if data.is_available is not None:
            item.is_available = data.is_available
        if data.effective_from is not None:
            item.effective_from = data.effective_from
        if data.effective_until is not None:
            item.effective_until = data.effective_until
        if data.recurrence_type is not None:
            item.recurrence_type = data.recurrence_type
        if data.notes is not None:
            item.notes = data.notes

        item.updated_by_id = current_user.id
        updated_item = AvailabilityRepository.update_availability(db=db, availability=item)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.AVAILABILITY_UPDATED,
            module="AVAILABILITY_MANAGEMENT",
            entity_id=updated_item.id,
            new_value={"host_id": item.user_id, "updated_fields": list(data.model_dump(exclude_unset=True).keys())}
        )

        return AvailabilityMapper.to_response(updated_item)

    @classmethod
    def delete_availability(
        cls,
        db: Session,
        current_user: User,
        availability_id: int
    ) -> None:
        item = AvailabilityRepository.get_by_id(db=db, availability_id=availability_id)
        if not item:
            raise NotFoundException(f"Availability schedule ID {availability_id} not found")

        AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=item.tenant_id
        )

        AvailabilityValidator.validate_management_permissions(
            current_user=current_user,
            target_tenant_id=item.tenant_id,
            host_id=item.user_id
        )

        AvailabilityRepository.delete_availability(db=db, availability=item, deleted_by_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.AVAILABILITY_DELETED,
            module="AVAILABILITY_MANAGEMENT",
            entity_id=availability_id,
            new_value={"host_id": item.user_id}
        )



    @classmethod
    def check_host_availability_slots(
        cls,
        db: Session,
        current_user: User,
        host_id: int,
        target_date: date,
        slot_duration_minutes: int = 30
    ) -> HostSlotCheckResponse:
        """
        Calculates available booking time slots for a host on a specific date.
        Takes into account:
        1. Host working schedule
        2. Break times
        3. Company holidays & host leave exceptions
        4. Maximum visitor capacity per slot
        5. Existing visit request bookings on that date
        """
        target_tenant_id = AvailabilityValidator.validate_tenant_boundary(current_user=current_user)
        host = AvailabilityValidator.validate_host_user(db=db, target_tenant_id=target_tenant_id, host_id=host_id)
        host_name = f"{host.first_name} {host.last_name}".strip()

        # Map date to Weekday enum
        weekday_map = {
            0: Weekday.MONDAY,
            1: Weekday.TUESDAY,
            2: Weekday.WEDNESDAY,
            3: Weekday.THURSDAY,
            4: Weekday.FRIDAY,
            5: Weekday.SATURDAY,
            6: Weekday.SUNDAY
        }
        target_weekday = weekday_map[target_date.weekday()]

        # 1. Check for exceptions (company holiday or personal leave)
        exceptions = AvailabilityRepository.list_exceptions(
            db=db,
            tenant_id=target_tenant_id,
            user_id=host_id,
            start_date=target_date,
            end_date=target_date
        )

        full_day_exception = next((e for e in exceptions if e.is_full_day), None)
        if full_day_exception:
            return HostSlotCheckResponse(
                host_id=host_id,
                host_name=host_name,
                date=target_date,
                weekday=target_weekday,
                is_working_day=False,
                slots=[TimeSlot(
                    start_time="00:00:00",
                    end_time="23:59:59",
                    is_available=False,
                    reason=f"Unavailable ({full_day_exception.title})",
                    remaining_capacity=0
                )]
            )

        # 2. Get host working schedules for date & weekday
        schedules = AvailabilityRepository.get_host_schedules_for_date_and_weekday(
            db=db,
            tenant_id=target_tenant_id,
            user_id=host_id,
            weekday=target_weekday,
            target_date=target_date
        )

        if not schedules:
            return HostSlotCheckResponse(
                host_id=host_id,
                host_name=host_name,
                date=target_date,
                weekday=target_weekday,
                is_working_day=False,
                slots=[]
            )

        # 3. Get existing visit requests for this host on target date to compute booked slots
        day_start_dt = datetime.combine(target_date, time.min)
        day_end_dt = datetime.combine(target_date, time.max)
        existing_requests = db.query(VisitRequest).filter(
            VisitRequest.tenant_id == target_tenant_id,
            VisitRequest.host_id == host_id,
            VisitRequest.is_deleted == False,
            VisitRequest.status.in_([VisitRequestStatus.PENDING, VisitRequestStatus.APPROVED, VisitRequestStatus.CHECKED_IN]),
            VisitRequest.scheduled_start_time < day_end_dt,
            VisitRequest.scheduled_end_time > day_start_dt
        ).all()

        slots_list: List[TimeSlot] = []
        schedule = schedules[0] # Primary schedule for weekday

        curr_dt = datetime.combine(target_date, schedule.start_time)
        end_dt = datetime.combine(target_date, schedule.end_time)
        delta = timedelta(minutes=slot_duration_minutes)

        while curr_dt + delta <= end_dt:
            slot_start_time = curr_dt.time()
            slot_end_time = (curr_dt + delta).time()

            is_slot_avail = True
            unavail_reason = None

            # Check break time overlap
            if schedule.break_start and schedule.break_end:
                if (slot_start_time < schedule.break_end) and (slot_end_time > schedule.break_start):
                    is_slot_avail = False
                    unavail_reason = "Scheduled Lunch / Break"

            # Check partial day exceptions
            if is_slot_avail and exceptions:
                for exc in exceptions:
                    if not exc.is_full_day and exc.start_time and exc.end_time:
                        if (slot_start_time < exc.end_time) and (slot_end_time > exc.start_time):
                            is_slot_avail = False
                            unavail_reason = f"Unavailable ({exc.title})"
                            break

            # Calculate remaining visitor capacity
            slot_start_datetime = curr_dt
            slot_end_datetime = curr_dt + delta
            booked_count = sum(
                1 for req in existing_requests
                if (req.scheduled_start_time < slot_end_datetime) and (req.scheduled_end_time > slot_start_datetime)
            )

            remaining_cap = max(0, schedule.max_visitors - booked_count)
            if remaining_cap <= 0:
                is_slot_avail = False
                unavail_reason = "Slot Fully Booked"

            slots_list.append(TimeSlot(
                start_time=slot_start_time.strftime("%H:%M:%S"),
                end_time=slot_end_time.strftime("%H:%M:%S"),
                is_available=is_slot_avail,
                reason=unavail_reason,
                remaining_capacity=remaining_cap
            ))

            curr_dt += delta

        return HostSlotCheckResponse(
            host_id=host_id,
            host_name=host_name,
            date=target_date,
            weekday=target_weekday,
            is_working_day=True,
            working_start=schedule.start_time.strftime("%H:%M:%S"),
            working_end=schedule.end_time.strftime("%H:%M:%S"),
            break_start=schedule.break_start.strftime("%H:%M:%S") if schedule.break_start else None,
            break_end=schedule.break_end.strftime("%H:%M:%S") if schedule.break_end else None,
            slots=slots_list
        )

    # Exception Management Service Methods
    @classmethod
    def create_exception(
        cls,
        db: Session,
        current_user: User,
        data: AvailabilityExceptionCreate
    ) -> AvailabilityExceptionResponse:
        target_tenant_id = AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=data.tenant_id
        )

        if data.user_id:
            AvailabilityValidator.validate_host_user(
                db=db,
                target_tenant_id=target_tenant_id,
                host_id=data.user_id
            )

        AvailabilityValidator.validate_management_permissions(
            current_user=current_user,
            target_tenant_id=target_tenant_id,
            host_id=data.user_id
        )

        if data.end_date < data.start_date:
            raise BusinessRuleException(f"End date ({data.end_date}) cannot be before start date ({data.start_date})")


        exception = AvailabilityException(
            tenant_id=target_tenant_id,
            user_id=data.user_id,
            title=data.title,
            exception_type=data.exception_type,
            start_date=data.start_date,
            end_date=data.end_date,
            is_full_day=data.is_full_day,
            start_time=data.start_time,
            end_time=data.end_time,
            notes=data.notes,
            created_by_id=current_user.id
        )

        created_exception = AvailabilityRepository.create_exception(db=db, exception=exception)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.AVAILABILITY_EXCEPTION_CREATED,
            module="AVAILABILITY_MANAGEMENT",
            entity_id=created_exception.id,
            new_value={"title": data.title, "type": data.exception_type.value}
        )

        return AvailabilityMapper.to_exception_response(created_exception)

    @classmethod
    def list_exceptions(
        cls,
        db: Session,
        current_user: User,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AvailabilityExceptionResponse]:
        target_tenant_id = AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=tenant_id
        )

        items = AvailabilityRepository.list_exceptions(
            db=db,
            tenant_id=target_tenant_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        return AvailabilityMapper.to_exception_response_list(items)

    @classmethod
    def delete_exception(
        cls,
        db: Session,
        current_user: User,
        exception_id: int
    ) -> None:
        item = AvailabilityRepository.get_exception_by_id(db=db, exception_id=exception_id)
        if not item:
            raise NotFoundException(f"Availability Exception ID {exception_id} not found")

        AvailabilityValidator.validate_tenant_boundary(
            current_user=current_user,
            target_tenant_id=item.tenant_id
        )

        AvailabilityValidator.validate_management_permissions(
            current_user=current_user,
            target_tenant_id=item.tenant_id,
            host_id=item.user_id
        )

        AvailabilityRepository.delete_exception(db=db, exception=item, deleted_by_id=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.AVAILABILITY_EXCEPTION_DELETED,
            module="AVAILABILITY_MANAGEMENT",
            entity_id=exception_id,
            new_value={"title": item.title}
        )

