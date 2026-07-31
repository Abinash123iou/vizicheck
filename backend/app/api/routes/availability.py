from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.models.user import User
from app.models.availability import Weekday
from app.schemas.availability import (
    HostAvailabilityCreate,
    HostAvailabilityUpdate,
    HostAvailabilityResponse,
    AvailabilityExceptionCreate,
    AvailabilityExceptionResponse,
    HostSlotCheckResponse
)
from app.services.availability_service import AvailabilityService
from app.constants.permissions import Permissions
from app.utils.logger import get_logger


logger = get_logger("availability_route")

router = APIRouter(prefix="/availability", tags=["Host Availability Management"])


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_CREATE))]
)
def create_availability_schedule(
    request_data: HostAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new working availability schedule for a Host user.
    """
    logger.info(f"User '{current_user.email}' creating availability schedule for Host ID {request_data.user_id}")
    data = AvailabilityService.create_availability(
        db=db,
        current_user=current_user,
        data=request_data
    )
    return {
        "success": True,
        "message": "Host availability schedule created successfully",
        "data": data.model_dump(),
        "errors": None
    }


@router.get(
    "",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_READ))]
)
def list_availability_schedules(
    tenant_id: Optional[int] = Query(None, description="Filter by Tenant ID"),
    user_id: Optional[int] = Query(None, description="Filter by Host User ID"),
    weekday: Optional[Weekday] = Query(None, description="Filter by Weekday"),
    is_available: Optional[bool] = Query(None, description="Filter by availability status"),
    target_date: Optional[date] = Query(None, description="Filter schedules effective on date"),
    search: Optional[str] = Query(None, description="Search term in host name or notes"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List host availability schedules with pagination and filters.
    """
    items, total_count = AvailabilityService.list_availabilities(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        user_id=user_id,
        weekday=weekday,
        is_available=is_available,
        target_date=target_date,
        search=search,
        page=page,
        page_size=page_size
    )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "success": True,
        "message": "Host availability schedules retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "pagination": {
                "total_records": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        },
        "errors": None
    }


@router.get(
    "/slots",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_READ))]
)
def get_host_available_slots(
    host_id: int = Query(..., description="Target Host User ID"),
    date: date = Query(..., description="Target booking date (YYYY-MM-DD)"),
    slot_duration_minutes: int = Query(30, ge=15, le=120, description="Slot duration in minutes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate available booking time slots for a host on a specific date.
    """
    data = AvailabilityService.check_host_availability_slots(
        db=db,
        current_user=current_user,
        host_id=host_id,
        target_date=date,
        slot_duration_minutes=slot_duration_minutes
    )

    return {
        "success": True,
        "message": "Host available slots calculated successfully",
        "data": data.model_dump(),
        "errors": None
    }


@router.get(
    "/exceptions",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_READ))]
)
def list_availability_exceptions(
    tenant_id: Optional[int] = Query(None, description="Tenant ID"),
    user_id: Optional[int] = Query(None, description="Host User ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List holiday, leave, and maintenance exceptions.
    """
    items = AvailabilityService.list_exceptions(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "success": True,
        "message": "Availability exceptions retrieved successfully",
        "data": [item.model_dump() for item in items],
        "errors": None
    }


@router.post(
    "/exceptions",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_CREATE))]
)
def create_availability_exception(
    request_data: AvailabilityExceptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new holiday, leave, or maintenance exception.
    """
    data = AvailabilityService.create_exception(
        db=db,
        current_user=current_user,
        data=request_data
    )

    return {
        "success": True,
        "message": "Availability exception created successfully",
        "data": data.model_dump(),
        "errors": None
    }


@router.delete(
    "/exceptions/{id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_DELETE))]
)
def delete_availability_exception(
    id: int = Path(..., description="Exception ID to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Soft delete an availability exception.
    """
    AvailabilityService.delete_exception(
        db=db,
        current_user=current_user,
        exception_id=id
    )

    return {
        "success": True,
        "message": f"Availability exception ID {id} deleted successfully",
        "data": None,
        "errors": None
    }


@router.get(
    "/{id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_READ))]
)
def get_availability_schedule(
    id: int = Path(..., description="Availability Schedule ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a single host availability schedule by ID.
    """
    data = AvailabilityService.get_availability(
        db=db,
        current_user=current_user,
        availability_id=id
    )

    return {
        "success": True,
        "message": "Availability schedule retrieved successfully",
        "data": data.model_dump(),
        "errors": None
    }


@router.put(
    "/{id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_UPDATE))]
)
def update_availability_schedule(
    id: int = Path(..., description="Availability Schedule ID"),
    request_data: HostAvailabilityUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing host availability schedule.
    """
    data = AvailabilityService.update_availability(
        db=db,
        current_user=current_user,
        availability_id=id,
        data=request_data
    )

    return {
        "success": True,
        "message": "Availability schedule updated successfully",
        "data": data.model_dump(),
        "errors": None
    }


@router.delete(
    "/{id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(has_permission(Permissions.AVAILABILITY_DELETE))]
)
def delete_availability_schedule(
    id: int = Path(..., description="Availability Schedule ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Soft delete an availability schedule.
    """
    AvailabilityService.delete_availability(
        db=db,
        current_user=current_user,
        availability_id=id
    )

    return {
        "success": True,
        "message": f"Availability schedule ID {id} deleted successfully",
        "data": None,
        "errors": None
    }

