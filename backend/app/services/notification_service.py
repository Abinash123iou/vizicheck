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
