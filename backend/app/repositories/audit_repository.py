from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models.audit_log import AuditLog
from app.models.user import User

class AuditRepository:
    """
    Repository layer for creating, querying, and exporting audit log records with multi-tenant isolation.
    """

    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: Optional[int],
        action: str,
        module: str = "USER_MANAGEMENT",
        ip_address: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        tenant_id: Optional[int] = None
    ) -> AuditLog:
        """
        Persist audit log entry to database. Automatically populates tenant_id from User if user_id is given and tenant_id is missing.
        """
        if not tenant_id and user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                tenant_id = user.tenant_id

        audit_log = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            module=module,
            entity_id=entity_id or user_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def get_audit_logs(
        db: Session,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Query audit logs with multi-tenant filtering, search, and pagination.
        """
        query = db.query(AuditLog)

        if tenant_id is not None:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if module:
            query = query.filter(AuditLog.module == module)
        if action:
            query = query.filter(AuditLog.action == action)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    AuditLog.action.ilike(search_pattern),
                    AuditLog.module.ilike(search_pattern),
                    AuditLog.ip_address.ilike(search_pattern)
                )
            )

        total = query.count()
        offset = (page - 1) * limit
        items = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get_all_audit_logs_for_export(
        db: Session,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """
        Retrieve unpaginated audit logs matching criteria for file exports.
        """
        query = db.query(AuditLog)

        if tenant_id is not None:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if module:
            query = query.filter(AuditLog.module == module)
        if action:
            query = query.filter(AuditLog.action == action)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(desc(AuditLog.created_at)).all()

    @staticmethod
    def get_entity_activity_timeline(
        db: Session,
        module: str,
        entity_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Retrieve audit log history for a specific module entity (e.g. tenant activity timeline).
        """
        return db.query(AuditLog).filter(
            AuditLog.module == module,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
