from datetime import date, time
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.availability import HostAvailability, Weekday, AvailabilityException
from app.repositories.availability_repository import AvailabilityRepository
from app.core.exceptions import BusinessRuleException, AuthorizationException, NotFoundException



class AvailabilityValidator:
    """
    Validation engine for Host Availability management enforcing business rules, RBAC, tenant isolation, and time boundaries.
    """

    @classmethod
    def validate_tenant_boundary(cls, current_user: User, target_tenant_id: Optional[int] = None) -> int:
        """
        Enforce tenant isolation. Super Admins can access any tenant; other users are bound to their tenant.
        """
        role_name = current_user.role.name if current_user.role else ""
        if role_name == "SUPER_ADMIN":
            if target_tenant_id is not None:
                return target_tenant_id
            return current_user.tenant_id if current_user.tenant_id else 1
        
        if not current_user.tenant_id:
            raise AuthorizationException("User is not assigned to a tenant organization")

        if target_tenant_id and target_tenant_id != current_user.tenant_id:
            raise AuthorizationException(f"Access denied to tenant ID {target_tenant_id}")

        return current_user.tenant_id

    @classmethod
    def validate_host_user(cls, db: Session, target_tenant_id: int, host_id: int) -> User:
        """
        Verify that the target host user exists, belongs to the tenant, and is active.
        """
        host = db.query(User).filter(User.id == host_id, User.is_deleted == False).first()
        if not host:
            raise NotFoundException(f"Host User ID {host_id} not found")

        if host.tenant_id and host.tenant_id != target_tenant_id:
            raise BusinessRuleException(f"Host User ID {host_id} does not belong to Tenant ID {target_tenant_id}")

        if not host.is_active:
            raise BusinessRuleException(f"Host User ID {host_id} is inactive")

        return host

    @classmethod
    def validate_management_permissions(cls, current_user: User, target_tenant_id: int, host_id: Optional[int] = None) -> None:
        """
        Verify that current user is authorized to modify schedule (Super Admin, Tenant Admin, or the Host themselves).
        """
        role_name = current_user.role.name if current_user.role else ""
        if role_name == "SUPER_ADMIN":
            return

        if current_user.tenant_id != target_tenant_id:
            raise AuthorizationException("Tenant isolation violation")

        if role_name == "TENANT_ADMIN":
            return

        # If user is editing their own schedule
        if host_id and current_user.id == host_id:
            return

        raise AuthorizationException("Only Tenant Admins or the Host can modify availability schedules")

    @classmethod
    def validate_time_boundaries(
        cls,
        start_time: time,
        end_time: time,
        break_start: Optional[time] = None,
        break_end: Optional[time] = None
    ) -> None:
        """
        Validate working hours and break bounds.
        """
        if end_time <= start_time:
            raise BusinessRuleException(f"End time ({end_time}) must be after start time ({start_time})")

        if (break_start is not None and break_end is None) or (break_start is None and break_end is not None):
            raise BusinessRuleException("Both break start and break end must be specified together")

        if break_start and break_end:
            if break_end <= break_start:
                raise BusinessRuleException(f"Break end time ({break_end}) must be after break start time ({break_start})")

            if break_start < start_time or break_end > end_time:
                raise BusinessRuleException(
                    f"Break timing ({break_start} - {break_end}) must fall entirely inside working hours ({start_time} - {end_time})"
                )

    @classmethod
    def validate_effective_dates(cls, effective_from: Optional[date] = None, effective_until: Optional[date] = None) -> None:
        """
        Validate validity date range.
        """
        if effective_from and effective_until and effective_until < effective_from:
            raise BusinessRuleException(f"Effective until date ({effective_until}) cannot be prior to effective from date ({effective_from})")

    @classmethod
    def validate_schedule_overlap(
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
    ) -> None:
        """
        Verify no overlapping schedule exists for the same host on the same weekday.
        """
        overlapping = AvailabilityRepository.find_overlapping_schedules(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            effective_from=effective_from,
            effective_until=effective_until,
            exclude_id=exclude_id
        )

        if overlapping:
            conflict = overlapping[0]
            raise BusinessRuleException(
                f"Host ID {user_id} already has an overlapping availability schedule (ID: {conflict.id}, {conflict.start_time} - {conflict.end_time}) on {weekday.value}"
            )

