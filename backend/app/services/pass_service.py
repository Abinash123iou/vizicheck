from typing import Dict, Any, Optional
from datetime import datetime
from app.models.visit_request import VisitRequest
from app.utils.logger import get_logger

logger = get_logger("pass_service")

class PassService:
    """
    Pass generation service handling QR code visitor pass creation upon request approval.
    """

    @classmethod
    def generate_pass_for_approved_request(cls, request: VisitRequest) -> Dict[str, Any]:
        """
        Integration hook: Automatically generate a QR pass token for approved visit request.
        """
        pass_code = f"PASS-{request.request_code}"
        logger.info(
            f"[Pass Generation Hook] Generated Visitor Pass '{pass_code}' for Request {request.request_code} "
            f"(Visitor ID={request.visitor_id}, Tenant ID={request.tenant_id})"
        )
        return {
            "pass_code": pass_code,
            "request_code": request.request_code,
            "visitor_id": request.visitor_id,
            "host_id": request.host_id,
            "valid_from": request.scheduled_start_time,
            "valid_until": request.scheduled_end_time,
            "qr_data": f"VIZICHECK:{request.tenant_id}:{request.request_code}:{pass_code}",
            "generated_at": datetime.now()
        }
