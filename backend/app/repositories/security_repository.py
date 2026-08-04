from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_

from app.models.security import UserSession, SecurityLog
from app.models.user import User

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

class SecurityRepository:
    """
    Repository layer for session management, security logging, failed login tracking,
    account lockout, and security metrics aggregation.
    """

    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        token_jti: str,
        expires_at: datetime,
        tenant_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            tenant_id=tenant_id,
            token_jti=token_jti,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            is_active=True,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            last_activity_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> Optional[UserSession]:
        return db.query(UserSession).filter(UserSession.id == session_id).first()

    @staticmethod
    def get_session_by_token_jti(db: Session, token_jti: str) -> Optional[UserSession]:
        return db.query(UserSession).filter(
            UserSession.token_jti == token_jti
        ).first()

    @staticmethod
    def get_active_sessions(
        db: Session,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None
    ) -> List[UserSession]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at > now
        )
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        if tenant_id:
            query = query.filter(UserSession.tenant_id == tenant_id)
        return query.order_by(desc(UserSession.created_at)).all()

    @staticmethod
    def revoke_session(db: Session, session_id: int) -> Optional[UserSession]:
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if session and session.is_active:
            session.is_active = False
            session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            db.refresh(session)
        return session

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: int) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        count = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({
            UserSession.is_active: False,
            UserSession.revoked_at: now
        }, synchronize_session=False)
        db.commit()
        return count

    @staticmethod
    def create_security_log(
        db: Session,
        event_type: str,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        severity: str = "LOW",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        details: Optional[dict] = None
    ) -> SecurityLog:
        log = SecurityLog(
            user_id=user_id,
            tenant_id=tenant_id,
            event_type=event_type,
            severity=severity.upper(),
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            details=details,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_security_activities(
        db: Session,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[SecurityLog], int]:
        query = db.query(SecurityLog)
        if tenant_id:
            query = query.filter(SecurityLog.tenant_id == tenant_id)
        if user_id:
            query = query.filter(SecurityLog.user_id == user_id)
        if event_type:
            query = query.filter(SecurityLog.event_type == event_type)
        if severity:
            query = query.filter(SecurityLog.severity == severity.upper())
        if start_date:
            query = query.filter(SecurityLog.created_at >= start_date)
        if end_date:
            query = query.filter(SecurityLog.created_at <= end_date)

        total = query.count()
        offset = (page - 1) * limit
        items = query.order_by(desc(SecurityLog.created_at)).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def is_account_locked(db: Session, user: User) -> Tuple[bool, Optional[datetime]]:
        if not user.locked_until:
            return False, None
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if user.locked_until > now:
            return True, user.locked_until
        
        # Lock expired, auto reset
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        return False, None

    @staticmethod
    def increment_failed_logins(db: Session, user: User) -> bool:
        user.failed_login_attempts += 1
        is_locked = False
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            user.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            is_locked = True
        db.commit()
        return is_locked

    @staticmethod
    def reset_failed_logins(db: Session, user: User) -> None:
        if user.failed_login_attempts > 0 or user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

    @staticmethod
    def get_dashboard_metrics(
        db: Session,
        tenant_id: Optional[int] = None
    ) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        since_24h = now - timedelta(hours=24)

        # Active sessions
        session_query = db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at > now
        )
        if tenant_id:
            session_query = session_query.filter(UserSession.tenant_id == tenant_id)
        total_active_sessions = session_query.count()

        # Failed logins last 24h
        failed_query = db.query(SecurityLog).filter(
            SecurityLog.event_type == "LOGIN_FAILED",
            SecurityLog.created_at >= since_24h
        )
        if tenant_id:
            failed_query = failed_query.filter(SecurityLog.tenant_id == tenant_id)
        failed_logins_24h = failed_query.count()

        # Locked accounts
        user_query = db.query(User).filter(User.locked_until > now)
        if tenant_id:
            user_query = user_query.filter(User.tenant_id == tenant_id)
        locked_accounts_count = user_query.count()

        # Suspicious activities (severity HIGH/CRITICAL or SUSPICIOUS_ACTIVITY)
        suspicious_query = db.query(SecurityLog).filter(
            SecurityLog.created_at >= since_24h,
            or_(
                SecurityLog.severity.in_(["HIGH", "CRITICAL"]),
                SecurityLog.event_type == "SUSPICIOUS_ACTIVITY"
            )
        )
        if tenant_id:
            suspicious_query = suspicious_query.filter(SecurityLog.tenant_id == tenant_id)
        suspicious_activities_count = suspicious_query.count()

        return {
            "total_active_sessions": total_active_sessions,
            "failed_logins_24h": failed_logins_24h,
            "locked_accounts_count": locked_accounts_count,
            "suspicious_activities_count": suspicious_activities_count
        }
