import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.checkin import CheckIn, CheckInStatus, GateVerificationStatus
from app.models.visitor_pass import VisitorPass, PassStatus, PassStatusHistory
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.schemas.checkin_schema import (
    QRCheckInRequest,
    ManualCheckInRequest,
    QRCheckOutRequest,
    ManualCheckOutRequest,
    UndoCheckInRequest,
    CheckInResponse,
    ScanLogResponse,
    GateEventResponse,
    CheckInPaginationRequest,
    CheckInStatisticsResponse,
    LiveDashboardResponse
)
from app.schemas.user import EnhancedPaginationResponse
from app.repositories.checkin_repository import CheckInRepository
from app.validators.checkin_validator import CheckInValidator
from app.mappers.checkin_mapper import CheckInMapper
from app.services.notification_service import NotificationService
from app.repositories.audit_repository import AuditRepository
from app.utils.logger import get_logger

logger = get_logger("checkin_service")


class CheckInService:
    """
    Core business service managing gate check-ins, check-outs, manual overrides,
    live occupancy dashboard metrics, CSV reports, scan analytics, and admin state undo.
    """

    @classmethod
    def scan_checkin(
        cls, 
        db: Session, 
        current_user: User, 
        request_data: QRCheckInRequest,
        ip_address: Optional[str] = None
    ) -> CheckInResponse:
        """
        Execute QR scan check-in flow with 12-stage enterprise validation pipeline.
        """
        device_meta = request_data.device_meta

        # Run 12-stage validation pipeline
        visitor_pass, qr_token, visit_request, visitor, claims, target_tenant_id = CheckInValidator.validate_qr_scan_for_checkin(
            db=db,
            current_user=current_user,
            raw_qr_token=request_data.qr_token,
            client_ip=ip_address,
            gate_device_id=device_meta.gate_device_id if device_meta else None
        )


        now = datetime.utcnow()

        # Update Pass Status to USED
        old_pass_status = visitor_pass.status
        visitor_pass.status = PassStatus.USED
        visitor_pass.used_at = now
        visitor_pass.updated_at = now

        pass_history = PassStatusHistory(
            pass_id=visitor_pass.id,
            old_status=old_pass_status,
            new_status=PassStatus.USED,
            changed_by=current_user.id,
            remarks=f"Checked in via QR Scan at {device_meta.gate_name if device_meta else 'Main Gate'}"
        )
        db.add(pass_history)

        # Update Visit Request Status to CHECKED_IN
        visit_request.status = VisitRequestStatus.CHECKED_IN
        visit_request.actual_checkin = now

        # Create CheckIn domain entity
        checkin = CheckIn(
            tenant_id=target_tenant_id,
            pass_id=visitor_pass.id,
            visit_request_id=visit_request.id,
            visitor_id=visitor.id,
            host_id=visit_request.host_id,
            checkin_time=now,
            status=CheckInStatus.CHECKED_IN,

            gate_device_id=device_meta.gate_device_id if device_meta else "DEV-GATE-01",
            scanner_name=device_meta.scanner_name if device_meta else "Main Gate Scanner 1",
            scanner_ip=device_meta.scanner_ip if device_meta else ip_address,
            scanner_location=device_meta.scanner_location if device_meta else "Main Gate Entrance",
            scanner_version=device_meta.scanner_version if device_meta else "v1.0.0",
            gate_name=device_meta.gate_name if device_meta else "Main Gate",
            gate_number=device_meta.gate_number if device_meta else "Gate 1",

            verification_method="QR_SCAN",
            checked_in_by=current_user.id,
            checkin_notes=request_data.notes,
            is_manual_checkin=False
        )

        CheckInRepository.create_checkin(db=db, checkin=checkin)

        # Log SUCCESS scan log
        CheckInRepository.log_scan(
            db=db,
            tenant_id=target_tenant_id,
            scan_result=GateVerificationStatus.SUCCESS,
            reason="QR Code validated successfully for Check-In",
            gate_device_id=checkin.gate_device_id,
            scanner_name=checkin.scanner_name,
            scanner_ip=checkin.scanner_ip,
            qr_token=request_data.qr_token,
            pass_id=visitor_pass.id,
            visitor_id=visitor.id,
            ip_address=ip_address
        )

        # Record Gate Event History
        CheckInRepository.record_gate_event(
            db=db,
            tenant_id=target_tenant_id,
            event_type="CHECK_IN",
            performed_by=current_user.id,
            checkin_id=checkin.id,
            pass_id=visitor_pass.id,
            gate_device_id=checkin.gate_device_id,
            details=f"Visitor '{visitor.first_name} {visitor.last_name}' checked in at {checkin.gate_name}"
        )

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="GATE_CHECKIN",
            module="GATE_SECURITY",
            ip_address=ip_address,
            entity_id=checkin.id,
            new_value={"checkin_id": checkin.id, "pass_code": visitor_pass.pass_code, "visitor_id": visitor.id}
        )

        # Trigger Notifications
        NotificationService.notify_host_checkin(checkin=checkin, visitor_pass=visitor_pass, host=visit_request.host)

        return CheckInMapper.to_checkin_response(checkin)

    @classmethod
    def manual_checkin(
        cls, 
        db: Session, 
        current_user: User, 
        request_data: ManualCheckInRequest,
        ip_address: Optional[str] = None
    ) -> CheckInResponse:
        """
        Execute security guard manual check-in override.
        """
        visitor_pass, visit_request, visitor, target_tenant_id = CheckInValidator.validate_manual_checkin(
            db=db,
            current_user=current_user,
            pass_code=request_data.pass_code,
            pass_id=request_data.pass_id,
            request_code=request_data.request_code,
            reason=request_data.reason
        )
        device_meta = request_data.device_meta



        now = datetime.utcnow()

        # Update Pass Status to USED
        old_status = visitor_pass.status
        visitor_pass.status = PassStatus.USED
        visitor_pass.used_at = now

        pass_history = PassStatusHistory(
            pass_id=visitor_pass.id,
            old_status=old_status,
            new_status=PassStatus.USED,
            changed_by=current_user.id,
            remarks=f"Manual Check-in Override: {request_data.reason}"
        )
        db.add(pass_history)

        # Update Visit Request
        visit_request.status = VisitRequestStatus.CHECKED_IN
        visit_request.actual_checkin = now

        # Create CheckIn
        checkin = CheckIn(
            tenant_id=target_tenant_id,
            pass_id=visitor_pass.id,
            visit_request_id=visit_request.id,
            visitor_id=visitor.id,
            host_id=visit_request.host_id,
            checkin_time=now,
            status=CheckInStatus.CHECKED_IN,

            gate_device_id=device_meta.gate_device_id if device_meta else "DEV-GATE-01",
            scanner_name=device_meta.scanner_name if device_meta else "Main Gate Scanner 1",
            scanner_ip=device_meta.scanner_ip if device_meta else ip_address,
            scanner_location=device_meta.scanner_location if device_meta else "Main Gate Entrance",
            scanner_version=device_meta.scanner_version if device_meta else "v1.0.0",
            gate_name=device_meta.gate_name if device_meta else "Main Gate",
            gate_number=device_meta.gate_number if device_meta else "Gate 1",

            verification_method="MANUAL",
            checked_in_by=current_user.id,
            checkin_notes=request_data.notes,
            is_manual_checkin=True,
            manual_checkin_reason=request_data.reason
        )

        CheckInRepository.create_checkin(db=db, checkin=checkin)

        # Gate Event History
        CheckInRepository.record_gate_event(
            db=db,
            tenant_id=target_tenant_id,
            event_type="MANUAL_CHECKIN",
            performed_by=current_user.id,
            checkin_id=checkin.id,
            pass_id=visitor_pass.id,
            gate_device_id=checkin.gate_device_id,
            details=f"Manual check-in override for visitor '{visitor.first_name} {visitor.last_name}'. Reason: {request_data.reason}"
        )

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="MANUAL_CHECKIN",
            module="GATE_SECURITY",
            ip_address=ip_address,
            entity_id=checkin.id,
            new_value={"checkin_id": checkin.id, "reason": request_data.reason}
        )

        NotificationService.notify_manual_override(checkin=checkin, performed_by=current_user, reason=request_data.reason)
        NotificationService.notify_host_checkin(checkin=checkin, visitor_pass=visitor_pass, host=visit_request.host)

        return CheckInMapper.to_checkin_response(checkin)

    @classmethod
    def scan_checkout(
        cls, 
        db: Session, 
        current_user: User, 
        request_data: QRCheckOutRequest,
        ip_address: Optional[str] = None
    ) -> CheckInResponse:
        """
        Execute exit scan check-out flow with duration calculation.
        """
        device_meta = request_data.device_meta

        active_checkin, visitor_pass, qr_token, claims, target_tenant_id = CheckInValidator.validate_qr_scan_for_checkout(
            db=db,
            current_user=current_user,
            raw_qr_token=request_data.qr_token,
            client_ip=ip_address,
            gate_device_id=device_meta.gate_device_id if device_meta else None
        )


        now = datetime.utcnow()

        # Calculate Attendance Duration
        duration_td = now - active_checkin.checkin_time
        duration_seconds = max(0, int(duration_td.total_seconds()))
        duration_minutes = round(duration_seconds / 60.0, 2)

        active_checkin.checkout_time = now
        active_checkin.status = CheckInStatus.CHECKED_OUT
        active_checkin.visit_duration_minutes = duration_minutes
        active_checkin.visit_duration_seconds = duration_seconds
        active_checkin.checked_out_by = current_user.id
        active_checkin.checkout_notes = request_data.notes

        CheckInRepository.update_checkin(db=db, checkin=active_checkin)

        # Update Visitor Pass to COMPLETED
        old_status = visitor_pass.status
        visitor_pass.status = PassStatus.COMPLETED
        visitor_pass.completed_at = now

        pass_history = PassStatusHistory(
            pass_id=visitor_pass.id,
            old_status=old_status,
            new_status=PassStatus.COMPLETED,
            changed_by=current_user.id,
            remarks=f"Checked out via QR Scan. Duration: {duration_minutes} mins"
        )
        db.add(pass_history)

        # Update Visit Request to COMPLETED
        visit_request = db.query(VisitRequest).filter(VisitRequest.id == active_checkin.visit_request_id).first()
        if visit_request:
            visit_request.status = VisitRequestStatus.COMPLETED
            visit_request.actual_checkout = now

        # Log SUCCESS scan
        CheckInRepository.log_scan(
            db=db,
            tenant_id=target_tenant_id,
            scan_result=GateVerificationStatus.SUCCESS,
            reason="QR Code validated successfully for Check-Out",
            gate_device_id=device_meta.gate_device_id if device_meta else active_checkin.gate_device_id,
            qr_token=request_data.qr_token,
            pass_id=visitor_pass.id,
            visitor_id=active_checkin.visitor_id,
            ip_address=ip_address
        )

        # Gate Event History
        CheckInRepository.record_gate_event(
            db=db,
            tenant_id=target_tenant_id,
            event_type="CHECK_OUT",
            performed_by=current_user.id,
            checkin_id=active_checkin.id,
            pass_id=visitor_pass.id,
            gate_device_id=active_checkin.gate_device_id,
            details=f"Visitor checked out. Visit Duration: {duration_minutes} minutes"
        )

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="GATE_CHECKOUT",
            module="GATE_SECURITY",
            ip_address=ip_address,
            entity_id=active_checkin.id,
            new_value={"checkin_id": active_checkin.id, "duration_minutes": duration_minutes}
        )

        NotificationService.notify_host_checkout(checkin=active_checkin, visitor_pass=visitor_pass, host=visit_request.host if visit_request else None)

        return CheckInMapper.to_checkin_response(active_checkin)

    @classmethod
    def manual_checkout(
        cls, 
        db: Session, 
        current_user: User, 
        request_data: ManualCheckOutRequest,
        ip_address: Optional[str] = None
    ) -> CheckInResponse:
        """
        Execute security guard manual check-out override.
        """
        active_checkin, visitor_pass, target_tenant_id = CheckInValidator.validate_manual_checkout(
            db=db,
            current_user=current_user,
            checkin_id=request_data.checkin_id,
            pass_code=request_data.pass_code,
            reason=request_data.reason
        )


        now = datetime.utcnow()
        duration_td = now - active_checkin.checkin_time
        duration_seconds = max(0, int(duration_td.total_seconds()))
        duration_minutes = round(duration_seconds / 60.0, 2)

        active_checkin.checkout_time = now
        active_checkin.status = CheckInStatus.CHECKED_OUT
        active_checkin.visit_duration_minutes = duration_minutes
        active_checkin.visit_duration_seconds = duration_seconds
        active_checkin.checked_out_by = current_user.id
        active_checkin.checkout_notes = request_data.notes
        active_checkin.is_manual_checkout = True
        active_checkin.manual_checkout_reason = request_data.reason

        CheckInRepository.update_checkin(db=db, checkin=active_checkin)

        # Update Visitor Pass & Visit Request
        if visitor_pass:
            old_status = visitor_pass.status
            visitor_pass.status = PassStatus.COMPLETED
            visitor_pass.completed_at = now
            db.add(PassStatusHistory(
                pass_id=visitor_pass.id,
                old_status=old_status,
                new_status=PassStatus.COMPLETED,
                changed_by=current_user.id,
                remarks=f"Manual Check-out Override: {request_data.reason}"
            ))

        visit_request = db.query(VisitRequest).filter(VisitRequest.id == active_checkin.visit_request_id).first()
        if visit_request:
            visit_request.status = VisitRequestStatus.COMPLETED
            visit_request.actual_checkout = now

        CheckInRepository.record_gate_event(
            db=db,
            tenant_id=target_tenant_id,
            event_type="MANUAL_CHECKOUT",
            performed_by=current_user.id,
            checkin_id=active_checkin.id,
            pass_id=active_checkin.pass_id,
            gate_device_id=active_checkin.gate_device_id,
            details=f"Manual check-out override. Reason: {request_data.reason}"
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="MANUAL_CHECKOUT",
            module="GATE_SECURITY",
            ip_address=ip_address,
            entity_id=active_checkin.id,
            new_value={"checkin_id": active_checkin.id, "reason": request_data.reason}
        )

        NotificationService.notify_manual_override(checkin=active_checkin, performed_by=current_user, reason=request_data.reason)
        NotificationService.notify_host_checkout(checkin=active_checkin, visitor_pass=visitor_pass, host=visit_request.host if visit_request else None)

        return CheckInMapper.to_checkin_response(active_checkin)

    @classmethod
    def get_checkin_by_id(cls, db: Session, current_user: User, checkin_id: int) -> CheckInResponse:
        """
        Fetch details of a single check-in record.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, db=db)
        checkin = CheckInRepository.get_by_id(db=db, checkin_id=checkin_id, tenant_id=target_tenant_id)
        if not checkin:
            from app.core.exceptions import NotFoundException
            raise NotFoundException(f"Check-in record ID {checkin_id} not found")
        return CheckInMapper.to_checkin_response(checkin)

    @classmethod
    def list_checkins(
        cls, 
        db: Session, 
        current_user: User, 
        params: CheckInPaginationRequest
    ) -> EnhancedPaginationResponse[CheckInResponse]:
        """
        Retrieve paginated list of check-in records.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, request_tenant_id=params.tenant_id, db=db)
        checkins, total = CheckInRepository.list_checkins(db=db, tenant_id=target_tenant_id, params=params)
        dto_list = CheckInMapper.to_checkin_response_list(checkins)

        total_pages = (total + params.page_size - 1) // params.page_size if params.page_size > 0 else 0
        return EnhancedPaginationResponse(
            items=dto_list,
            total_records=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )

    @classmethod
    def get_active_visitors(
        cls, 
        db: Session, 
        current_user: User, 
        params: CheckInPaginationRequest
    ) -> EnhancedPaginationResponse[CheckInResponse]:
        """
        Get visitors currently checked inside facility.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, request_tenant_id=params.tenant_id, db=db)
        checkins, total = CheckInRepository.get_active_visitors(db=db, tenant_id=target_tenant_id, params=params)
        dto_list = CheckInMapper.to_checkin_response_list(checkins)

        total_pages = (total + params.page_size - 1) // params.page_size if params.page_size > 0 else 0
        return EnhancedPaginationResponse(
            items=dto_list,
            total_records=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )


    @classmethod
    def get_statistics(cls, db: Session, current_user: User, tenant_id: Optional[int] = None) -> CheckInStatisticsResponse:
        """
        Fetch summary metrics and statistics.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, request_tenant_id=tenant_id, db=db)
        return CheckInRepository.get_statistics(db=db, tenant_id=target_tenant_id)

    @classmethod
    def get_live_dashboard(cls, db: Session, current_user: User, tenant_id: Optional[int] = None) -> LiveDashboardResponse:
        """
        Assemble Live Security Dashboard response payload.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, request_tenant_id=tenant_id, db=db)
        data = CheckInRepository.get_live_dashboard_metrics(db=db, tenant_id=target_tenant_id)

        recent_dtos = CheckInMapper.to_gate_event_response_list(data["recent_activities"])

        return LiveDashboardResponse(
            visitors_inside=data["visitors_inside"],
            todays_entries=data["todays_entries"],
            todays_exits=data["todays_exits"],
            pending_exits=data["pending_exits"],
            current_occupancy=data["current_occupancy"],
            peak_occupancy_today=data["peak_occupancy_today"],
            average_visit_duration_minutes=data["average_visit_duration_minutes"],
            visitors_inside_by_gate=data["visitors_inside_by_gate"],
            visitors_inside_by_department=data["visitors_inside_by_department"],
            recent_activities=recent_dtos,
            scan_analytics_summary=data["scan_analytics_summary"]
        )

    @classmethod
    def export_checkins_csv(cls, db: Session, current_user: User, params: CheckInPaginationRequest) -> str:
        """
        Export check-in records to CSV format string.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, request_tenant_id=params.tenant_id, db=db)
        params.page_size = 1000  # Export up to 1000 records
        checkins, _ = CheckInRepository.list_checkins(db=db, tenant_id=target_tenant_id, params=params)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "CheckIn ID", "Pass Code", "Visitor Name", "Visitor Phone", "Host Name", "Department",
            "Gate Name", "Gate Device ID", "Check-In Time", "Check-Out Time", "Status",
            "Verification Method", "Visit Duration (Mins)", "Manual Check-in", "Manual Check-out"
        ])

        for c in checkins:
            dto = CheckInMapper.to_checkin_response(c)
            writer.writerow([
                dto.id,
                dto.pass_code or "",
                dto.visitor_name or "",
                dto.visitor_phone or "",
                dto.host_name or "",
                dto.host_department or "",
                dto.gate_name or "",
                dto.gate_device_id or "",
                dto.checkin_time.isoformat() if dto.checkin_time else "",
                dto.checkout_time.isoformat() if dto.checkout_time else "",
                dto.status.value if hasattr(dto.status, "value") else str(dto.status),
                dto.verification_method,
                dto.visit_duration_minutes or 0.0,
                "Yes" if dto.is_manual_checkin else "No",
                "Yes" if dto.is_manual_checkout else "No"
            ])

        return output.getvalue()

    @classmethod
    def list_scan_logs(cls, db: Session, current_user: User, limit: int = 50) -> List[ScanLogResponse]:
        """
        Retrieve recent QR scan attempt logs for security analytics.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, db=db)
        logs = CheckInRepository.list_scan_logs(db=db, tenant_id=target_tenant_id, limit=limit)
        return [CheckInMapper.to_scan_log_response(l) for l in logs]

    @classmethod
    def undo_checkin(
        cls, 
        db: Session, 
        current_user: User, 
        checkin_id: int, 
        request_data: UndoCheckInRequest,
        ip_address: Optional[str] = None
    ) -> CheckInResponse:
        """
        Revert visitor check-in state (Admin only). Reverts pass to ACTIVE and visit request to APPROVED.
        """
        target_tenant_id = CheckInValidator.validate_tenant_boundary(current_user=current_user, db=db)
        checkin = CheckInValidator.validate_undo_checkin(
            db=db, checkin_id=checkin_id, reason=request_data.reason, target_tenant_id=target_tenant_id
        )

        now = datetime.utcnow()
        checkin.is_undone = True
        checkin.status = CheckInStatus.UNDONE
        checkin.undone_by = current_user.id
        checkin.undone_at = now
        checkin.undone_reason = request_data.reason

        CheckInRepository.update_checkin(db=db, checkin=checkin)

        # Revert Visitor Pass to ACTIVE
        visitor_pass = db.query(VisitorPass).filter(VisitorPass.id == checkin.pass_id).first()
        if visitor_pass:
            old_status = visitor_pass.status
            visitor_pass.status = PassStatus.ACTIVE
            visitor_pass.used_at = None
            db.add(PassStatusHistory(
                pass_id=visitor_pass.id,
                old_status=old_status,
                new_status=PassStatus.ACTIVE,
                changed_by=current_user.id,
                remarks=f"Undo Check-In: {request_data.reason}"
            ))

        # Revert Visit Request to APPROVED
        visit_request = db.query(VisitRequest).filter(VisitRequest.id == checkin.visit_request_id).first()
        if visit_request:
            visit_request.status = VisitRequestStatus.APPROVED
            visit_request.actual_checkin = None

        CheckInRepository.record_gate_event(
            db=db,
            tenant_id=target_tenant_id,
            event_type="UNDO",
            performed_by=current_user.id,
            checkin_id=checkin.id,
            pass_id=checkin.pass_id,
            gate_device_id=checkin.gate_device_id,
            details=f"Check-in undone by Admin. Reason: {request_data.reason}"
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UNDO_CHECKIN",
            module="GATE_SECURITY",
            ip_address=ip_address,
            entity_id=checkin.id,
            new_value={"checkin_id": checkin.id, "reason": request_data.reason}
        )

        return CheckInMapper.to_checkin_response(checkin)
