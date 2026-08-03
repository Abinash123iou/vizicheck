from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.notification import Notification, NotificationTemplate, NotificationPreference
from app.schemas.notification import NotificationPaginationRequest, CreateTemplateRequest
from app.constants.notification_types import NotificationStatus, NotificationChannel


class NotificationRepository:
    """
    Repository pattern layer managing database access for notifications, templates, and user preferences.
    """

    @classmethod
    def create(cls, db: Session, entity: Notification) -> Notification:
        """Persist a new notification entity."""
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @classmethod
    def find_by_id(
        cls,
        db: Session,
        notification_id: int,
        tenant_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Optional[Notification]:
        """Retrieve a notification by primary key ID with optional tenant isolation."""
        query = db.query(Notification).filter(Notification.id == notification_id)
        if tenant_id is not None:
            query = query.filter(Notification.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(Notification.is_deleted == False)
        return query.first()

    @classmethod
    def find_by_uuid(
        cls,
        db: Session,
        uuid_str: str,
        tenant_id: Optional[int] = None
    ) -> Optional[Notification]:
        """Retrieve notification by UUID string."""
        query = db.query(Notification).filter(Notification.uuid == uuid_str, Notification.is_deleted == False)
        if tenant_id is not None:
            query = query.filter(Notification.tenant_id == tenant_id)
        return query.first()

    @classmethod
    def list_notifications(
        cls,
        db: Session,
        params: NotificationPaginationRequest,
        tenant_id: Optional[int] = None,
        user_id_restrict: Optional[int] = None
    ) -> Tuple[List[Notification], int]:
        """
        List notifications with pagination, filtering, search, and tenant isolation.
        """
        query = db.query(Notification)

        # Soft delete filter
        if not params.is_deleted:
            query = query.filter(Notification.is_deleted == False)
        else:
            query = query.filter(Notification.is_deleted == True)

        # Tenant isolation
        effective_tenant_id = params.tenant_id if params.tenant_id is not None else tenant_id
        if effective_tenant_id is not None:
            query = query.filter(Notification.tenant_id == effective_tenant_id)

        # User restriction for regular employees / visitors viewing their own notifications
        if user_id_restrict is not None:
            query = query.filter(Notification.recipient_user_id == user_id_restrict)

        # Category / Status / Channel filters
        if params.status:
            query = query.filter(Notification.status == params.status.value)
        if params.channel:
            query = query.filter(Notification.channel == params.channel.value)
        if params.notification_type:
            query = query.filter(Notification.notification_type == params.notification_type.value)
        if params.recipient_user_id and user_id_restrict is None:
            query = query.filter(Notification.recipient_user_id == params.recipient_user_id)

        # Search term filter
        if params.search:
            pattern = f"%{params.search}%"
            query = query.filter(
                or_(
                    Notification.title.ilike(pattern),
                    Notification.message.ilike(pattern),
                    Notification.recipient_email.ilike(pattern),
                    Notification.recipient_phone.ilike(pattern)
                )
            )

        total_count = query.count()

        # Sorting
        sort_column = getattr(Notification, params.sort_by, Notification.created_at)
        if params.order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Pagination
        offset = (params.page - 1) * params.page_size
        items = query.offset(offset).limit(params.page_size).all()

        return items, total_count

    @classmethod
    def update(cls, db: Session, entity: Notification) -> Notification:
        """Update existing notification entity."""
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @classmethod
    def mark_as_read(cls, db: Session, notification_id: int, tenant_id: Optional[int] = None) -> Optional[Notification]:
        """Mark an in-app notification as READ."""
        entity = cls.find_by_id(db, notification_id, tenant_id=tenant_id)
        if entity:
            entity.status = NotificationStatus.READ.value
            entity.delivered_at = entity.delivered_at or datetime.utcnow()
            db.add(entity)
            db.commit()
            db.refresh(entity)
        return entity

    # --- Template Repository Operations ---

    @classmethod
    def find_template_by_code(
        cls,
        db: Session,
        template_code: str,
        tenant_id: Optional[int] = None
    ) -> Optional[NotificationTemplate]:
        """
        Find template by template_code. Searches tenant-specific template first,
        falling back to global template (tenant_id IS NULL).
        """
        if tenant_id is not None:
            tenant_template = db.query(NotificationTemplate).filter(
                NotificationTemplate.template_code == template_code,
                NotificationTemplate.tenant_id == tenant_id,
                NotificationTemplate.is_active == True,
                NotificationTemplate.is_deleted == False
            ).first()
            if tenant_template:
                return tenant_template

        # Global fallback
        return db.query(NotificationTemplate).filter(
            NotificationTemplate.template_code == template_code,
            NotificationTemplate.tenant_id == None,
            NotificationTemplate.is_active == True,
            NotificationTemplate.is_deleted == False
        ).first()

    @classmethod
    def create_template(cls, db: Session, entity: NotificationTemplate) -> NotificationTemplate:
        """Create new notification template."""
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @classmethod
    def list_templates(cls, db: Session, tenant_id: Optional[int] = None) -> List[NotificationTemplate]:
        """List active templates available to tenant."""
        query = db.query(NotificationTemplate).filter(NotificationTemplate.is_deleted == False)
        if tenant_id is not None:
            query = query.filter(or_(NotificationTemplate.tenant_id == tenant_id, NotificationTemplate.tenant_id == None))
        return query.order_by(NotificationTemplate.name.asc()).all()

    # --- Preferences Repository Operations ---

    @classmethod
    def get_user_preference(cls, db: Session, user_id: int, tenant_id: int) -> NotificationPreference:
        """Retrieve or initialize user delivery preferences."""
        pref = db.query(NotificationPreference).filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).first()
        if not pref:
            pref = NotificationPreference(
                tenant_id=tenant_id,
                user_id=user_id,
                email_enabled=True,
                sms_enabled=True,
                inapp_enabled=True
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @classmethod
    def update_user_preference(
        cls,
        db: Session,
        user_id: int,
        tenant_id: int,
        email_enabled: Optional[bool] = None,
        sms_enabled: Optional[bool] = None,
        inapp_enabled: Optional[bool] = None
    ) -> NotificationPreference:
        """Update user delivery opt-in/opt-out preferences."""
        pref = cls.get_user_preference(db, user_id=user_id, tenant_id=tenant_id)
        if email_enabled is not None:
            pref.email_enabled = email_enabled
        if sms_enabled is not None:
            pref.sms_enabled = sms_enabled
        if inapp_enabled is not None:
            pref.inapp_enabled = inapp_enabled
        db.add(pref)
        db.commit()
        db.refresh(pref)
        return pref

    # --- Analytics & Statistics ---

    @classmethod
    def get_statistics(cls, db: Session, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculate delivery stats for dashboard analytics."""
        query = db.query(Notification).filter(Notification.is_deleted == False)
        if tenant_id is not None:
            query = query.filter(Notification.tenant_id == tenant_id)

        total = query.count()
        delivered = query.filter(or_(Notification.status == NotificationStatus.DELIVERED.value, Notification.status == NotificationStatus.READ.value)).count()
        failed = query.filter(Notification.status == NotificationStatus.FAILED.value).count()
        pending = query.filter(Notification.status == NotificationStatus.PENDING.value).count()
        queued = query.filter(Notification.status == NotificationStatus.QUEUED.value).count()

        email_count = query.filter(Notification.channel == NotificationChannel.EMAIL.value).count()
        sms_count = query.filter(Notification.channel == NotificationChannel.SMS.value).count()
        inapp_count = query.filter(Notification.channel == NotificationChannel.IN_APP.value).count()

        success_rate = round((delivered / total * 100), 2) if total > 0 else 100.0

        return {
            "total_notifications": total,
            "delivered_count": delivered,
            "failed_count": failed,
            "pending_count": pending,
            "queued_count": queued,
            "email_channel_count": email_count,
            "sms_channel_count": sms_count,
            "inapp_channel_count": inapp_count,
            "success_rate_percentage": success_rate
        }
