from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.visitor import Visitor
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.checkin import CheckIn, CheckInStatus
from app.models.user import User
from app.schemas.report import (
    ReportSummaryResponse,
    VisitorAnalyticsReportResponse,
    GateActivityReportResponse
)
from app.services.export_service import ExportService


class ReportService:
    """
    Service aggregating metrics across Visitors, Visit Requests, Passes, Check-Ins, and Tenant Analytics.
    """

    @classmethod
    def get_summary_report(
        cls, 
        db: Session, 
        current_user: User, 
        tenant_id: Optional[int] = None
    ) -> ReportSummaryResponse:
        target_tenant_id = current_user.tenant_id if current_user.role.name != "SUPER_ADMIN" else (tenant_id or current_user.tenant_id)

        visitor_q = db.query(Visitor)
        request_q = db.query(VisitRequest)
        pass_q = db.query(VisitorPass)
        checkin_q = db.query(CheckIn)

        if target_tenant_id:
            visitor_q = visitor_q.filter(Visitor.tenant_id == target_tenant_id)
            request_q = request_q.filter(VisitRequest.tenant_id == target_tenant_id)
            pass_q = pass_q.filter(VisitorPass.tenant_id == target_tenant_id)
            checkin_q = checkin_q.filter(CheckIn.tenant_id == target_tenant_id)

        total_visitors = visitor_q.count()
        verified_visitors = visitor_q.filter(Visitor.verified == True).count()
        blacklisted_visitors = visitor_q.filter(Visitor.blacklisted == True).count()

        total_requests = request_q.count()
        approved_requests = request_q.filter(VisitRequest.status == VisitRequestStatus.APPROVED).count()
        rejected_requests = request_q.filter(VisitRequest.status == VisitRequestStatus.REJECTED).count()
        pending_requests = request_q.filter(VisitRequest.status == VisitRequestStatus.PENDING).count()

        total_passes = pass_q.count()
        active_passes = pass_q.filter(VisitorPass.status == PassStatus.ACTIVE).count()

        total_checkins = checkin_q.filter(CheckIn.status == CheckInStatus.CHECKED_IN).count()
        total_checkouts = checkin_q.filter(CheckIn.status == CheckInStatus.CHECKED_OUT).count()

        durations = []
        completed_checkins = checkin_q.filter(
            CheckIn.status == CheckInStatus.CHECKED_OUT,
            CheckIn.visit_duration_minutes.isnot(None)
        ).all()
        for c in completed_checkins:
            if c.visit_duration_minutes is not None:
                durations.append(c.visit_duration_minutes)

        avg_duration = float(sum(durations) / len(durations)) if durations else 0.0

        return ReportSummaryResponse(
            tenant_id=target_tenant_id,
            total_visitors=total_visitors,
            verified_visitors=verified_visitors,
            blacklisted_visitors=blacklisted_visitors,
            total_visit_requests=total_requests,
            approved_requests=approved_requests,
            rejected_requests=rejected_requests,
            pending_requests=pending_requests,
            total_passes_issued=total_passes,
            active_passes=active_passes,
            total_checkins=total_checkins,
            total_checkouts=total_checkouts,
            average_stay_duration_minutes=round(avg_duration, 2)
        )

    @classmethod
    def get_visitor_analytics(
        cls, 
        db: Session, 
        current_user: User, 
        tenant_id: Optional[int] = None
    ) -> VisitorAnalyticsReportResponse:
        target_tenant_id = current_user.tenant_id if current_user.role.name != "SUPER_ADMIN" else (tenant_id or current_user.tenant_id)
        
        q = db.query(Visitor)
        if target_tenant_id:
            q = q.filter(Visitor.tenant_id == target_tenant_id)

        visitors = q.all()
        by_company: Dict[str, int] = {}
        by_verification: Dict[str, int] = {}
        verified_count = 0
        blacklisted_count = 0

        for v in visitors:
            if v.verified:
                verified_count += 1
            if v.blacklisted:
                blacklisted_count += 1

            comp = v.company or "Unknown"
            by_company[comp] = by_company.get(comp, 0) + 1

            v_status = v.verification_status.value if v.verification_status else "UNVERIFIED"
            by_verification[v_status] = by_verification.get(v_status, 0) + 1

        return VisitorAnalyticsReportResponse(
            total_visitors=len(visitors),
            new_visitors_period=len(visitors),
            verified_count=verified_count,
            blacklisted_count=blacklisted_count,
            by_company=by_company,
            by_verification_status=by_verification
        )

    @classmethod
    def get_gate_activity(
        cls, 
        db: Session, 
        current_user: User, 
        tenant_id: Optional[int] = None
    ) -> GateActivityReportResponse:
        target_tenant_id = current_user.tenant_id if current_user.role.name != "SUPER_ADMIN" else (tenant_id or current_user.tenant_id)
        
        q = db.query(CheckIn)
        if target_tenant_id:
            q = q.filter(CheckIn.tenant_id == target_tenant_id)

        total_checkins = q.filter(CheckIn.status == CheckInStatus.CHECKED_IN).count()
        total_checkouts = q.filter(CheckIn.status == CheckInStatus.CHECKED_OUT).count()
        currently_on_site = q.filter(CheckIn.status == CheckInStatus.CHECKED_IN).count()
        manual_overrides = q.filter(CheckIn.is_manual_checkin == True).count()

        return GateActivityReportResponse(
            total_checkins=total_checkins,
            total_checkouts=total_checkouts,
            currently_on_site=currently_on_site,
            verification_failures=0,
            manual_overrides=manual_overrides
        )

    @classmethod
    def export_summary_csv(
        cls, 
        db: Session, 
        current_user: User, 
        tenant_id: Optional[int] = None
    ) -> str:
        summary = cls.get_summary_report(db, current_user, tenant_id)
        headers = [
            "Metric", "Value"
        ]
        rows = [
            {"Metric": "Tenant ID", "Value": str(summary.tenant_id or "All")},
            {"Metric": "Total Visitors", "Value": str(summary.total_visitors)},
            {"Metric": "Verified Visitors", "Value": str(summary.verified_visitors)},
            {"Metric": "Blacklisted Visitors", "Value": str(summary.blacklisted_visitors)},
            {"Metric": "Total Visit Requests", "Value": str(summary.total_visit_requests)},
            {"Metric": "Approved Requests", "Value": str(summary.approved_requests)},
            {"Metric": "Rejected Requests", "Value": str(summary.rejected_requests)},
            {"Metric": "Pending Requests", "Value": str(summary.pending_requests)},
            {"Metric": "Total Passes Issued", "Value": str(summary.total_passes_issued)},
            {"Metric": "Active Passes", "Value": str(summary.active_passes)},
            {"Metric": "Total Check-Ins", "Value": str(summary.total_checkins)},
            {"Metric": "Total Check-Outs", "Value": str(summary.total_checkouts)},
            {"Metric": "Average Stay Duration (Mins)", "Value": str(summary.average_stay_duration_minutes)}
        ]
        return ExportService.generate_csv(headers, rows)
