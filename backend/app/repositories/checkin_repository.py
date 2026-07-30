from datetime import datetime, date, time
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session, joinedload

from app.models.checkin import CheckIn, CheckInStatus, ScanLog, GateEventHistory, GateVerificationStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor import Visitor
from app.models.user import User
from app.schemas.checkin_schema import CheckInPaginationRequest, CheckInStatisticsResponse


class CheckInRepository:
    """
    Repository layer handling database persistence, search queries, active occupancy tracking,
    scan logging, and gate event history records.
    """

    @staticmethod
    def create_checkin(db: Session, checkin: CheckIn) -> CheckIn:
        """
        Persist a new CheckIn record to database.
        """
        db.add(checkin)
        db.commit()
        db.refresh(checkin)
        return checkin

    @staticmethod
    def update_checkin(db: Session, checkin: CheckIn) -> CheckIn:
        """
        Update an existing CheckIn record.
        """
        checkin.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(checkin)
        return checkin

    @staticmethod
    def get_by_id(db: Session, checkin_id: int, tenant_id: Optional[int] = None) -> Optional[CheckIn]:
        """
        Fetch check-in record by ID, optionally enforcing tenant isolation.
        """
        query = db.query(CheckIn).options(
            joinedload(CheckIn.visitor),
            joinedload(CheckIn.visitor_pass),
            joinedload(CheckIn.visit_request),
            joinedload(CheckIn.host)
        ).filter(CheckIn.id == checkin_id, CheckIn.is_deleted == False)

        if tenant_id is not None:
            query = query.filter(CheckIn.tenant_id == tenant_id)

        return query.first()

    @staticmethod
    def get_active_checkin_by_pass_id(db: Session, pass_id: int, tenant_id: int) -> Optional[CheckIn]:
        """
        Fetch currently active check-in record (CHECKED_IN status) for a visitor pass.
        """
        return db.query(CheckIn).filter(
            CheckIn.pass_id == pass_id,
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            CheckIn.is_deleted == False
        ).order_by(CheckIn.checkin_time.desc()).first()

    @staticmethod
    def get_active_checkin_by_visitor_id(db: Session, visitor_id: int, tenant_id: int) -> Optional[CheckIn]:
        """
        Fetch currently active check-in record for a visitor ID.
        """
        return db.query(CheckIn).filter(
            CheckIn.visitor_id == visitor_id,
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            CheckIn.is_deleted == False
        ).order_by(CheckIn.checkin_time.desc()).first()

    @staticmethod
    def list_checkins(
        db: Session, 
        tenant_id: int, 
        params: CheckInPaginationRequest
    ) -> Tuple[List[CheckIn], int]:
        """
        Retrieve paginated, searched, and filtered list of check-in records.
        """
        query = db.query(CheckIn).options(
            joinedload(CheckIn.visitor),
            joinedload(CheckIn.visitor_pass),
            joinedload(CheckIn.visit_request),
            joinedload(CheckIn.host)
        ).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.is_deleted == False
        )

        if params.status:
            query = query.filter(CheckIn.status == params.status)

        if params.gate_name:
            query = query.filter(CheckIn.gate_name.ilike(f"%{params.gate_name}%"))

        if params.visitor_id:
            query = query.filter(CheckIn.visitor_id == params.visitor_id)

        if params.host_id:
            query = query.filter(CheckIn.host_id == params.host_id)

        if params.start_date:
            query = query.filter(CheckIn.checkin_time >= params.start_date)

        if params.end_date:
            query = query.filter(CheckIn.checkin_time <= params.end_date)

        if params.search and params.search.strip():
            term = f"%{params.search.strip()}%"
            query = query.join(CheckIn.visitor).join(CheckIn.host).join(CheckIn.visitor_pass).filter(
                or_(
                    Visitor.first_name.ilike(term),
                    Visitor.last_name.ilike(term),
                    Visitor.visitor_code.ilike(term),
                    Visitor.email.ilike(term),
                    Visitor.phone.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    VisitorPass.pass_code.ilike(term),
                    CheckIn.gate_name.ilike(term),
                    CheckIn.gate_device_id.ilike(term)
                )
            )

        total = query.count()

        # Sorting
        sort_attr = getattr(CheckIn, params.sort_by, CheckIn.checkin_time)
        if params.order.lower() == "asc":
            query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(sort_attr.desc())

        # Pagination
        offset = (params.page - 1) * params.page_size
        checkins = query.offset(offset).limit(params.page_size).all()

        return checkins, total

    @staticmethod
    def get_active_visitors(
        db: Session, 
        tenant_id: int, 
        params: CheckInPaginationRequest
    ) -> Tuple[List[CheckIn], int]:
        """
        Get visitors currently checked inside facility (status == CHECKED_IN).
        """
        params.status = CheckInStatus.CHECKED_IN
        return CheckInRepository.list_checkins(db=db, tenant_id=tenant_id, params=params)

    @staticmethod
    def get_statistics(db: Session, tenant_id: int) -> CheckInStatisticsResponse:
        """
        Compute dashboard metrics and analytics summary for check-ins.
        """
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)

        # Total checkins today
        total_checkins_today = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkin_time >= today_start,
            CheckIn.checkin_time <= today_end,
            CheckIn.is_deleted == False
        ).count()

        # Total checkouts today
        total_checkouts_today = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkout_time >= today_start,
            CheckIn.checkout_time <= today_end,
            CheckIn.is_deleted == False
        ).count()

        # Active visitors inside right now
        active_visitors_count = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            CheckIn.is_deleted == False
        ).count()

        # Manual overrides today
        manual_overrides_count = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkin_time >= today_start,
            CheckIn.checkin_time <= today_end,
            or_(CheckIn.is_manual_checkin == True, CheckIn.is_manual_checkout == True),
            CheckIn.is_deleted == False
        ).count()

        # Average visit duration in minutes today
        avg_duration_res = db.query(func.avg(CheckIn.visit_duration_minutes)).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkout_time >= today_start,
            CheckIn.checkout_time <= today_end,
            CheckIn.visit_duration_minutes.isnot(None),
            CheckIn.is_deleted == False
        ).scalar()
        average_visit_duration_minutes = round(float(avg_duration_res), 2) if avg_duration_res else 0.0

        # Gate breakdown
        gate_counts = db.query(
            CheckIn.gate_name, func.count(CheckIn.id)
        ).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkin_time >= today_start,
            CheckIn.is_deleted == False
        ).group_by(CheckIn.gate_name).all()
        gate_breakdown = {g or "Main Gate": cnt for g, cnt in gate_counts}

        # Status breakdown
        status_counts = db.query(
            CheckIn.status, func.count(CheckIn.id)
        ).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.is_deleted == False
        ).group_by(CheckIn.status).all()
        status_breakdown = {st.value if hasattr(st, "value") else str(st): cnt for st, cnt in status_counts}

        return CheckInStatisticsResponse(
            total_checkins_today=total_checkins_today,
            total_checkouts_today=total_checkouts_today,
            active_visitors_count=active_visitors_count,
            manual_overrides_count=manual_overrides_count,
            average_visit_duration_minutes=average_visit_duration_minutes,
            gate_breakdown=gate_breakdown,
            status_breakdown=status_breakdown
        )

    @staticmethod
    def get_live_dashboard_metrics(db: Session, tenant_id: int) -> Dict[str, Any]:
        """
        Assemble metrics for the Live Security Dashboard.
        """
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)

        # Active visitors / Current Occupancy
        active_visitors = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            CheckIn.is_deleted == False
        ).count()

        todays_entries = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkin_time >= today_start,
            CheckIn.checkin_time <= today_end,
            CheckIn.is_deleted == False
        ).count()

        todays_exits = db.query(CheckIn).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkout_time >= today_start,
            CheckIn.checkout_time <= today_end,
            CheckIn.is_deleted == False
        ).count()

        # Pending exits: visitors checked in whose scheduled_end_time is past or approaching
        now = datetime.utcnow()
        pending_exits = db.query(CheckIn).join(CheckIn.visit_request).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            VisitRequest.scheduled_end_time <= now,
            CheckIn.is_deleted == False
        ).count()

        # Visitors inside by gate
        gate_counts = db.query(
            CheckIn.gate_name, func.count(CheckIn.id)
        ).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            CheckIn.is_deleted == False
        ).group_by(CheckIn.gate_name).all()
        visitors_inside_by_gate = {g or "Main Gate": cnt for g, cnt in gate_counts}

        # Visitors inside by department
        dept_counts = db.query(
            VisitRequest.department, func.count(CheckIn.id)
        ).join(CheckIn, CheckIn.visit_request_id == VisitRequest.id).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.status == CheckInStatus.CHECKED_IN,
            CheckIn.is_deleted == False
        ).group_by(VisitRequest.department).all()
        visitors_inside_by_department = {d or "General": cnt for d, cnt in dept_counts}

        # Peak occupancy today
        peak_occupancy_today = max(todays_entries, active_visitors)

        # Avg duration
        avg_dur = db.query(func.avg(CheckIn.visit_duration_minutes)).filter(
            CheckIn.tenant_id == tenant_id,
            CheckIn.checkout_time >= today_start,
            CheckIn.is_deleted == False
        ).scalar()
        avg_duration_minutes = round(float(avg_dur), 2) if avg_dur else 0.0

        # Recent activities
        recent_events = db.query(GateEventHistory).options(
            joinedload(GateEventHistory.performed_by_user)
        ).filter(
            GateEventHistory.tenant_id == tenant_id
        ).order_by(GateEventHistory.created_at.desc()).limit(15).all()

        # Scan analytics summary
        scan_counts = db.query(
            ScanLog.scan_result, func.count(ScanLog.id)
        ).filter(
            ScanLog.tenant_id == tenant_id,
            ScanLog.created_at >= today_start
        ).group_by(ScanLog.scan_result).all()
        scan_analytics_summary = {s.value if hasattr(s, "value") else str(s): cnt for s, cnt in scan_counts}

        return {
            "visitors_inside": active_visitors,
            "todays_entries": todays_entries,
            "todays_exits": todays_exits,
            "pending_exits": pending_exits,
            "current_occupancy": active_visitors,
            "peak_occupancy_today": peak_occupancy_today,
            "average_visit_duration_minutes": avg_duration_minutes,
            "visitors_inside_by_gate": visitors_inside_by_gate,
            "visitors_inside_by_department": visitors_inside_by_department,
            "recent_activities": recent_events,
            "scan_analytics_summary": scan_analytics_summary
        }

    @staticmethod
    def log_scan(
        db: Session,
        tenant_id: int,
        scan_result: GateVerificationStatus,
        reason: str,
        gate_device_id: Optional[str] = None,
        scanner_name: Optional[str] = None,
        scanner_ip: Optional[str] = None,
        qr_token: Optional[str] = None,
        pass_id: Optional[int] = None,
        visitor_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> ScanLog:
        """
        Record a QR scan attempt log (both SUCCESS and FAILED) into scan_logs table.
        """
        scan_log = ScanLog(
            tenant_id=tenant_id,
            pass_id=pass_id,
            visitor_id=visitor_id,
            gate_device_id=gate_device_id or "DEV-GATE-01",
            scanner_name=scanner_name or "Main Gate Scanner 1",
            scanner_ip=scanner_ip,
            qr_token=qr_token[:100] if qr_token else None,  # Snippet for security
            scan_result=scan_result,
            reason=reason,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(scan_log)
        db.commit()
        db.refresh(scan_log)
        return scan_log

    @staticmethod
    def record_gate_event(
        db: Session,
        tenant_id: int,
        event_type: str,
        performed_by: Optional[int] = None,
        checkin_id: Optional[int] = None,
        pass_id: Optional[int] = None,
        gate_device_id: Optional[str] = None,
        details: Optional[str] = None
    ) -> GateEventHistory:
        """
        Record audit event in gate_event_history table.
        """
        event = GateEventHistory(
            tenant_id=tenant_id,
            checkin_id=checkin_id,
            pass_id=pass_id,
            event_type=event_type,
            performed_by=performed_by,
            gate_device_id=gate_device_id or "DEV-GATE-01",
            details=details,
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def list_scan_logs(db: Session, tenant_id: int, limit: int = 50) -> List[ScanLog]:
        """
        Fetch recent scan logs for security analytics.
        """
        return db.query(ScanLog).filter(
            ScanLog.tenant_id == tenant_id
        ).order_by(ScanLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def list_overdue_checkins(db: Session) -> List[CheckIn]:
        """
        Fetch check-ins where visitor is checked in past scheduled end time.
        """
        now = datetime.utcnow()
        return db.query(CheckIn).join(CheckIn.visit_request).filter(
            CheckIn.status == CheckInStatus.CHECKED_IN,
            VisitRequest.scheduled_end_time <= now,
            CheckIn.is_deleted == False
        ).all()
