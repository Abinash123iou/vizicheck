import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database.base import Base
from app.models.mixins import SoftDeleteMixin
from app.constants.notification_types import (
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)


class Notification(Base, SoftDeleteMixin):
    """
    Model representing system notifications across Email, SMS, and In-App channels.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(50), nullable=True)

    notification_type = Column(String(100), nullable=False, default=NotificationType.GENERAL_ANNOUNCEMENT)
    channel = Column(String(50), nullable=False, default=NotificationChannel.IN_APP)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    status = Column(String(50), nullable=False, default=NotificationStatus.PENDING, index=True)
    priority = Column(String(50), nullable=False, default=NotificationPriority.MEDIUM)

    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    reference_module = Column(String(100), nullable=True)
    reference_id = Column(Integer, nullable=True)

    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    retry_count = Column(Integer, default=0, nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    recipient = relationship("User", foreign_keys=[recipient_user_id])
    template = relationship("NotificationTemplate", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by])


class NotificationTemplate(Base, SoftDeleteMixin):
    """
    Model representing reusable notification message templates.
    """
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)  # Null for global defaults

    template_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)

    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # Allowed template variables

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])


class NotificationPreference(Base):
    """
    Model representing per-user channel delivery preferences.
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=True, nullable=False)
    inapp_enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    user = relationship("User", foreign_keys=[user_id])
