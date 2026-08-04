from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.security import UserSession, SecurityLog
from app.repositories.security_repository import SecurityRepository
from app.schemas.security import (
    UserSessionResponse,
    SessionListResponse,
    SecurityActivityResponse,
    SecurityActivityListResponse,
    SecurityDashboardMetrics,
    SecurityDashboardResponse
)
from app.core.exceptions import (
    NotFoundException,
    AuthorizationException,
    AccountLockedException
)

class SecurityService:
    """
    Service layer providing business logic for active session management, token revocation,
    failed login tracking, account lockout, suspicious activity detection, and security dashboard reporting.
    """

    @classmethod
    def get_active_sessions(
        cls,
        db: Session,
        current_user: User,
        user_id: Optional[int] = None
    ) -> SessionListResponse:
        """
        List active user sessions based on caller role & privileges.
        """
        if current_user.is_super_admin:
            target_user_id = user_id
            target_tenant_id = None
        elif current_user.role and current_user.role.name in ["TENANT_ADMIN", "SECURITY_OFFICER"]:
            target_user_id = user_id
            target_tenant_id = current_user.tenant_id
        else:
            target_user_id = current_user.id
            target_tenant_id = None

        sessions = SecurityRepository.get_active_sessions(
            db,
            user_id=target_user_id,
            tenant_id=target_tenant_id
        )
        items = [UserSessionResponse.model_validate(s) for s in sessions]
        return SessionListResponse(sessions=items, total=len(items))

    @classmethod
    def revoke_session(
        cls,
        db: Session,
        current_user: User,
        session_id: int
    ) -> UserSessionResponse:
        """
        Revoke an active session by ID after authorization verification.
        """
        session = SecurityRepository.get_session_by_id(db, session_id)
        if not session:
            raise NotFoundException(f"Session with ID {session_id} not found")

        # Check permission to revoke session
        is_owner = session.user_id == current_user.id
        is_tenant_admin = (
            current_user.role and 
            current_user.role.name in ["TENANT_ADMIN", "SECURITY_OFFICER"] and 
            session.tenant_id == current_user.tenant_id
        )
        if not (current_user.is_super_admin or is_tenant_admin or is_owner):
            raise AuthorizationException("Not authorized to revoke this session")

        revoked_session = SecurityRepository.revoke_session(db, session_id)

        # Log security event
        SecurityRepository.create_security_log(
            db,
            event_type="SESSION_REVOKED",
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            severity="MEDIUM",
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_fingerprint=session.device_fingerprint,
            details={"revoked_by_user_id": current_user.id, "session_id": session_id}
        )

        return UserSessionResponse.model_validate(revoked_session)

    @classmethod
    def get_security_activities(
        cls,
        db: Session,
        current_user: User,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> SecurityActivityListResponse:
        """
        Query security activity logs with multi-tenant RBAC enforcement.
        """
        # RBAC filtering logic
        if current_user.is_super_admin:
            eff_tenant_id = tenant_id
            eff_user_id = user_id
        elif current_user.role and current_user.role.name in ["TENANT_ADMIN", "SECURITY_OFFICER"]:
            eff_tenant_id = current_user.tenant_id
            eff_user_id = user_id
        else:
            eff_tenant_id = current_user.tenant_id
            eff_user_id = current_user.id

        items, total = SecurityRepository.get_security_activities(
            db,
            tenant_id=eff_tenant_id,
            user_id=eff_user_id,
            event_type=event_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit
        )

        activity_dtos = [SecurityActivityResponse.model_validate(item) for item in items]
        return SecurityActivityListResponse(
            activities=activity_dtos,
            total=total,
            page=page,
            limit=limit
        )

    @classmethod
    def get_security_dashboard(
        cls,
        db: Session,
        current_user: User
    ) -> SecurityDashboardResponse:
        """
        Retrieve security metrics summary and recent high-priority security activities.
        """
        tenant_id = None if current_user.is_super_admin else current_user.tenant_id
        metrics_dict = SecurityRepository.get_dashboard_metrics(db, tenant_id=tenant_id)
        metrics = SecurityDashboardMetrics(**metrics_dict)

        recent_items, _ = SecurityRepository.get_security_activities(
            db,
            tenant_id=tenant_id,
            page=1,
            limit=10
        )
        recent_dtos = [SecurityActivityResponse.model_validate(item) for item in recent_items]

        return SecurityDashboardResponse(
            metrics=metrics,
            recent_activities=recent_dtos
        )

    @classmethod
    def check_account_lockout(cls, db: Session, user: User) -> None:
        """
        Check if user account is locked. If locked, raise AccountLockedException.
        """
        is_locked, locked_until = SecurityRepository.is_account_locked(db, user)
        if is_locked and locked_until:
            formatted_time = locked_until.strftime("%H:%M:%S UTC")
            raise AccountLockedException(
                f"Account is temporarily locked due to multiple failed login attempts until {formatted_time}"
            )

    @classmethod
    def handle_failed_login(
        cls,
        db: Session,
        user: Optional[User],
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> None:
        """
        Record failed login attempt, update counter, and trigger lockout / alert if threshold reached.
        """
        is_locked = False
        user_id = user.id if user else None
        tenant_id = user.tenant_id if user else None

        if user:
            is_locked = SecurityRepository.increment_failed_logins(db, user)

        severity = "CRITICAL" if is_locked else "MEDIUM"
        event_type = "ACCOUNT_LOCKED" if is_locked else "LOGIN_FAILED"

        SecurityRepository.create_security_log(
            db,
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            details={"email": email, "reason": "Invalid credentials", "is_locked": is_locked}
        )

    @classmethod
    def handle_successful_login(
        cls,
        db: Session,
        user: User,
        token_jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> UserSession:
        """
        Reset failed attempts, create new active UserSession, check for suspicious device/IP, and log success.
        """
        # Reset lockout counters
        SecurityRepository.reset_failed_logins(db, user)

        # Check for suspicious activity (e.g., login from unseen device fingerprint)
        cls.detect_suspicious_activity(
            db,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint
        )

        # Create active session
        session = SecurityRepository.create_session(
            db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_jti=token_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint
        )

        # Log LOGIN_SUCCESS
        SecurityRepository.create_security_log(
            db,
            event_type="LOGIN_SUCCESS",
            user_id=user.id,
            tenant_id=user.tenant_id,
            severity="LOW",
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            details={"session_id": session.id}
        )

        return session

    @classmethod
    def detect_suspicious_activity(
        cls,
        db: Session,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> None:
        """
        Detect if login is coming from a new unknown device fingerprint or IP.
        """
        if not device_fingerprint:
            return

        # Query existing user sessions for matching fingerprint
        previous_session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.device_fingerprint == device_fingerprint
        ).first()

        if not previous_session:
            # First time login from this device fingerprint
            SecurityRepository.create_security_log(
                db,
                event_type="SUSPICIOUS_ACTIVITY",
                user_id=user.id,
                tenant_id=user.tenant_id,
                severity="HIGH",
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                details={"reason": "Login from unrecognized device fingerprint"}
            )
