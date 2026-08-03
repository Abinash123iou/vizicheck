from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.constants.notification_types import (
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)


class SendNotificationRequest(BaseModel):
    """
    Request schema for sending a notification across Email, SMS, or In-App channels.
    """
    tenant_id: Optional[int] = Field(None, description="Tenant ID (defaults to current user tenant)")
    recipient_user_id: Optional[int] = Field(None, description="Recipient system user ID")
    recipient_email: Optional[EmailStr] = Field(None, description="Destination email address")
    recipient_phone: Optional[str] = Field(None, description="Destination phone number")

    notification_type: NotificationType = Field(
        default=NotificationType.GENERAL_ANNOUNCEMENT,
        description="Category of notification event"
    )
    channel: NotificationChannel = Field(
        default=NotificationChannel.IN_APP,
        description="Delivery channel (EMAIL, SMS, IN_APP)"
    )

    title: str = Field(..., min_length=1, max_length=255, description="Notification title or email subject")
    message: str = Field(..., min_length=1, description="Notification body content")

    priority: NotificationPriority = Field(
        default=NotificationPriority.MEDIUM,
        description="Priority level (LOW, MEDIUM, HIGH, URGENT)"
    )

    template_code: Optional[str] = Field(None, description="Optional notification template code to interpolate variables")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Key-value pairs for template variable interpolation")

    reference_module: Optional[str] = Field(None, description="Originating module name (e.g. VISIT_REQUEST)")
    reference_id: Optional[int] = Field(None, description="Originating entity ID")

    scheduled_at: Optional[datetime] = Field(None, description="Optional scheduled dispatch timestamp")


class NotificationResponse(BaseModel):
    """
    Response schema representing notification record.
    """
    id: int
    uuid: str
    tenant_id: int
    recipient_user_id: Optional[int] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None

    notification_type: str
    channel: str
    title: str
    message: str

    status: str
    priority: str

    template_id: Optional[int] = None
    reference_module: Optional[str] = None
    reference_id: Optional[int] = None

    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int

    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    class Config:
        from_attributes = True


class NotificationPaginationRequest(BaseModel):
    """
    Query parameters for filtering and paginating notifications history.
    """
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    search: Optional[str] = None
    status: Optional[NotificationStatus] = None
    channel: Optional[NotificationChannel] = None
    notification_type: Optional[NotificationType] = None
    recipient_user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    is_deleted: bool = False
    sort_by: str = "created_at"
    order: str = "desc"


class CreateTemplateRequest(BaseModel):
    """
    Schema for creating a notification template.
    """
    tenant_id: Optional[int] = None
    template_code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    channel: NotificationChannel
    subject: Optional[str] = Field(None, max_length=255)
    body: str = Field(..., min_length=1)
    variables: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True


class UpdateTemplateRequest(BaseModel):
    """
    Schema for updating a notification template.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(BaseModel):
    """
    Response schema for notification templates.
    """
    id: int
    tenant_id: Optional[int] = None
    template_code: str
    name: str
    channel: str
    subject: Optional[str] = None
    body: str
    variables: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceRequest(BaseModel):
    """
    Schema for updating user channel delivery preferences.
    """
    email_enabled: Optional[bool] = True
    sms_enabled: Optional[bool] = True
    inapp_enabled: Optional[bool] = True


class NotificationPreferenceResponse(BaseModel):
    """
    Response schema for user channel delivery preferences.
    """
    id: int
    tenant_id: int
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    inapp_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationStatisticsResponse(BaseModel):
    """
    Dashboard analytics metrics for notification delivery.
    """
    total_notifications: int
    delivered_count: int
    failed_count: int
    pending_count: int
    queued_count: int
    email_channel_count: int
    sms_channel_count: int
    inapp_channel_count: int
    success_rate_percentage: float
