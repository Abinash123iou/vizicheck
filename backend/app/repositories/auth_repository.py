from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

class AuthRepository:
    """
    Database repository for authentication-related records such as audit logs.
    """

    @staticmethod
    def create_audit_log(
        db: Session,
        user_id: Optional[int],
        action: str,
        module: str = "AUTH",
        ip_address: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None
    ) -> AuditLog:
        """
        Persist an audit log entry for authentication events.
        """
        audit_log = AuditLog(
            user_id=user_id,
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
