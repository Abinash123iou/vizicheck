from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.models.visitor import Visitor, VisitorStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.qr_token import QRToken
from app.models.checkin import CheckIn, CheckInStatus, GateVerificationStatus
from app.core.exceptions import ValidationException, AuthorizationException, NotFoundException, ConflictException
from app.core.permissions import SystemRoles
from app.services.qr_service import QRService
from app.repositories.checkin_repository import CheckInRepository
from app.utils.logger import get_logger

logger = get_logger("checkin_validator")


class CheckInValidator:
    """
    Validator enforcing the strict 12-Stage Enterprise QR & Security Gate Pipeline:
    1. QR Payload Parsing
    2. JWT Signature Verification
    3. JWT Expiry Check
    4. QR Version Match
    5. Pass Existence
    6. Pass Status Validation
    7. Pass Validity Window
    8. Tenant Boundary Enforcement
    9. Visit Request Status
    10. Visitor Account Status
    11. Duplicate Scan / Check-In Prevention
    12. Manual Override Validation
    """

    @classmethod
    def validate_tenant_boundary(
        cls, 
        current_user: User, 
        request_tenant_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> int:
        """
        Enforce tenant isolation boundaries based on user role.
        """
        if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN:
            if request_tenant_id:
                target_tenant_id = request_tenant_id
            elif current_user.tenant_id:
                target_tenant_id = current_user.tenant_id
            elif db is not None:
                active_tenant = db.query(Tenant).filter(Tenant.status == TenantStatus.ACTIVE).first()
                if not active_tenant:
                    active_tenant = db.query(Tenant).first()
                if active_tenant:
                    target_tenant_id = active_tenant.id
                else:
                    raise NotFoundException("No tenant organization exists in the database. Please create a tenant organization first (via POST /api/v1/tenants).")
            else:
                target_tenant_id = 1
        else:
            if not current_user.tenant_id:
                raise AuthorizationException("User is not assigned to any tenant organization")
            if request_tenant_id and request_tenant_id != current_user.tenant_id:
                raise AuthorizationException("Access denied. Cannot operate across external tenant boundaries")
            target_tenant_id = current_user.tenant_id

        if db is not None and 'target_tenant_id' in locals():
            tenant = db.query(Tenant).filter(Tenant.id == target_tenant_id).first()
            if not tenant:
                raise NotFoundException(f"Tenant ID {target_tenant_id} not found. Please provide a valid tenant_id query parameter.")
            if tenant.status != TenantStatus.ACTIVE:
                raise ValidationException(f"Tenant organization '{tenant.name}' is inactive")


        return target_tenant_id

    @classmethod
    def parse_qr_raw_string(cls, raw_qr_token: str) -> str:
        """
        Extract clean JWT string if payload is prefixed with VIZICHECK:PASS:... format.
        """
        if not raw_qr_token or not raw_qr_token.strip():
            raise ValidationException("QR token input is empty")

        token_str = raw_qr_token.strip()

        # Check prefix format VIZICHECK:PASS:<uuid>:V<version>:<jwt_token>
        if token_str.startswith("VIZICHECK:PASS:"):
            parts = token_str.split(":")
            if len(parts) >= 5:
                return parts[-1]  # The actual JWT token string is the final segment
            else:
                raise ValidationException("Invalid ViziCheck raw QR format")

        return token_str

    @classmethod
    @classmethod
    def validate_qr_scan_for_checkin(
        cls, 
        db: Session, 
        current_user: User,
        raw_qr_token: str, 
        client_ip: Optional[str] = None,
        gate_device_id: Optional[str] = None
    ) -> Tuple[VisitorPass, QRToken, VisitRequest, Visitor, Dict[str, Any], int]:
        """
        Full 11-stage enterprise check-in validation pipeline.
        Returns validated (visitor_pass, qr_token_model, visit_request, visitor, claims, target_tenant_id).
        """
        # Stage 1: Parse QR Token
        try:
            jwt_token_str = cls.parse_qr_raw_string(raw_qr_token)
        except ValidationException as ve:
            CheckInRepository.log_scan(
                db=db, tenant_id=current_user.tenant_id or 1, scan_result=GateVerificationStatus.UNKNOWN_QR,
                reason=str(ve), gate_device_id=gate_device_id, qr_token=raw_qr_token, ip_address=client_ip
            )
            raise

        # Stage 2 & 3: JWT Signature & Expiration Verification
        try:
            claims = QRService.decode_and_verify_jwt(jwt_token_str)
        except ValidationException as ve:
            scan_res = GateVerificationStatus.EXPIRED if "expired" in str(ve).lower() else GateVerificationStatus.INVALID_SIGNATURE
            CheckInRepository.log_scan(
                db=db, tenant_id=current_user.tenant_id or 1, scan_result=scan_res,
                reason=str(ve), gate_device_id=gate_device_id, qr_token=jwt_token_str, ip_address=client_ip
            )
            raise

        pass_uuid = claims.get("sub")
        token_version = claims.get("version", 1)
        token_tenant_id = claims.get("tenant_id")

        # Stage 4: Tenant Boundary Enforcement
        try:
            target_tenant_id = cls.validate_tenant_boundary(
                current_user=current_user,
                request_tenant_id=token_tenant_id,
                db=db
            )
        except (AuthorizationException, NotFoundException) as ae:
            CheckInRepository.log_scan(
                db=db, tenant_id=current_user.tenant_id or token_tenant_id or 1, scan_result=GateVerificationStatus.WRONG_TENANT,
                reason=str(ae), gate_device_id=gate_device_id, qr_token=jwt_token_str, ip_address=client_ip
            )
            raise

        # Stage 5: Pass Existence
        visitor_pass = db.query(VisitorPass).filter(
            VisitorPass.uuid == pass_uuid,
            VisitorPass.is_deleted == False
        ).first()

        if not visitor_pass:
            msg = f"Visitor Pass with UUID '{pass_uuid}' not found in database"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.UNKNOWN_QR,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, ip_address=client_ip
            )
            raise NotFoundException(msg)

        # Stage 6: QR Version Match
        qr_token_record = db.query(QRToken).filter(
            QRToken.pass_id == visitor_pass.id,
            QRToken.token == jwt_token_str,
            QRToken.is_active == True
        ).first()

        if not qr_token_record or token_version != visitor_pass.latest_qr_version:
            msg = f"QR Token version mismatch or inactive (Token Ver: {token_version}, Pass Ver: {visitor_pass.latest_qr_version})"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.FAILED,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        # Stage 7: Duplicate Scan / Active Check-in Check
        active_checkin = CheckInRepository.get_active_checkin_by_pass_id(
            db=db, pass_id=visitor_pass.id, tenant_id=target_tenant_id
        )
        if active_checkin:
            msg = f"Duplicate Scan: Visitor is ALREADY checked in at {active_checkin.checkin_time}"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.ALREADY_CHECKED_IN,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, visitor_id=visitor_pass.visitor_id, ip_address=client_ip
            )
            raise ConflictException(msg)

        # Stage 8: Pass Status Validation
        if visitor_pass.status == PassStatus.REVOKED:
            msg = f"Visitor Pass '{visitor_pass.pass_code}' is REVOKED"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.REVOKED,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        if visitor_pass.status in [PassStatus.COMPLETED, PassStatus.EXPIRED]:
            msg = f"Visitor Pass '{visitor_pass.pass_code}' status is '{visitor_pass.status.value}' and cannot be used"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.PASS_EXPIRED,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        # Stage 9: Pass Validity Time Window
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if visitor_pass.valid_until and visitor_pass.valid_until < now:
            msg = f"Visitor Pass '{visitor_pass.pass_code}' expired at {visitor_pass.valid_until}"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.PASS_EXPIRED,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        # Stage 10: Visit Request Validation
        visit_request = db.query(VisitRequest).filter(VisitRequest.id == visitor_pass.visit_request_id).first()
        if not visit_request or visit_request.is_deleted:
            msg = "Associated Visit Request not found"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.REQUEST_INVALID,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise NotFoundException(msg)

        if visit_request.status != VisitRequestStatus.APPROVED:
            msg = f"Visit Request '{visit_request.request_code}' status is '{visit_request.status.value}', expected 'APPROVED'"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.REQUEST_INVALID,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        # Stage 11: Visitor Account Status
        visitor = db.query(Visitor).filter(Visitor.id == visitor_pass.visitor_id).first()
        if not visitor or visitor.is_deleted:
            msg = "Associated Visitor profile not found"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.VISITOR_INACTIVE,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise NotFoundException(msg)

        if visitor.status == VisitorStatus.BLACKLISTED:
            msg = f"Visitor '{visitor.first_name} {visitor.last_name}' is BLACKLISTED"
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.VISITOR_INACTIVE,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, visitor_id=visitor.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        return visitor_pass, qr_token_record, visit_request, visitor, claims, target_tenant_id

    @classmethod
    def validate_qr_scan_for_checkout(
        cls, 
        db: Session, 
        current_user: User,
        raw_qr_token: str, 
        client_ip: Optional[str] = None,
        gate_device_id: Optional[str] = None
    ) -> Tuple[CheckIn, VisitorPass, QRToken, Dict[str, Any], int]:
        """
        Validation pipeline for exit check-out scanning.
        Must find an active CheckIn record.
        """
        jwt_token_str = cls.parse_qr_raw_string(raw_qr_token)
        claims = QRService.decode_and_verify_jwt(jwt_token_str)
        pass_uuid = claims.get("sub")
        token_tenant_id = claims.get("tenant_id")

        target_tenant_id = cls.validate_tenant_boundary(
            current_user=current_user,
            request_tenant_id=token_tenant_id,
            db=db
        )

        visitor_pass = db.query(VisitorPass).filter(
            VisitorPass.uuid == pass_uuid,
            VisitorPass.tenant_id == target_tenant_id,
            VisitorPass.is_deleted == False
        ).first()

        if not visitor_pass:
            raise NotFoundException(f"Visitor Pass with UUID '{pass_uuid}' not found")

        active_checkin = CheckInRepository.get_active_checkin_by_pass_id(
            db=db, pass_id=visitor_pass.id, tenant_id=target_tenant_id
        )

        if not active_checkin:
            msg = f"No active check-in record found for Pass '{visitor_pass.pass_code}'. Visitor is NOT currently checked in."
            CheckInRepository.log_scan(
                db=db, tenant_id=target_tenant_id, scan_result=GateVerificationStatus.NOT_CHECKED_IN,
                reason=msg, gate_device_id=gate_device_id, qr_token=jwt_token_str, pass_id=visitor_pass.id, ip_address=client_ip
            )
            raise ValidationException(msg)

        qr_token_record = db.query(QRToken).filter(
            QRToken.pass_id == visitor_pass.id,
            QRToken.token == jwt_token_str
        ).first()

        return active_checkin, visitor_pass, qr_token_record, claims, target_tenant_id


    @classmethod
    @classmethod
    def validate_manual_checkin(
        cls, 
        db: Session, 
        current_user: User,
        pass_code: Optional[str], 
        pass_id: Optional[int], 
        request_code: Optional[str], 
        reason: str
    ) -> Tuple[VisitorPass, VisitRequest, Visitor, int]:
        """
        Validate security manual check-in override requirements.
        """
        if not reason or not reason.strip():
            raise ValidationException("Justification reason is required for manual check-in override")

        visitor_pass = None
        if pass_id:
            visitor_pass = db.query(VisitorPass).filter(VisitorPass.id == pass_id).first()
        elif pass_code:
            visitor_pass = db.query(VisitorPass).filter(VisitorPass.pass_code == pass_code).first()
        elif request_code:
            visit_req = db.query(VisitRequest).filter(VisitRequest.request_code == request_code).first()
            if visit_req:
                visitor_pass = db.query(VisitorPass).filter(VisitorPass.visit_request_id == visit_req.id).first()

        if not visitor_pass or visitor_pass.is_deleted:
            raise NotFoundException("Visitor Pass not found for provided identification code")

        # Enforce tenant isolation boundary
        target_tenant_id = cls.validate_tenant_boundary(
            current_user=current_user, 
            request_tenant_id=visitor_pass.tenant_id, 
            db=db
        )

        active_checkin = CheckInRepository.get_active_checkin_by_pass_id(db=db, pass_id=visitor_pass.id, tenant_id=target_tenant_id)
        if active_checkin:
            raise ConflictException(f"Visitor is ALREADY checked in (Checkin ID: {active_checkin.id})")

        visit_request = db.query(VisitRequest).filter(VisitRequest.id == visitor_pass.visit_request_id).first()
        visitor = db.query(Visitor).filter(Visitor.id == visitor_pass.visitor_id).first()

        if not visit_request or not visitor:
            raise NotFoundException("Associated Visit Request or Visitor profile missing")

        return visitor_pass, visit_request, visitor, target_tenant_id

    @classmethod
    def validate_manual_checkout(
        cls, 
        db: Session, 
        current_user: User,
        checkin_id: Optional[int], 
        pass_code: Optional[str], 
        reason: str
    ) -> Tuple[CheckIn, VisitorPass, int]:
        """
        Validate security manual check-out override.
        """
        if not reason or not reason.strip():
            raise ValidationException("Justification reason is required for manual check-out override")

        checkin = None
        if checkin_id:
            checkin = db.query(CheckIn).filter(CheckIn.id == checkin_id).first()
        elif pass_code:
            vpass = db.query(VisitorPass).filter(VisitorPass.pass_code == pass_code).first()
            if vpass:
                checkin = CheckInRepository.get_active_checkin_by_pass_id(db=db, pass_id=vpass.id, tenant_id=vpass.tenant_id)

        if not checkin or checkin.status != CheckInStatus.CHECKED_IN:
            raise NotFoundException("No active check-in record found to check out")

        target_tenant_id = cls.validate_tenant_boundary(
            current_user=current_user, 
            request_tenant_id=checkin.tenant_id, 
            db=db
        )

        visitor_pass = db.query(VisitorPass).filter(VisitorPass.id == checkin.pass_id).first()

        return checkin, visitor_pass, target_tenant_id


    @classmethod
    def validate_undo_checkin(cls, db: Session, checkin_id: int, reason: str, target_tenant_id: int) -> CheckIn:
        """
        Validate admin undo check-in requirements.
        """
        if not reason or not reason.strip():
            raise ValidationException("Reason is required to undo a check-in record")

        checkin = CheckInRepository.get_by_id(db=db, checkin_id=checkin_id, tenant_id=target_tenant_id)
        if not checkin:
            raise NotFoundException(f"Check-in record ID {checkin_id} not found")

        if checkin.is_undone:
            raise ValidationException("This check-in record has already been undone")

        return checkin
