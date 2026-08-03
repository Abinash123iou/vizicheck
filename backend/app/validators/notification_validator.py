import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import ValidationException, NotFoundException
from app.models.notification import Notification, NotificationPreference, NotificationTemplate
from app.models.user import User
from app.constants.notification_types import NotificationChannel, NotificationStatus, NotificationType
from app.schemas.notification import SendNotificationRequest, CreateTemplateRequest


class NotificationValidator:
    """
    Validator layer for Notification Management Module enforcing schema integrity,
    channel address validation, delivery preference compliance, and template interpolation.
    """

    @classmethod
    def validate_send_request(
        cls,
        db: Session,
        request: SendNotificationRequest,
        recipient_user: Optional[User] = None
    ) -> None:
        """
        Validate destination contact information and delivery preferences for notification requests.
        """
        # 1. Ensure recipient destination address exists for target channel
        email = request.recipient_email or (recipient_user.email if recipient_user else None)
        phone = request.recipient_phone or (recipient_user.phone if recipient_user else None)

        if request.channel == NotificationChannel.EMAIL:
            if not email:
                raise ValidationException("Email recipient address is required for EMAIL channel dispatches.")
            if not cls._is_valid_email(email):
                raise ValidationException(f"Invalid email address format: '{email}'")

        elif request.channel == NotificationChannel.SMS:
            if not phone:
                raise ValidationException("Recipient phone number is required for SMS channel dispatches.")

        elif request.channel == NotificationChannel.IN_APP:
            if not request.recipient_user_id:
                raise ValidationException("Recipient user ID is required for IN_APP notifications.")

        # 2. Check user preference opt-outs if recipient_user_id is present
        if request.recipient_user_id:
            pref = db.query(NotificationPreference).filter_by(
                user_id=request.recipient_user_id
            ).first()
            if pref:
                if request.channel == NotificationChannel.EMAIL and not pref.email_enabled:
                    raise ValidationException("Recipient has opted out of Email notifications.")
                elif request.channel == NotificationChannel.SMS and not pref.sms_enabled:
                    raise ValidationException("Recipient has opted out of SMS notifications.")
                elif request.channel == NotificationChannel.IN_APP and not pref.inapp_enabled:
                    raise ValidationException("Recipient has opted out of In-App notifications.")

    @classmethod
    def validate_template_create(cls, db: Session, request: CreateTemplateRequest) -> None:
        """
        Validate uniqueness of template code per tenant scope.
        """
        existing = db.query(NotificationTemplate).filter_by(
            template_code=request.template_code,
            tenant_id=request.tenant_id,
            is_deleted=False
        ).first()
        if existing:
            raise ValidationException(
                f"Notification template with code '{request.template_code}' already exists for this tenant."
            )

    @classmethod
    def interpolate_template(
        cls,
        template: NotificationTemplate,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Render template subject and body by replacing placeholders formatted as {variable_name}.
        """
        variables = variables or {}
        subject = template.subject or ""
        body = template.body

        for key, val in variables.items():
            placeholder = f"{{{key}}}"
            str_val = str(val)
            subject = subject.replace(placeholder, str_val)
            body = body.replace(placeholder, str_val)

        return subject, body

    @classmethod
    def validate_state_transition(
        cls,
        notification: Notification,
        target_status: NotificationStatus
    ) -> None:
        """
        Validate legal lifecycle status transitions.
        """
        valid_transitions = {
            NotificationStatus.PENDING: [NotificationStatus.QUEUED, NotificationStatus.SENDING, NotificationStatus.CANCELLED],
            NotificationStatus.QUEUED: [NotificationStatus.SENDING, NotificationStatus.FAILED, NotificationStatus.CANCELLED],
            NotificationStatus.SENDING: [NotificationStatus.DELIVERED, NotificationStatus.FAILED, NotificationStatus.RETRYING],
            NotificationStatus.RETRYING: [NotificationStatus.SENDING, NotificationStatus.FAILED, NotificationStatus.CANCELLED],
            NotificationStatus.DELIVERED: [NotificationStatus.READ],
            NotificationStatus.FAILED: [NotificationStatus.RETRYING, NotificationStatus.CANCELLED],
            NotificationStatus.READ: [],
            NotificationStatus.CANCELLED: []
        }

        current = NotificationStatus(notification.status)
        allowed = valid_transitions.get(current, [])
        if target_status not in allowed:
            raise ValidationException(
                f"Illegal notification status transition from '{current.value}' to '{target_status.value}'."
            )

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Simple regex validation for email addresses."""
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        return bool(re.match(pattern, email))
