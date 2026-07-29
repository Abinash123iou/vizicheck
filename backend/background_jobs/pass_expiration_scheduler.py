import sys
import os
from datetime import datetime
from typing import Optional

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from database.session import SessionLocal
from app.models.visitor_pass import VisitorPass, PassStatus
from app.repositories.pass_repository import PassRepository
from app.repositories.qr_repository import QRRepository
from app.repositories.audit_repository import AuditRepository
from app.constants.audit_actions import AuditActions
from app.services.notification_service import NotificationService
from app.utils.logger import get_logger

logger = get_logger("pass_expiration_scheduler")


def run_pass_expiration_check(db: Optional[Session] = None) -> int:
    """
    Background scheduler job that queries all ACTIVE visitor passes whose valid_until timestamp
    is in the past, automatically transitions their status to EXPIRED, deactivates active QR tokens,
    logs status history & audit trails, and triggers expiration notifications.
    Returns the count of passes expired.
    """
    close_db_on_exit = False
    if db is None:
        db = SessionLocal()
        close_db_on_exit = True

    try:
        expired_passes = PassRepository.find_expired_active_passes(db)
        if not expired_passes:
            return 0

        expired_count = 0
        for p in expired_passes:
            old_status = p.status
            p.status = PassStatus.EXPIRED
            PassRepository.update(db, p)

            # Deactivate active QR tokens for expired pass
            QRRepository.deactivate_tokens_for_pass(db, p.id)

            # Record Pass Status History
            PassRepository.record_status_change(
                db=db,
                pass_id=p.id,
                old_status=old_status,
                new_status=PassStatus.EXPIRED,
                changed_by=None,
                remarks="Pass automatically expired by background scheduler"
            )

            # System Audit Log
            AuditRepository.create_audit_log(
                db=db,
                user_id=None,
                action=AuditActions.PASS_EXPIRED,
                module="BACKGROUND_SCHEDULER",
                entity_id=p.id,
                new_value={
                    "pass_code": p.pass_code,
                    "valid_until": str(p.valid_until),
                    "status": PassStatus.EXPIRED.value
                }
            )

            # Notification Hook
            NotificationService.notify_pass_expired(p)
            expired_count += 1

        logger.info(f"[Pass Expiration Scheduler] Expired {expired_count} ACTIVE visitor pass(es).")
        return expired_count

    except Exception as e:
        logger.error(f"[Pass Expiration Scheduler Error] {str(e)}")
        return 0
    finally:
        if close_db_on_exit:
            db.close()


if __name__ == "__main__":
    print("Running background pass expiration check...")
    count = run_pass_expiration_check()
    print(f"Completed. {count} pass(es) expired.")
