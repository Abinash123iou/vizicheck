from typing import Optional, List
from app.models.checkin import CheckIn, ScanLog, GateEventHistory
from app.schemas.checkin_schema import CheckInResponse, ScanLogResponse, GateEventResponse


class CheckInMapper:
    """
    Data mapper converting CheckIn, ScanLog, and GateEventHistory domain entities to API DTOs.
    """

    @classmethod
    def to_checkin_response(cls, checkin: CheckIn) -> CheckInResponse:
        """
        Convert CheckIn entity to CheckInResponse DTO with populated nested details.
        """
        visitor_name = None
        visitor_code = None
        visitor_email = None
        visitor_phone = None
        visitor_company = None
        if checkin.visitor:
            first_name = checkin.visitor.first_name or ""
            last_name = checkin.visitor.last_name or ""
            visitor_name = f"{first_name} {last_name}".strip()
            visitor_code = checkin.visitor.visitor_code
            visitor_email = checkin.visitor.email
            visitor_phone = checkin.visitor.phone
            visitor_company = checkin.visitor.company

        host_name = None
        host_department = None
        if checkin.host:
            first = checkin.host.first_name or ""
            last = checkin.host.last_name or ""
            host_name = f"{first} {last}".strip()

        pass_code = checkin.visitor_pass.pass_code if checkin.visitor_pass else None
        request_code = checkin.visit_request.request_code if checkin.visit_request else None
        purpose = checkin.visit_request.purpose if checkin.visit_request else None
        if checkin.visit_request and hasattr(checkin.visit_request, 'department') and checkin.visit_request.department:
            host_department = checkin.visit_request.department

        return CheckInResponse(
            id=checkin.id,
            uuid=checkin.uuid,
            tenant_id=checkin.tenant_id,
            pass_id=checkin.pass_id,
            visit_request_id=checkin.visit_request_id,
            visitor_id=checkin.visitor_id,
            host_id=checkin.host_id,

            checkin_time=checkin.checkin_time,
            checkout_time=checkin.checkout_time,
            status=checkin.status,

            gate_device_id=checkin.gate_device_id,
            scanner_name=checkin.scanner_name,
            scanner_ip=checkin.scanner_ip,
            scanner_location=checkin.scanner_location,
            scanner_version=checkin.scanner_version,
            gate_name=checkin.gate_name,
            gate_number=checkin.gate_number,

            verification_method=checkin.verification_method,
            checked_in_by=checkin.checked_in_by,
            checked_out_by=checkin.checked_out_by,
            checkin_notes=checkin.checkin_notes,
            checkout_notes=checkin.checkout_notes,

            is_manual_checkin=checkin.is_manual_checkin,
            is_manual_checkout=checkin.is_manual_checkout,
            manual_checkin_reason=checkin.manual_checkin_reason,
            manual_checkout_reason=checkin.manual_checkout_reason,

            visit_duration_minutes=checkin.visit_duration_minutes,
            visit_duration_seconds=checkin.visit_duration_seconds,

            is_undone=checkin.is_undone,
            undone_by=checkin.undone_by,
            undone_at=checkin.undone_at,
            undone_reason=checkin.undone_reason,

            visitor_name=visitor_name,
            visitor_code=visitor_code,
            visitor_email=visitor_email,
            visitor_phone=visitor_phone,
            visitor_company=visitor_company,

            host_name=host_name,
            host_department=host_department,
            pass_code=pass_code,
            request_code=request_code,
            purpose=purpose,

            created_at=checkin.created_at,
            updated_at=checkin.updated_at
        )

    @classmethod
    def to_checkin_response_list(cls, checkins: List[CheckIn]) -> List[CheckInResponse]:
        """
        Convert list of CheckIn entities to DTOs.
        """
        return [cls.to_checkin_response(c) for c in checkins]

    @classmethod
    def to_scan_log_response(cls, log: ScanLog) -> ScanLogResponse:
        """
        Convert ScanLog entity to DTO.
        """
        return ScanLogResponse(
            id=log.id,
            tenant_id=log.tenant_id,
            pass_id=log.pass_id,
            visitor_id=log.visitor_id,
            gate_device_id=log.gate_device_id,
            scanner_name=log.scanner_name,
            scanner_ip=log.scanner_ip,
            qr_token=log.qr_token,
            scan_result=log.scan_result,
            reason=log.reason,

            ip_address=log.ip_address,
            created_at=log.created_at
        )

    @classmethod
    def to_gate_event_response(cls, event: GateEventHistory) -> GateEventResponse:
        """
        Convert GateEventHistory entity to DTO.
        """
        performed_by_name = None
        if event.performed_by_user:
            performed_by_name = f"{event.performed_by_user.first_name} {event.performed_by_user.last_name}".strip()

        return GateEventResponse(
            id=event.id,
            tenant_id=event.tenant_id,
            checkin_id=event.checkin_id,
            pass_id=event.pass_id,
            event_type=event.event_type,
            performed_by=event.performed_by,
            performed_by_name=performed_by_name,
            gate_device_id=event.gate_device_id,
            details=event.details,
            created_at=event.created_at
        )

    @classmethod
    def to_gate_event_response_list(cls, events: List[GateEventHistory]) -> List[GateEventResponse]:
        """
        Convert list of GateEventHistory entities to DTOs.
        """
        return [cls.to_gate_event_response(e) for e in events]
