from datetime import date, time
from typing import Optional, List, Tuple
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload
from app.models.availability import HostAvailability, AvailabilityException, Weekday
from app.repositories.specifications.availability_filters import AvailabilityFilterSpec


class AvailabilityRepository:
    """
    Repository layer handling database operations for HostAvailability and AvailabilityException entities.
    """

    @classmethod
    def create_availability(cls, db: Session, availability: HostAvailability) -> HostAvailability:
        db.add(availability)
        db.commit()
        db.refresh(availability)
        return availability

    @classmethod
    def get_by_id(cls, db: Session, availability_id: int) -> Optional[HostAvailability]:
        return db.query(HostAvailability).options(
            joinedload(HostAvailability.user),
            joinedload(HostAvailability.tenant)
        ).filter(
            HostAvailability.id == availability_id,
            HostAvailability.is_deleted == False
        ).first()

    @classmethod
    def list_availabilities(
        cls,
        db: Session,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        weekday: Optional[Weekday] = None,
        is_available: Optional[bool] = None,
        target_date: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[HostAvailability], int]:
        query = db.query(HostAvailability).options(
            joinedload(HostAvailability.user)
        )

        query = AvailabilityFilterSpec.apply_filters(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
            weekday=weekday,
            is_available=is_available,
            target_date=target_date,
            search=search
        )

        total_count = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(HostAvailability.weekday, HostAvailability.start_time).offset(offset).limit(page_size).all()

        return items, total_count

    @classmethod
    def update_availability(cls, db: Session, availability: HostAvailability) -> HostAvailability:
        db.commit()
        db.refresh(availability)
        return availability

    @classmethod
    def delete_availability(cls, db: Session, availability: HostAvailability, deleted_by_id: Optional[int] = None) -> None:
        availability.delete()
        if deleted_by_id:
            availability.deleted_by_id = deleted_by_id
        db.commit()


    @classmethod
    def find_overlapping_schedules(
        cls,
        db: Session,
        tenant_id: int,
        user_id: int,
        weekday: Weekday,
        start_time: time,
        end_time: time,
        effective_from: Optional[date] = None,
        effective_until: Optional[date] = None,
        exclude_id: Optional[int] = None
    ) -> List[HostAvailability]:
        """
        Check for overlapping schedules for the same host on the same weekday.
        Overlapping time condition: (new_start < existing_end) AND (new_end > existing_start)
        """
        query = db.query(HostAvailability).filter(
            HostAvailability.tenant_id == tenant_id,
            HostAvailability.user_id == user_id,
            HostAvailability.weekday == weekday,
            HostAvailability.is_deleted == False,
            HostAvailability.start_time < end_time,
            HostAvailability.end_time > start_time
        )

        if exclude_id is not None:
            query = query.filter(HostAvailability.id != exclude_id)

        # Date window overlap filter if effective dates are specified
        if effective_from is not None or effective_until is not None:
            if effective_from is not None:
                query = query.filter(
                    or_(
                        HostAvailability.effective_until == None,
                        HostAvailability.effective_until >= effective_from
                    )
                )
            if effective_until is not None:
                query = query.filter(
                    or_(
                        HostAvailability.effective_from == None,
                        HostAvailability.effective_from <= effective_until
                    )
                )

        return query.all()

    @classmethod
    def get_host_schedules_for_date_and_weekday(
        cls,
        db: Session,
        tenant_id: int,
        user_id: int,
        weekday: Weekday,
        target_date: date
    ) -> List[HostAvailability]:
        return db.query(HostAvailability).filter(
            HostAvailability.tenant_id == tenant_id,
            HostAvailability.user_id == user_id,
            HostAvailability.weekday == weekday,
            HostAvailability.is_available == True,
            HostAvailability.is_deleted == False,
            or_(
                HostAvailability.effective_from == None,
                HostAvailability.effective_from <= target_date
            ),
            or_(
                HostAvailability.effective_until == None,
                HostAvailability.effective_until >= target_date
            )
        ).order_by(HostAvailability.start_time).all()

    # Exception Handling Methods
    @classmethod
    def create_exception(cls, db: Session, exception: AvailabilityException) -> AvailabilityException:
        db.add(exception)
        db.commit()
        db.refresh(exception)
        return exception

    @classmethod
    def get_exception_by_id(cls, db: Session, exception_id: int) -> Optional[AvailabilityException]:
        return db.query(AvailabilityException).options(
            joinedload(AvailabilityException.user)
        ).filter(
            AvailabilityException.id == exception_id,
            AvailabilityException.is_deleted == False
        ).first()

    @classmethod
    def list_exceptions(
        cls,
        db: Session,
        tenant_id: int,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AvailabilityException]:
        query = db.query(AvailabilityException).options(
            joinedload(AvailabilityException.user)
        ).filter(
            AvailabilityException.tenant_id == tenant_id,
            AvailabilityException.is_deleted == False
        )

        if user_id is not None:
            # Include both company-wide holidays (user_id IS NULL) and host-specific leaves
            query = query.filter(
                or_(
                    AvailabilityException.user_id == None,
                    AvailabilityException.user_id == user_id
                )
            )

        if start_date is not None:
            query = query.filter(AvailabilityException.end_date >= start_date)

        if end_date is not None:
            query = query.filter(AvailabilityException.start_date <= end_date)

        return query.order_by(AvailabilityException.start_date).all()

    @classmethod
    def delete_exception(cls, db: Session, exception: AvailabilityException, deleted_by_id: Optional[int] = None) -> None:
        exception.delete()
        if deleted_by_id:
            exception.created_by_id = deleted_by_id
        db.commit()

