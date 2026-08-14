from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.permissions import has_permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.schemas.auth import ResponseEnvelope
from app.schemas.report import (
    ReportSummaryResponse,
    VisitorAnalyticsReportResponse,
    GateActivityReportResponse
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Report & Analytics Management"])


@router.get("/summary", response_model=ResponseEnvelope[ReportSummaryResponse])
def get_summary_report(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID filter (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.REPORTS_READ))
):
    """
    Retrieve aggregated tenant summary metrics.
    """
    report = ReportService.get_summary_report(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Summary report retrieved successfully",
        data=report
    )


@router.get("/visitors", response_model=ResponseEnvelope[VisitorAnalyticsReportResponse])
def get_visitor_analytics(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID filter (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.REPORTS_READ))
):
    """
    Retrieve visitor analytics report.
    """
    report = ReportService.get_visitor_analytics(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Visitor analytics report retrieved successfully",
        data=report
    )


@router.get("/gate", response_model=ResponseEnvelope[GateActivityReportResponse])
def get_gate_activity_report(
    tenant_id: Optional[int] = Query(default=None, description="Tenant ID filter (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.REPORTS_READ))
):
    """
    Retrieve gate activity and check-in report.
    """
    report = ReportService.get_gate_activity(db=db, current_user=current_user, tenant_id=tenant_id)
    return ResponseEnvelope(
        success=True,
        message="Gate activity report retrieved successfully",
        data=report
    )


@router.get("/export")
def export_summary_report(
    tenant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission(Permissions.REPORTS_EXPORT))
):
    """
    Export summary metrics report in CSV format.
    """
    csv_data = ReportService.export_summary_csv(db=db, current_user=current_user, tenant_id=tenant_id)
    filename = f"report_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
