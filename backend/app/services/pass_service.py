import io
import csv
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.qr_token import QRToken
from app.constants.audit_actions import AuditActions
from app.core.exceptions import NotFoundException, ValidationException, AuthorizationException, ConflictException
from app.core.permissions import SystemRoles
from app.repositories.pass_repository import PassRepository
from app.repositories.qr_repository import QRRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.pass_validator import PassValidator
from app.validators.qr_validator import QRValidator
from app.mappers.pass_mapper import PassMapper
from app.services.qr_service import QRService
from app.services.notification_service import NotificationService
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.pass_schema import (
    GeneratePassRequest,
    UpdatePassRequest,
    RevokePassRequest,
    PassPaginationRequest,
    PassResponse,
    QRResponse,
    PassStatisticsResponse
)


class PassService:
    """
    Business logic orchestration service for Visitor Pass & QR Token lifecycle management.
    """

    MODULE_NAME = "VISITOR_PASS_MANAGEMENT"

    @classmethod
    def generate_pass(
        cls,
        db: Session,
        current_user: User,
        visit_request_id: int,
        request_data: Optional[GeneratePassRequest] = None,
        ip_address: Optional[str] = None
    ) -> PassResponse:
        """
        Generate a new secure visitor pass for an approved visit request.
        """
        request_tenant = request_data.tenant_id if request_data else None
        target_tenant_id = PassValidator.validate_tenant_boundary(current_user, request_tenant, db=db)

        # Validate visit request & duplicate pass check
        visit_request = PassValidator.validate_visit_request_for_pass(db, visit_request_id, target_tenant_id)
        PassValidator.validate_no_duplicate_pass(db, visit_request_id, target_tenant_id)

        # Validity times
        vf = request_data.valid_from if (request_data and request_data.valid_from) else visit_request.scheduled_start_time
        vu = request_data.valid_until if (request_data and request_data.valid_until) else visit_request.scheduled_end_time
        
        vf_naive = vf.replace(tzinfo=None) if vf.tzinfo else vf
        vu_naive = vu.replace(tzinfo=None) if vu.tzinfo else vu
        PassValidator.validate_pass_validity_times(vf_naive, vu_naive)

        pass_code = PassRepository.generate_pass_code(db, target_tenant_id)
        notes = request_data.notes.strip() if (request_data and request_data.notes) else visit_request.notes

        # Create VisitorPass entity
        pass_entity = VisitorPass(
            tenant_id=target_tenant_id,
            visit_request_id=visit_request.id,
            visitor_id=visit_request.visitor_id,
            host_id=visit_request.host_id,
            pass_code=pass_code,
            status=PassStatus.ACTIVE,
            latest_qr_version=1,
            valid_from=vf_naive,
            valid_until=vu_naive,
            notes=notes,
            created_by=current_user.id
        )

        created_pass = PassRepository.create(db, pass_entity)

        # Generate cryptographic JWT QR token
        jwt_token, claims, qr_data_uri = QRService.generate_jwt_qr_token(
            visitor_pass=created_pass,
            version=1,
            expires_at=vu_naive
        )

        qr_entity = QRToken(
            tenant_id=target_tenant_id,
            pass_id=created_pass.id,
            token=jwt_token,
            version=1,
            is_active=True,
            expires_at=vu_naive
        )
        active_qr = QRRepository.create(db, qr_entity)

        # Record Pass Status History
        PassRepository.record_status_change(
            db=db,
            pass_id=created_pass.id,
            old_status=None,
            new_status=PassStatus.ACTIVE,
            changed_by=current_user.id,
            remarks=f"Pass generated for Visit Request {visit_request.request_code}"
        )

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASS_GENERATED,
            module=cls.MODULE_NAME,
            entity_id=created_pass.id,
            new_value={
                "pass_code": created_pass.pass_code,
                "uuid": created_pass.uuid,
                "visit_request_id": created_pass.visit_request_id,
                "visitor_id": created_pass.visitor_id,
                "status": created_pass.status.value,
                "qr_version": 1
            },
            ip_address=ip_address
        )

        # Trigger notification hook
        NotificationService.notify_pass_generated(created_pass)

        # Include qr_code_base64 in claims payload for response
        claims["qr_code_base64"] = qr_data_uri
        return PassMapper.to_pass_response(created_pass, active_qr=active_qr, decoded_claims=claims)

    @classmethod
    def generate_pass_for_approved_request(cls, visit_request: Any, db: Optional[Session] = None) -> Optional[VisitorPass]:
        """
        Automatically generate a visitor pass when a visit request is approved.
        """
        from sqlalchemy.orm import object_session
        session = db or object_session(visit_request)
        if not session:
            return None

        existing_pass = PassRepository.find_by_visit_request_id(session, visit_request.id, visit_request.tenant_id)
        if existing_pass:
            return existing_pass

        pass_code = PassRepository.generate_pass_code(session, visit_request.tenant_id)
        vf = visit_request.scheduled_start_time
        vu = visit_request.scheduled_end_time
        vf_naive = vf.replace(tzinfo=None) if vf and vf.tzinfo else vf
        vu_naive = vu.replace(tzinfo=None) if vu and vu.tzinfo else vu

        pass_entity = VisitorPass(
            tenant_id=visit_request.tenant_id,
            visit_request_id=visit_request.id,
            visitor_id=visit_request.visitor_id,
            host_id=visit_request.host_id,
            pass_code=pass_code,
            status=PassStatus.ACTIVE,
            latest_qr_version=1,
            valid_from=vf_naive,
            valid_until=vu_naive,
            notes=visit_request.notes,
            created_by=visit_request.approved_by
        )

        created_pass = PassRepository.create(session, pass_entity)

        jwt_token, claims, qr_data_uri = QRService.generate_jwt_qr_token(
            visitor_pass=created_pass,
            version=1,
            expires_at=vu_naive
        )

        qr_entity = QRToken(
            tenant_id=visit_request.tenant_id,
            pass_id=created_pass.id,
            token=jwt_token,
            version=1,
            is_active=True,
            expires_at=vu_naive
        )
        active_qr = QRRepository.create(session, qr_entity)

        PassRepository.record_status_change(
            db=session,
            pass_id=created_pass.id,
            old_status=None,
            new_status=PassStatus.ACTIVE,
            changed_by=visit_request.approved_by,
            remarks=f"Automatic pass generated upon approval of Visit Request {visit_request.request_code}"
        )

        NotificationService.notify_pass_generated(created_pass)
        return created_pass

    @classmethod
    def list_passes(
        cls, 
        db: Session, 
        current_user: User, 
        params: PassPaginationRequest
    ) -> EnhancedPaginationResponse[PassResponse]:
        """
        Retrieve paginated, filtered, and searched visitor passes.
        """
        target_tenant_id = PassValidator.validate_tenant_boundary(current_user, params.tenant_id, db=db)
        params.tenant_id = target_tenant_id

        passes, total_count = PassRepository.find_all(db, params)

        items = []
        for p in passes:
            active_qr = QRRepository.find_active_by_pass_id(db, p.id)
            claims = None
            if active_qr:
                try:
                    claims = QRService.decode_and_verify_jwt(active_qr.token)
                except Exception:
                    pass
            items.append(PassMapper.to_pass_response(p, active_qr=active_qr, decoded_claims=claims))

        total_pages = (total_count + params.page_size - 1) // params.page_size if total_count > 0 else 1

        return EnhancedPaginationResponse[PassResponse](
            items=items,
            total=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=(params.page < total_pages),
            has_prev=(params.page > 1)
        )

    @classmethod
    def get_pass_by_id(cls, db: Session, current_user: User, pass_id: int) -> PassResponse:
        """
        Retrieve details of a single visitor pass by ID.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        active_qr = QRRepository.find_active_by_pass_id(db, entity.id)
        claims = None
        if active_qr:
            try:
                claims = QRService.decode_and_verify_jwt(active_qr.token)
            except Exception:
                pass

        return PassMapper.to_pass_response(entity, active_qr=active_qr, decoded_claims=claims)

    @classmethod
    def get_pass_by_code(cls, db: Session, current_user: User, pass_code: str) -> PassResponse:
        """
        Retrieve details of a visitor pass by pass code.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_pass_code(db, pass_code=pass_code, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with code '{pass_code}' not found")

        active_qr = QRRepository.find_active_by_pass_id(db, entity.id)
        claims = None
        if active_qr:
            try:
                claims = QRService.decode_and_verify_jwt(active_qr.token)
            except Exception:
                pass

        return PassMapper.to_pass_response(entity, active_qr=active_qr, decoded_claims=claims)

    @classmethod
    def update_pass(
        cls,
        db: Session,
        current_user: User,
        pass_id: int,
        request: UpdatePassRequest,
        ip_address: Optional[str] = None
    ) -> PassResponse:
        """
        Update visitor pass valid window or notes.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        PassValidator.validate_state_transition(entity, target_action="UPDATE")

        target_vf = request.valid_from or entity.valid_from
        target_vu = request.valid_until or entity.valid_until
        PassValidator.validate_pass_validity_times(target_vf, target_vu)

        if request.valid_from is not None:
            entity.valid_from = request.valid_from.replace(tzinfo=None) if request.valid_from.tzinfo else request.valid_from
        if request.valid_until is not None:
            entity.valid_until = request.valid_until.replace(tzinfo=None) if request.valid_until.tzinfo else request.valid_until
        if request.notes is not None:
            entity.notes = request.notes.strip()

        updated_entity = PassRepository.update(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASS_UPDATED,
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            new_value={
                "pass_code": updated_entity.pass_code,
                "valid_from": str(updated_entity.valid_from),
                "valid_until": str(updated_entity.valid_until)
            },
            ip_address=ip_address
        )

        active_qr = QRRepository.find_active_by_pass_id(db, updated_entity.id)
        return PassMapper.to_pass_response(updated_entity, active_qr=active_qr)

    @classmethod
    def delete_pass(
        cls,
        db: Session,
        current_user: User,
        pass_id: int,
        ip_address: Optional[str] = None
    ) -> PassResponse:
        """
        Soft delete a visitor pass.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        deleted_entity = PassRepository.delete(db, entity, deleted_by=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASS_DELETED,
            module=cls.MODULE_NAME,
            entity_id=deleted_entity.id,
            new_value={"pass_code": deleted_entity.pass_code},
            ip_address=ip_address
        )

        return PassMapper.to_pass_response(deleted_entity)

    @classmethod
    def restore_pass(
        cls,
        db: Session,
        current_user: User,
        pass_id: int,
        ip_address: Optional[str] = None
    ) -> PassResponse:
        """
        Restore a soft-deleted visitor pass.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id, include_deleted=True)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        PassValidator.validate_state_transition(entity, target_action="RESTORE")

        restored_entity = PassRepository.restore(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASS_RESTORED,
            module=cls.MODULE_NAME,
            entity_id=restored_entity.id,
            new_value={"pass_code": restored_entity.pass_code},
            ip_address=ip_address
        )

        return PassMapper.to_pass_response(restored_entity)

    @classmethod
    def get_qr_info(cls, db: Session, current_user: User, pass_id: int) -> QRResponse:
        """
        Get active QR token info and decoded claims for a pass.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        active_qr = QRRepository.find_active_by_pass_id(db, entity.id)
        if not active_qr:
            raise NotFoundException(f"No active QR token found for visitor pass '{entity.pass_code}'")

        claims = QRService.decode_and_verify_jwt(active_qr.token)
        return PassMapper.to_qr_response(active_qr, decoded_claims=claims)

    @classmethod
    def regenerate_qr_token(
        cls,
        db: Session,
        current_user: User,
        pass_id: int,
        ip_address: Optional[str] = None
    ) -> QRResponse:
        """
        Regenerate QR token for an active pass. Increments pass.latest_qr_version and invalidates previous tokens.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        PassValidator.validate_state_transition(entity, target_action="REGENERATE_QR")

        # Increment QR version & deactivate previous tokens
        new_version = entity.latest_qr_version + 1
        entity.latest_qr_version = new_version
        PassRepository.update(db, entity)

        QRRepository.deactivate_tokens_for_pass(db, entity.id)

        # Generate new token
        jwt_token, claims, qr_data_uri = QRService.generate_jwt_qr_token(
            visitor_pass=entity,
            version=new_version,
            expires_at=entity.valid_until
        )

        new_qr_entity = QRToken(
            tenant_id=entity.tenant_id,
            pass_id=entity.id,
            token=jwt_token,
            version=new_version,
            is_active=True,
            expires_at=entity.valid_until
        )
        created_qr = QRRepository.create(db, new_qr_entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.QR_REGENERATED,
            module=cls.MODULE_NAME,
            entity_id=entity.id,
            new_value={
                "pass_code": entity.pass_code,
                "new_version": new_version
            },
            ip_address=ip_address
        )

        NotificationService.notify_qr_regenerated(entity, new_version)

        claims["qr_code_base64"] = qr_data_uri
        return PassMapper.to_qr_response(created_qr, decoded_claims=claims)

    @classmethod
    def revoke_pass(
        cls,
        db: Session,
        current_user: User,
        pass_id: int,
        revocation_data: RevokePassRequest,
        ip_address: Optional[str] = None
    ) -> PassResponse:
        """
        Manually revoke an active or pending visitor pass.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = PassRepository.find_by_id(db, pass_id=pass_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visitor pass with ID {pass_id} not found")

        PassValidator.validate_state_transition(entity, target_action="REVOKE", revocation_reason=revocation_data.revocation_reason)

        old_status = entity.status
        entity.status = PassStatus.REVOKED
        entity.revoked_by = current_user.id
        entity.revoked_at = datetime.now()
        entity.revocation_reason = revocation_data.revocation_reason.strip()

        updated_entity = PassRepository.update(db, entity)

        # Deactivate all active QR tokens for revoked pass
        QRRepository.deactivate_tokens_for_pass(db, updated_entity.id)

        # Record Pass Status History
        PassRepository.record_status_change(
            db=db,
            pass_id=updated_entity.id,
            old_status=old_status,
            new_status=PassStatus.REVOKED,
            changed_by=current_user.id,
            remarks=f"Revoked: {updated_entity.revocation_reason}"
        )

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.PASS_REVOKED,
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            new_value={
                "pass_code": updated_entity.pass_code,
                "revocation_reason": updated_entity.revocation_reason
            },
            ip_address=ip_address
        )

        NotificationService.notify_pass_revoked(updated_entity)

        return PassMapper.to_pass_response(updated_entity)

    @classmethod
    def get_statistics(
        cls, 
        db: Session, 
        current_user: User, 
        tenant_id: Optional[int] = None
    ) -> PassStatisticsResponse:
        """
        Retrieve comprehensive dashboard statistics for visitor passes.
        """
        target_tenant_id = PassValidator.validate_tenant_boundary(current_user, tenant_id, db=db)
        stats_dict = PassRepository.get_statistics(db=db, tenant_id=target_tenant_id)
        return PassStatisticsResponse(**stats_dict)

    @classmethod
    def export_passes(
        cls, 
        db: Session, 
        current_user: User, 
        params: PassPaginationRequest
    ) -> str:
        """
        Export visitor passes matching filter criteria into CSV format.
        """
        target_tenant_id = PassValidator.validate_tenant_boundary(current_user, params.tenant_id, db=db)
        params.tenant_id = target_tenant_id
        params.page_size = 10000  # Export all matching records

        passes, _ = PassRepository.find_all(db, params)

        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "Pass Code",
            "UUID",
            "Visitor Name",
            "Visitor Email",
            "Visitor Company",
            "Host Name",
            "Host Email",
            "Status",
            "QR Version",
            "Valid From",
            "Valid Until",
            "Used At",
            "Completed At",
            "Created At"
        ]
        writer.writerow(headers)

        for p in passes:
            v_name = f"{p.visitor.first_name} {p.visitor.last_name}" if p.visitor else ""
            v_email = p.visitor.email if p.visitor else ""
            v_comp = p.visitor.company if p.visitor else ""
            h_name = f"{p.host.first_name} {p.host.last_name}" if p.host else ""
            h_email = p.host.email if p.host else ""

            writer.writerow([
                p.pass_code,
                p.uuid,
                v_name,
                v_email,
                v_comp,
                h_name,
                h_email,
                p.status.value,
                p.latest_qr_version,
                p.valid_from.strftime("%Y-%m-%d %H:%M:%S") if p.valid_from else "",
                p.valid_until.strftime("%Y-%m-%d %H:%M:%S") if p.valid_until else "",
                p.used_at.strftime("%Y-%m-%d %H:%M:%S") if p.used_at else "",
                p.completed_at.strftime("%Y-%m-%d %H:%M:%S") if p.completed_at else "",
                p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else ""
            ])

        return output.getvalue()
