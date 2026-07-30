from typing import Optional
from app.models.visit_request import VisitRequest
from app.utils.logger import get_logger

logger = get_logger("notification_service")

class NotificationService:
    """
    Notification trigger service providing hooks for multi-channel dispatches (Email, SMS, Push).
    Acts as event handler for Visit Request lifecycle events.
    """

    @classmethod
    def notify_request_created(cls, request: VisitRequest) -> bool:
        """
        Trigger notification hook when a new visit request is submitted.
        """
        logger.info(
            f"[Notification Hook] Visit Request Created: Code={request.request_code}, "
            f"Visitor ID={request.visitor_id}, Host ID={request.host_id}, Tenant ID={request.tenant_id}"
        )
        # Downstream integration point: Notify Host & Visitor of pending request
        return True

    @classmethod
    def notify_request_approved(cls, request: VisitRequest) -> bool:
        """
        Trigger notification hook when a visit request is approved.
        """
        logger.info(
            f"[Notification Hook] Visit Request Approved: Code={request.request_code}, "
            f"Visitor ID={request.visitor_id}, Host ID={request.host_id}, Approved By={request.approved_by}"
        )
        # Downstream integration point: Send Visitor Pass & QR Code to visitor via Email/SMS
        return True

    @classmethod
    def notify_request_rejected(cls, request: VisitRequest) -> bool:
        """
        Trigger notification hook when a visit request is rejected.
        """
        logger.info(
            f"[Notification Hook] Visit Request Rejected: Code={request.request_code}, "
            f"Visitor ID={request.visitor_id}, Reason='{request.rejection_reason}'"
        )
        # Downstream integration point: Notify Visitor of rejection with reason
        return True

    @classmethod
    def notify_request_cancelled(cls, request: VisitRequest) -> bool:
        """
        Trigger notification hook when a visit request is cancelled.
        """
        logger.info(
            f"[Notification Hook] Visit Request Cancelled: Code={request.request_code}, "
            f"Reason='{request.cancellation_reason}'"
        )
        return True

    @classmethod
    def notify_host(cls, host_id: int, message: str) -> bool:
        """
        Direct notification dispatch to employee host.
        """
        logger.info(f"[Notification Hook] Direct Host Notification (Host ID={host_id}): {message}")
        return True

    @classmethod
    def notify_security(cls, tenant_id: int, message: str) -> bool:
        """
        Direct notification dispatch to security officers.
        """
        logger.info(f"[Notification Hook] Direct Security Notification (Tenant ID={tenant_id}): {message}")
        return True

    # --- Visitor Pass & QR Event Notification Hooks ---

    @classmethod
    def notify_pass_generated(cls, visitor_pass) -> bool:
        """
        Trigger notification hook when a Visitor Pass is generated.
        """
        logger.info(
            f"[Notification Hook] PASS_GENERATED: Code={visitor_pass.pass_code}, "
            f"Visitor ID={visitor_pass.visitor_id}, Valid Until={visitor_pass.valid_until}"
        )
        return True

    @classmethod
    def notify_pass_revoked(cls, visitor_pass) -> bool:
        """
        Trigger notification hook when a Visitor Pass is revoked.
        """
        logger.info(
            f"[Notification Hook] PASS_REVOKED: Code={visitor_pass.pass_code}, "
            f"Reason='{visitor_pass.revocation_reason}'"
        )
        return True

    @classmethod
    def notify_pass_expired(cls, visitor_pass) -> bool:
        """
        Trigger notification hook when a Visitor Pass expires automatically.
        """
        logger.info(
            f"[Notification Hook] PASS_EXPIRED: Code={visitor_pass.pass_code}, "
            f"Visitor ID={visitor_pass.visitor_id}"
        )
        return True

    @classmethod
    def notify_qr_regenerated(cls, visitor_pass, new_version: int) -> bool:
        """
        Trigger notification hook when a QR code is regenerated.
        """
        logger.info(
            f"[Notification Hook] QR_REGENERATED: Code={visitor_pass.pass_code}, "
            f"New Version={new_version}"
        )
        return True

    # --- Gate Security & Check-In/Out Notification Hooks ---

    @classmethod
    def notify_host_checkin(cls, checkin, visitor_pass, host) -> bool:
        """
        Notify host employee when their visitor checks in at the gate.
        """
        host_id = host.id if host else checkin.host_id
        logger.info(
            f"[Notification Hook] HOST_CHECKIN_ALERT: Host ID={host_id}, "
            f"Pass={visitor_pass.pass_code if visitor_pass else checkin.pass_id}, "
            f"Gate={checkin.gate_name}, CheckInTime={checkin.checkin_time}"
        )
        return True

    @classmethod
    def notify_host_checkout(cls, checkin, visitor_pass, host) -> bool:
        """
        Notify host employee when their visitor checks out.
        """
        host_id = host.id if host else checkin.host_id
        logger.info(
            f"[Notification Hook] HOST_CHECKOUT_ALERT: Host ID={host_id}, "
            f"Pass={visitor_pass.pass_code if visitor_pass else checkin.pass_id}, "
            f"DurationMinutes={checkin.visit_duration_minutes}"
        )
        return True

    @classmethod
    def notify_security_alert(cls, tenant_id: int, alert_type: str, message: str, details: Optional[str] = None) -> bool:
        """
        Dispatch security alert to gate officers and tenant administrators.
        """
        logger.warning(
            f"[Notification Hook] SECURITY_ALERT (Tenant ID={tenant_id}): [{alert_type}] {message} | Details: {details}"
        )
        return True

    @classmethod
    def notify_overstay(cls, checkin, visitor_pass, host) -> bool:
        """
        Notify host and security when a visitor has exceeded their scheduled visit duration.
        """
        logger.warning(
            f"[Notification Hook] VISITOR_OVERSTAY_ALERT: CheckIn ID={checkin.id}, "
            f"Visitor ID={checkin.visitor_id}, Host ID={checkin.host_id}"
        )
        return True

    @classmethod
    def notify_manual_override(cls, checkin, performed_by, reason: str) -> bool:
        """
        Notify security administrator when a manual check-in/out override occurs.
        """
        logger.info(
            f"[Notification Hook] MANUAL_OVERRIDE_ALERT: CheckIn ID={checkin.id}, "
            f"PerformedBy={performed_by.id if performed_by else 'System'}, Reason='{reason}'"
        )
        return True

