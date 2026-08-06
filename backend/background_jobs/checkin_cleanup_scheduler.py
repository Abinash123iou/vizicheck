import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from database.session import SessionLocal
from app.models.checkin import CheckIn, CheckInStatus
from app.models.visitor_pass import VisitorPass, PassStatus, PassStatusHistory
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.repositories.checkin_repository import CheckInRepository
from app.repositories.audit_repository import AuditRepository
from app.services.notification_service import NotificationService
from app.utils.logger import get_logger

logger = get_logger("checkin_cleanup_scheduler")


def run_overdue_checkin_cleanup(db: Optional[Session] = None) -> int:
    """
    Background scheduler routine that identifies visitors who remain CHECKED_IN
    past their scheduled visit end time, notifies hosts and security officers of overstay alerts,
    records gate event history, and automatically completes stale check-ins if threshold exceeded.
    """
    close_db_on_exit = False
    if db is None:
        db = SessionLocal()
        close_db_on_exit = True

    try:
        overdue_checkins = CheckInRepository.list_overdue_checkins(db)
        if not overdue_checkins:
            return 0

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        flagged_count = 0

        for c in overdue_checkins:
            vpass = db.query(VisitorPass).filter(VisitorPass.id == c.pass_id).first()
            vreq = db.query(VisitRequest).filter(VisitRequest.id == c.visit_request_id).first()
            host = vreq.host if vreq else None

            # Dispatch overstay notification
            NotificationService.notify_overstay(checkin=c, visitor_pass=vpass, host=host)

            # Record overstay gate event if not recorded recently
            CheckInRepository.record_gate_event(
                db=db,
                tenant_id=c.tenant_id,
                event_type="OVERSTAY_ALERT",
                performed_by=None,
                checkin_id=c.id,
                pass_id=c.pass_id,
                gate_device_id=c.gate_device_id,
                details=f"Visitor overstay alert: Scheduled end time was {vreq.scheduled_end_time if vreq else 'N/A'}"
            )

            # Auto-complete stale checkins older than 24 hours overdue
            if vreq and vreq.scheduled_end_time and (now - vreq.scheduled_end_time) > timedelta(hours=24):
                duration_td = now - c.checkin_time
                duration_seconds = max(0, int(duration_td.total_seconds()))
                duration_minutes = round(duration_seconds / 60.0, 2)

                c.status = CheckInStatus.CHECKED_OUT
                c.checkout_time = now
                c.visit_duration_minutes = duration_minutes
                c.visit_duration_seconds = duration_seconds
                c.checkout_notes = "Auto-completed by background cleanup scheduler due to 24hr overstay"

                if vpass and vpass.status != PassStatus.COMPLETED:
                    old_st = vpass.status
                    vpass.status = PassStatus.COMPLETED
                    vpass.completed_at = now
                    db.add(PassStatusHistory(
                        pass_id=vpass.id,
                        old_status=old_st,
                        new_status=PassStatus.COMPLETED,
                        changed_by=None,
                        remarks="Pass auto-completed by background overstay scheduler"
                    ))

                if vreq:
                    vreq.status = VisitRequestStatus.COMPLETED
                    vreq.actual_checkout = now

                db.commit()

            flagged_count += 1

        logger.info(f"[Checkin Cleanup Scheduler] Evaluated {flagged_count} overdue visitor check-in(s).")
        return flagged_count

    except Exception as e:
        logger.error(f"[Checkin Cleanup Scheduler Error] {str(e)}")
        return 0
    finally:
        if close_db_on_exit:
            db.close()


if __name__ == "__main__":
    print("Running background check-in overdue cleanup...")
    count = run_overdue_checkin_cleanup()
    print(f"Completed. Processed {count} overdue check-in(s).")
