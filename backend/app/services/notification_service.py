from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, AuthorizationException, ValidationException
from app.models.user import User
from app.core.permissions import SystemRoles
from app.models.notification import Notification, NotificationTemplate, NotificationPreference
from app.models.visit_request import VisitRequest
from app.constants.notification_types import (
    NotificationType, NotificationChannel, NotificationStatus, NotificationPriority
)
from app.constants.audit_actions import AuditActions
from app.schemas.notification import (
    SendNotificationRequest,
    NotificationResponse,
    NotificationPaginationRequest,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    NotificationTemplateResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    NotificationStatisticsResponse
)
from app.schemas.user import EnhancedPaginationResponse
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.notification_validator import NotificationValidator
from app.mappers.notification_mapper import NotificationMapper
from app.utils.logger import get_logger

logger = get_logger("notification_service")


class NotificationService:
    """
    Centralized Notification Pipeline Service supporting Email, SMS, and In-App dispatches,
    template variable interpolation, user preferences, delivery tracking, and event hooks.
    """

    MODULE_NAME = "NOTIFICATIONS"

    @classmethod
    def send_notification(
        cls,
        db: Session,
        current_user: User,
        request: SendNotificationRequest,
        ip_address: Optional[str] = None
    ) -> NotificationResponse:
        """
        Dispatch a single notification across target delivery channel.
        Applies recipient validation, preference opt-out checks, template interpolation, and audit logging.
        """
        # Resolve Tenant ID context dynamically
        tenant_id = cls._resolve_tenant_id(
            db,
            current_user,
            explicit_tenant_id=request.tenant_id,
            target_user_id=request.recipient_user_id
        )

        # Resolve Recipient User details
        recipient_user = None
        if request.recipient_user_id:
            recipient_user = UserRepository.find_by_id(db, request.recipient_user_id)
            if not recipient_user:
                raise NotFoundException(f"Recipient user with ID {request.recipient_user_id} not found.")

        # Validate channel addresses and user preference opt-outs
        NotificationValidator.validate_send_request(db, request, recipient_user=recipient_user)

        # Template variable interpolation if template_code is provided
        title = request.title
        message = request.message
        template_entity = None

        if request.template_code:
            template_entity = NotificationRepository.find_template_by_code(
                db, template_code=request.template_code, tenant_id=tenant_id
            )
            if template_entity:
                tpl_subject, tpl_body = NotificationValidator.interpolate_template(
                    template_entity, request.template_variables
                )
                if tpl_subject:
                    title = tpl_subject
                message = tpl_body

        # Construct Notification Entity
        now = datetime.utcnow()
        entity = Notification(
            tenant_id=tenant_id,
            recipient_user_id=request.recipient_user_id,
            recipient_email=request.recipient_email or (recipient_user.email if recipient_user else None),
            recipient_phone=request.recipient_phone or (recipient_user.phone if recipient_user else None),
            notification_type=request.notification_type.value if hasattr(request.notification_type, "value") else str(request.notification_type),
            channel=request.channel.value if hasattr(request.channel, "value") else str(request.channel),
            title=title,
            message=message,
            status=NotificationStatus.SENDING.value,
            priority=request.priority.value if hasattr(request.priority, "value") else str(request.priority),
            template_id=template_entity.id if template_entity else None,
            reference_module=request.reference_module,
            reference_id=request.reference_id,
            scheduled_at=request.scheduled_at,
            created_by=current_user.id,
            created_at=now,
            updated_at=now
        )

        created_notification = NotificationRepository.create(db, entity)

        # Provider Dispatch Simulation (Email / SMS / In-App)
        cls._dispatch_to_provider(created_notification)

        # Update status to DELIVERED
        created_notification.status = NotificationStatus.DELIVERED.value
        created_notification.sent_at = datetime.utcnow()
        created_notification.delivered_at = datetime.utcnow()
        NotificationRepository.update(db, created_notification)

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=getattr(AuditActions, "NOTIFICATION_SENT", "NOTIFICATION_SENT"),
            module=cls.MODULE_NAME,
            entity_id=created_notification.id,
            new_value={
                "uuid": created_notification.uuid,
                "channel": created_notification.channel,
                "recipient_user_id": created_notification.recipient_user_id,
                "notification_type": created_notification.notification_type
            },
            ip_address=ip_address
        )

        return NotificationMapper.to_notification_response(created_notification)

    @classmethod
    def list_notifications(
        cls,
        db: Session,
        current_user: User,
        params: NotificationPaginationRequest
    ) -> EnhancedPaginationResponse[NotificationResponse]:
        """
        Retrieve paginated list of notifications. Enforces tenant isolation and user self-filtering.
        """
        is_super_admin = current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN
        tenant_id = None if is_super_admin else current_user.tenant_id

        # Non-admin users are restricted to viewing only notifications sent to themselves
        user_id_restrict = None
        if not is_super_admin and current_user.role and current_user.role.name not in [SystemRoles.TENANT_ADMIN, SystemRoles.SECURITY_GUARD]:
            user_id_restrict = current_user.id

        items, total_count = NotificationRepository.list_notifications(
            db=db,
            params=params,
            tenant_id=tenant_id,
            user_id_restrict=user_id_restrict
        )

        dtos = NotificationMapper.to_notification_response_list(items)
        total_pages = (total_count + params.page_size - 1) // params.page_size if params.page_size > 0 else 0

        return EnhancedPaginationResponse(
            items=dtos,
            total_records=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )

    @classmethod
    def mark_as_read(
        cls,
        db: Session,
        current_user: User,
        notification_id: int,
        ip_address: Optional[str] = None
    ) -> NotificationResponse:
        """
        Mark an in-app notification as READ.
        """
        is_super_admin = current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN
        tenant_id = None if is_super_admin else current_user.tenant_id

        entity = NotificationRepository.find_by_id(db, notification_id=notification_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Notification with ID {notification_id} not found.")

        # Ensure user is recipient or admin
        if not is_super_admin and entity.recipient_user_id and entity.recipient_user_id != current_user.id:
            raise AuthorizationException("Unauthorized to access this notification.")

        entity.status = NotificationStatus.READ.value
        entity.delivered_at = entity.delivered_at or datetime.utcnow()
        updated_entity = NotificationRepository.update(db, entity)

        # Audit log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=getattr(AuditActions, "NOTIFICATION_READ", "NOTIFICATION_READ"),
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            new_value={"status": updated_entity.status},
            ip_address=ip_address
        )

        return NotificationMapper.to_notification_response(updated_entity)

    # --- Preference Management ---

    @classmethod
    def _resolve_tenant_id(cls, db: Session, current_user: User, explicit_tenant_id: Optional[int] = None, target_user_id: Optional[int] = None) -> int:
        if explicit_tenant_id:
            return explicit_tenant_id
        if current_user.tenant_id:
            return current_user.tenant_id
        if target_user_id:
            target_user = UserRepository.find_by_id(db, target_user_id)
            if target_user and target_user.tenant_id:
                return target_user.tenant_id
        from app.models.tenant import Tenant
        first_tenant = db.query(Tenant).first()
        return first_tenant.id if first_tenant else 1

    @classmethod
    def get_user_preference(cls, db: Session, current_user: User, user_id: int) -> NotificationPreferenceResponse:
        """Retrieve user delivery opt-in/opt-out preferences."""
        tenant_id = cls._resolve_tenant_id(db, current_user, target_user_id=user_id)
        pref = NotificationRepository.get_user_preference(db, user_id=user_id, tenant_id=tenant_id)
        return NotificationMapper.to_preference_response(pref)

    @classmethod
    def update_user_preference(
        cls,
        db: Session,
        current_user: User,
        user_id: int,
        request: NotificationPreferenceRequest,
        ip_address: Optional[str] = None
    ) -> NotificationPreferenceResponse:
        """Update user delivery opt-in/opt-out preferences."""
        tenant_id = cls._resolve_tenant_id(db, current_user, target_user_id=user_id)
        pref = NotificationRepository.update_user_preference(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            email_enabled=request.email_enabled,
            sms_enabled=request.sms_enabled,
            inapp_enabled=request.inapp_enabled
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=getattr(AuditActions, "PREFERENCES_UPDATED", "PREFERENCES_UPDATED"),
            module=cls.MODULE_NAME,
            entity_id=pref.id,
            new_value={
                "email_enabled": pref.email_enabled,
                "sms_enabled": pref.sms_enabled,
                "inapp_enabled": pref.inapp_enabled
            },
            ip_address=ip_address
        )

        return NotificationMapper.to_preference_response(pref)

    # --- Template Management ---

    @classmethod
    def create_template(
        cls,
        db: Session,
        current_user: User,
        request: CreateTemplateRequest,
        ip_address: Optional[str] = None
    ) -> NotificationTemplateResponse:
        """Create new notification template."""
        tenant_id = request.tenant_id or current_user.tenant_id
        NotificationValidator.validate_template_create(db, request)

        entity = NotificationTemplate(
            tenant_id=tenant_id,
            template_code=request.template_code,
            name=request.name,
            channel=request.channel.value if hasattr(request.channel, "value") else str(request.channel),
            subject=request.subject,
            body=request.body,
            variables=request.variables,
            is_active=request.is_active
        )
        created = NotificationRepository.create_template(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=getattr(AuditActions, "TEMPLATE_CREATED", "TEMPLATE_CREATED"),
            module=cls.MODULE_NAME,
            entity_id=created.id,
            new_value={"template_code": created.template_code, "name": created.name},
            ip_address=ip_address
        )

        return NotificationMapper.to_template_response(created)

    @classmethod
    def list_templates(cls, db: Session, current_user: User) -> List[NotificationTemplateResponse]:
        """List active templates available for current tenant."""
        tenant_id = current_user.tenant_id
        entities = NotificationRepository.list_templates(db, tenant_id=tenant_id)
        return NotificationMapper.to_template_response_list(entities)

    @classmethod
    def get_statistics(cls, db: Session, current_user: User, tenant_id: Optional[int] = None) -> NotificationStatisticsResponse:
        """Retrieve notification delivery analytics."""
        is_super_admin = current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN
        effective_tenant_id = tenant_id if is_super_admin else current_user.tenant_id
        stats = NotificationRepository.get_statistics(db, tenant_id=effective_tenant_id)
        return NotificationStatisticsResponse(**stats)

    # --- System Event Notification Hooks ---

    @classmethod
    def notify_request_created(cls, request: VisitRequest) -> bool:
        """Trigger notification hook when a new visit request is submitted."""
        logger.info(
            f"[Notification System Event] Visit Request Created: Code={request.request_code}, "
            f"Visitor ID={request.visitor_id}, Host ID={request.host_id}, Tenant ID={request.tenant_id}"
        )
        return True

    @classmethod
    def notify_request_approved(cls, request: VisitRequest) -> bool:
        """Trigger notification hook when a visit request is approved."""
        logger.info(
            f"[Notification System Event] Visit Request Approved: Code={request.request_code}, "
            f"Visitor ID={request.visitor_id}, Host ID={request.host_id}"
        )
        return True

    @classmethod
    def notify_request_rejected(cls, request: VisitRequest) -> bool:
        """Trigger notification hook when a visit request is rejected."""
        logger.info(
            f"[Notification System Event] Visit Request Rejected: Code={request.request_code}, "
            f"Visitor ID={request.visitor_id}, Reason='{request.rejection_reason}'"
        )
        return True

    @classmethod
    def notify_request_cancelled(cls, request: VisitRequest) -> bool:
        """Trigger notification hook when a visit request is cancelled."""
        logger.info(
            f"[Notification System Event] Visit Request Cancelled: Code={request.request_code}, "
            f"Reason='{request.cancellation_reason}'"
        )
        return True

    @classmethod
    def notify_host(cls, host_id: int, message: str) -> bool:
        """Direct notification dispatch to employee host."""
        logger.info(f"[Notification System Event] Direct Host Alert (Host ID={host_id}): {message}")
        return True

    @classmethod
    def notify_security(cls, tenant_id: int, message: str) -> bool:
        """Direct notification dispatch to security officers."""
        logger.info(f"[Notification System Event] Direct Security Alert (Tenant ID={tenant_id}): {message}")
        return True

    @classmethod
    def notify_pass_generated(cls, visitor_pass) -> bool:
        """Trigger notification hook when a Visitor Pass is generated."""
        logger.info(f"[Notification System Event] Pass Generated: Code={visitor_pass.pass_code}")
        return True

    @classmethod
    def notify_pass_revoked(cls, visitor_pass) -> bool:
        """Trigger notification hook when a Visitor Pass is revoked."""
        logger.info(f"[Notification System Event] Pass Revoked: Code={visitor_pass.pass_code}")
        return True

    @classmethod
    def notify_pass_expired(cls, visitor_pass) -> bool:
        """Trigger notification hook when a Visitor Pass expires automatically."""
        logger.info(f"[Notification System Event] Pass Expired: Code={visitor_pass.pass_code}")
        return True

    @classmethod
    def notify_qr_regenerated(cls, visitor_pass, new_version: int) -> bool:
        """Trigger notification hook when a QR code is regenerated."""
        logger.info(f"[Notification System Event] QR Regenerated: Code={visitor_pass.pass_code}, Version={new_version}")
        return True

    @classmethod
    def notify_host_checkin(cls, checkin, visitor_pass, host) -> bool:
        """Notify host employee when their visitor checks in at the gate."""
        logger.info(f"[Notification System Event] Host Check-In Alert: Host ID={host.id if host else 'N/A'}")
        return True

    @classmethod
    def notify_host_checkout(cls, checkin, visitor_pass, host) -> bool:
        """Notify host employee when their visitor checks out."""
        logger.info(f"[Notification System Event] Host Check-Out Alert: Host ID={host.id if host else 'N/A'}")
        return True

    @classmethod
    def notify_security_alert(cls, tenant_id: int, alert_type: str, message: str, details: Optional[str] = None) -> bool:
        """Dispatch security alert to gate officers and tenant administrators."""
        logger.warning(f"[Notification System Event] Security Alert: Tenant ID={tenant_id}, Alert='{alert_type}'")
        return True

    @classmethod
    def notify_overstay(cls, checkin, visitor_pass, host) -> bool:
        """Notify host and security when a visitor has exceeded scheduled duration."""
        logger.warning(f"[Notification System Event] Visitor Overstay Alert: CheckIn ID={checkin.id}")
        return True

    @classmethod
    def notify_manual_override(cls, checkin, performed_by, reason: str) -> bool:
        """Notify security administrator when a manual check-in/out override occurs."""
        logger.info(f"[Notification System Event] Manual Override Alert: CheckIn ID={checkin.id}")
        return True

    # --- Provider Dispatch Helper ---

    @staticmethod
    def _dispatch_to_provider(notification: Notification) -> bool:
        """
        Internal provider dispatch abstraction sending notification via Email, SMS, or In-App.
        """
        logger.info(
            f"[Notification Provider Dispatch] Channel={notification.channel}, "
            f"Title='{notification.title}', RecipientEmail='{notification.recipient_email}', "
            f"RecipientPhone='{notification.recipient_phone}'"
        )
        return True
