from typing import Optional, List
from app.models.visitor_pass import VisitorPass, PassStatusHistory
from app.models.qr_token import QRToken
from app.schemas.pass_schema import PassResponse, PassStatusHistoryResponse, QRResponse


class PassMapper:
    """
    Data mapper for converting VisitorPass, PassStatusHistory, and QRToken entities into DTO responses.
    """

    @classmethod
    def to_history_response(cls, history: PassStatusHistory) -> PassStatusHistoryResponse:
        """
        Convert PassStatusHistory entity to DTO.
        """
        return PassStatusHistoryResponse(
            id=history.id,
            pass_id=history.pass_id,
            old_status=history.old_status,
            new_status=history.new_status,
            changed_by=history.changed_by,
            changed_at=history.changed_at,
            remarks=history.remarks
        )

    @classmethod
    def to_qr_response(cls, qr_token: QRToken, decoded_claims: Optional[dict] = None) -> QRResponse:
        """
        Convert QRToken entity and decoded JWT claims to QRResponse DTO.
        """
        claims = decoded_claims or {}
        return QRResponse(
            id=qr_token.id,
            pass_id=qr_token.pass_id,
            tenant_id=qr_token.tenant_id,
            token=qr_token.token,
            version=qr_token.version,
            is_active=qr_token.is_active,
            expires_at=qr_token.expires_at,
            created_at=qr_token.created_at,
            sub=claims.get("sub", ""),
            visitor_id=claims.get("visitor_id", 0),
            visit_request_id=claims.get("visit_request_id", 0),
            token_type=claims.get("token_type", "VISITOR_PASS"),
            iss=claims.get("iss", "ViziCheck"),
            aud=claims.get("aud", "GateScanner"),
            iat=claims.get("iat", 0),
            exp=claims.get("exp", 0),
            qr_code_base64=claims.get("qr_code_base64", None)
        )

    @classmethod
    def to_pass_response(
        cls, 
        visitor_pass: VisitorPass, 
        active_qr: Optional[QRToken] = None, 
        decoded_claims: Optional[dict] = None
    ) -> PassResponse:
        """
        Convert VisitorPass domain entity to PassResponse DTO.
        """
        # Resolve visitor details
        visitor_name = None
        visitor_phone = None
        visitor_email = None
        visitor_company = None
        if visitor_pass.visitor:
            visitor_name = f"{visitor_pass.visitor.first_name} {visitor_pass.visitor.last_name}".strip()
            visitor_phone = visitor_pass.visitor.phone
            visitor_email = visitor_pass.visitor.email
            visitor_company = visitor_pass.visitor.company

        # Resolve host details
        host_name = None
        host_email = None
        if visitor_pass.host:
            host_name = f"{visitor_pass.host.first_name} {visitor_pass.host.last_name}".strip()
            host_email = visitor_pass.host.email

        # Resolve request code
        request_code = visitor_pass.visit_request.request_code if visitor_pass.visit_request else None

        # Map status history list
        history_dtos = [cls.to_history_response(h) for h in (visitor_pass.status_history or [])]
        history_dtos.sort(key=lambda x: x.changed_at)

        # Map active QR response if present
        qr_dto = cls.to_qr_response(active_qr, decoded_claims) if active_qr else None

        return PassResponse(
            id=visitor_pass.id,
            uuid=visitor_pass.uuid,
            tenant_id=visitor_pass.tenant_id,
            visit_request_id=visitor_pass.visit_request_id,
            request_code=request_code,
            visitor_id=visitor_pass.visitor_id,
            visitor_name=visitor_name,
            visitor_phone=visitor_phone,
            visitor_email=visitor_email,
            visitor_company=visitor_company,
            host_id=visitor_pass.host_id,
            host_name=host_name,
            host_email=host_email,
            pass_code=visitor_pass.pass_code,
            status=visitor_pass.status,
            latest_qr_version=visitor_pass.latest_qr_version,
            valid_from=visitor_pass.valid_from,
            valid_until=visitor_pass.valid_until,
            used_at=visitor_pass.used_at,
            completed_at=visitor_pass.completed_at,
            notes=visitor_pass.notes,
            revoked_by=visitor_pass.revoked_by,
            revoked_at=visitor_pass.revoked_at,
            revocation_reason=visitor_pass.revocation_reason,
            created_by=visitor_pass.created_by,
            created_at=visitor_pass.created_at,
            updated_at=visitor_pass.updated_at,
            is_deleted=visitor_pass.is_deleted,
            status_history=history_dtos,
            active_qr=qr_dto
        )
