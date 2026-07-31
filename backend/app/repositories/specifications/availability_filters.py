from datetime import date
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Query
from app.models.availability import HostAvailability, Weekday
from app.models.user import User


class AvailabilityFilterSpec:
    """
    Specification query filter builder for Host Availability queries.
    """

    @classmethod
    def apply_filters(
        cls,
        query: Query,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        weekday: Optional[Weekday] = None,
        is_available: Optional[bool] = None,
        target_date: Optional[date] = None,
        search: Optional[str] = None
    ) -> Query:
        """
        Applies filter criteria to HostAvailability SQLAlchemy query.
        """
        # Exclude soft deleted records
        query = query.filter(HostAvailability.is_deleted == False)

        if tenant_id is not None:
            query = query.filter(HostAvailability.tenant_id == tenant_id)

        if user_id is not None:
            query = query.filter(HostAvailability.user_id == user_id)

        if weekday is not None:
            query = query.filter(HostAvailability.weekday == weekday)

        if is_available is not None:
            query = query.filter(HostAvailability.is_available == is_available)

        if target_date is not None:
            query = query.filter(
                or_(
                    HostAvailability.effective_from == None,
                    HostAvailability.effective_from <= target_date
                ),
                or_(
                    HostAvailability.effective_until == None,
                    HostAvailability.effective_until >= target_date
                )
            )

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.join(HostAvailability.user).filter(
                or_(
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    HostAvailability.notes.ilike(search_pattern)
                )
            )

        return query
