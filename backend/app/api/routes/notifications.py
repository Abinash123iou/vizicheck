from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.permissions import has_permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.models.notification import NotificationStatus, NotificationChannel, NotificationType
from app.schemas.auth import ResponseEnvelope
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.notification import (
    SendNotificationRequest,
    NotificationResponse,
    NotificationPaginationRequest,
    CreateTemplateRequest,
    NotificationTemplateResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    NotificationStatisticsResponse
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notification Management Module"])


@router.post("/send", response_model=ResponseEnvelope[NotificationResponse], status_code=status.HTTP_201_CREATED)
def send_notification(
    request_data: SendNotificationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.NOTIFICATION_SEND))
):
    """
    Dispatch a single system notification across target channel (Email, SMS, In-App).
    Applies recipient validation, preference opt-out checks, template variable interpolation, and audit logging.
    """
    client_ip = request.client.host if request.client else None
    dto = NotificationService.send_notification(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Notification dispatched successfully",
        data=dto
    )


@router.get("", response_model=ResponseEnvelope[EnhancedPaginationResponse[NotificationResponse]])
def list_notifications(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search term across title, message, recipient"),
    status_filter: Optional[NotificationStatus] = Query(default=None, alias="status", description="Filter by delivery status"),
    channel: Optional[NotificationChannel] = Query(default=None, description="Filter by delivery channel"),
    notification_type: Optional[NotificationType] = Query(default=None, description="Filter by event type"),
    recipient_user_id: Optional[int] = Query(default=None, description="Filter by recipient user ID"),
    tenant_id: Optional[int] = Query(default=None, description="Filter by tenant ID (Super Admin only)"),
    is_deleted: bool = Query(default=False, description="Include soft deleted records"),
    sort_by: str = Query(default="created_at", description="Field to sort by"),
    order: str = Query(default="desc", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.NOTIFICATION_READ))
):
    """
    Retrieve paginated, searched, and filtered list of notifications history.
    """
    params = NotificationPaginationRequest(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        channel=channel,
        notification_type=notification_type,
        recipient_user_id=recipient_user_id,
        tenant_id=tenant_id,
        is_deleted=is_deleted,
        sort_by=sort_by,
        order=order
    )
    paginated_dto = NotificationService.list_notifications(db=db, current_user=current_user, params=params)
    return ResponseEnvelope(
        success=True,
        message="Notifications history retrieved successfully",
        data=paginated_dto
    )


@router.patch("/{id}/read", response_model=ResponseEnvelope[NotificationResponse])
def mark_notification_as_read(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark an in-app notification record as READ.
    """
    client_ip = request.client.host if request.client else None
    dto = NotificationService.mark_as_read(
        db=db,
        current_user=current_user,
        notification_id=id,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Notification marked as read",
        data=dto
    )


@router.get("/statistics", response_model=ResponseEnvelope[NotificationStatisticsResponse])
def get_notification_statistics(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID filter (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.NOTIFICATION_READ))
):
    """
    Retrieve notification delivery statistics and channel breakdown analytics.
    """
    stats = NotificationService.get_statistics(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Notification statistics retrieved successfully",
        data=stats
    )


@router.get("/preferences", response_model=ResponseEnvelope[NotificationPreferenceResponse])
def get_user_preferences(
    user_id: Optional[int] = Query(default=None, description="Target user ID (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve user channel delivery opt-in/opt-out preferences.
    """
    target_id = user_id or current_user.id
    dto = NotificationService.get_user_preference(db=db, current_user=current_user, user_id=target_id)
    return ResponseEnvelope(
        success=True,
        message="User notification preferences retrieved successfully",
        data=dto
    )


@router.put("/preferences", response_model=ResponseEnvelope[NotificationPreferenceResponse])
def update_user_preferences(
    request_data: NotificationPreferenceRequest,
    request: Request,
    user_id: Optional[int] = Query(default=None, description="Target user ID (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user channel delivery preferences (Email, SMS, In-App opt-in/opt-out).
    """
    client_ip = request.client.host if request.client else None
    target_id = user_id or current_user.id
    dto = NotificationService.update_user_preference(
        db=db,
        current_user=current_user,
        user_id=target_id,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Notification preferences updated successfully",
        data=dto
    )


@router.post("/templates", response_model=ResponseEnvelope[NotificationTemplateResponse], status_code=status.HTTP_201_CREATED)
def create_notification_template(
    request_data: CreateTemplateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.NOTIFICATION_MANAGE_TEMPLATES))
):
    """
    Create a reusable notification message template with placeholder variables.
    """
    client_ip = request.client.host if request.client else None
    dto = NotificationService.create_template(
        db=db,
        current_user=current_user,
        request=request_data,
        ip_address=client_ip
    )
    return ResponseEnvelope(
        success=True,
        message="Notification template created successfully",
        data=dto
    )


@router.get("/templates", response_model=ResponseEnvelope[List[NotificationTemplateResponse]])
def list_notification_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.NOTIFICATION_READ))
):
    """
    List active notification templates available to current tenant.
    """
    dtos = NotificationService.list_templates(db=db, current_user=current_user)
    return ResponseEnvelope(
        success=True,
        message="Notification templates retrieved successfully",
        data=dtos
    )
