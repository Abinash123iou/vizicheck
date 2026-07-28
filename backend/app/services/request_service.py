from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.constants.audit_actions import AuditActions
from app.core.exceptions import NotFoundException, ValidationException, AuthorizationException
from app.core.permissions import SystemRoles
from app.repositories.request_repository import RequestRepository
from app.repositories.audit_repository import AuditRepository
from app.validators.request_validator import RequestValidator
from app.mappers.request_mapper import RequestMapper
from app.services.notification_service import NotificationService
from app.services.pass_service import PassService
from app.services.export_service import ExportService
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.request import (
    CreateVisitRequest,
    UpdateVisitRequest,
    ApprovalRequest,
    RejectRequest,
    CancelRequest,
    VisitRequestPaginationRequest,
    VisitRequestResponse,
    VisitRequestStatisticsResponse,
    VisitRequestCalendarResponse
)

class RequestService:
    """
    Business logic orchestration layer for Visit Request Management.
    Handles CRUD operations, tenant boundary security, validation, state transitions,
    pass generation hooks, notification hooks, CSV exports, and audit logging.
    """

    MODULE_NAME = "VISIT_REQUEST_MANAGEMENT"

    @classmethod
    def create_request(
        cls,
        db: Session,
        current_user: User,
        request: CreateVisitRequest,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Submit a new visit request. Validates tenant, host, visitor eligibility, and overlapping bookings.
        """
        target_tenant_id = RequestValidator.validate_tenant_boundary(current_user, request.tenant_id, db=db)
        
        # Validate visitor and host eligibility
        visitor = RequestValidator.validate_visitor_eligibility(db, request.visitor_id, target_tenant_id)
        host = RequestValidator.validate_host_eligibility(db, request.host_id, target_tenant_id)

        start_time = request.scheduled_start_time.replace(tzinfo=None) if request.scheduled_start_time.tzinfo else request.scheduled_start_time
        end_time = request.scheduled_end_time.replace(tzinfo=None) if request.scheduled_end_time.tzinfo else request.scheduled_end_time

        # Validate scheduled time sanity & overlapping bookings
        RequestValidator.validate_scheduled_times(start_time, end_time)
        RequestValidator.validate_no_overlapping_booking(
            db=db,
            tenant_id=target_tenant_id,
            visitor_id=request.visitor_id,
            start_time=start_time,
            end_time=end_time
        )

        request_code = RequestRepository.generate_request_code(db, target_tenant_id)

        entity = VisitRequest(
            tenant_id=target_tenant_id,
            request_code=request_code,
            visitor_id=request.visitor_id,
            host_id=request.host_id,
            purpose=request.purpose.strip(),
            department=request.department.strip() if request.department else None,
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            additional_visitors_count=request.additional_visitors_count,
            notes=request.notes.strip() if request.notes else None,
            status=VisitRequestStatus.PENDING,
            created_by=current_user.id
        )

        created_entity = RequestRepository.create(db, entity)

        # Audit Log
        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_CREATED,
            module=cls.MODULE_NAME,
            entity_id=created_entity.id,
            new_value={
                "request_code": created_entity.request_code,
                "visitor_id": created_entity.visitor_id,
                "host_id": created_entity.host_id,
                "purpose": created_entity.purpose,
                "status": created_entity.status.value
            },
            ip_address=ip_address
        )

        # Trigger notification hooks
        NotificationService.notify_request_created(created_entity)

        return RequestMapper.to_request_response(created_entity)

    @classmethod
    def list_requests(
        cls,
        db: Session,
        current_user: User,
        params: VisitRequestPaginationRequest
    ) -> EnhancedPaginationResponse[VisitRequestResponse]:
        """
        Retrieve paginated, filtered, and sorted visit requests list within tenant isolation.
        """
        if current_user.role and current_user.role.name != SystemRoles.SUPER_ADMIN:
            params.tenant_id = current_user.tenant_id

        requests, total_count = RequestRepository.find_all(db, params)
        return RequestMapper.to_paginated_response(
            requests=requests,
            total_records=total_count,
            page=params.page,
            page_size=params.page_size
        )

    @classmethod
    def get_request_by_id(
        cls,
        db: Session,
        current_user: User,
        request_id: int
    ) -> VisitRequestResponse:
        """
        Retrieve single visit request by ID.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id, include_deleted=True)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        return RequestMapper.to_request_response(entity)

    @classmethod
    def update_request(
        cls,
        db: Session,
        current_user: User,
        request_id: int,
        request: UpdateVisitRequest,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Update visit request details. Only allowed when request status is PENDING.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        if entity.status != VisitRequestStatus.PENDING:
            raise ValidationException(f"Cannot edit visit request in '{entity.status.value}' state")

        old_snapshot = {
            "visitor_id": entity.visitor_id,
            "host_id": entity.host_id,
            "purpose": entity.purpose,
            "scheduled_start_time": str(entity.scheduled_start_time),
            "scheduled_end_time": str(entity.scheduled_end_time)
        }

        target_visitor_id = request.visitor_id or entity.visitor_id
        target_host_id = request.host_id or entity.host_id
        
        target_start = request.scheduled_start_time or entity.scheduled_start_time
        if target_start and target_start.tzinfo:
            target_start = target_start.replace(tzinfo=None)
            
        target_end = request.scheduled_end_time or entity.scheduled_end_time
        if target_end and target_end.tzinfo:
            target_end = target_end.replace(tzinfo=None)

        # Validate eligibility & times if updated
        RequestValidator.validate_visitor_eligibility(db, target_visitor_id, entity.tenant_id)
        RequestValidator.validate_host_eligibility(db, target_host_id, entity.tenant_id)
        RequestValidator.validate_scheduled_times(target_start, target_end)

        if request.scheduled_start_time or request.scheduled_end_time or request.visitor_id:
            RequestValidator.validate_no_overlapping_booking(
                db=db,
                tenant_id=entity.tenant_id,
                visitor_id=target_visitor_id,
                start_time=target_start,
                end_time=target_end,
                exclude_id=entity.id
            )

        if request.visitor_id is not None:
            entity.visitor_id = request.visitor_id
        if request.host_id is not None:
            entity.host_id = request.host_id
        if request.purpose is not None:
            entity.purpose = request.purpose.strip()
        if request.department is not None:
            entity.department = request.department.strip()
        if request.scheduled_start_time is not None:
            entity.scheduled_start_time = target_start
        if request.scheduled_end_time is not None:
            entity.scheduled_end_time = target_end
        if request.additional_visitors_count is not None:
            entity.additional_visitors_count = request.additional_visitors_count
        if request.notes is not None:
            entity.notes = request.notes.strip()

        entity.updated_by = current_user.id
        updated_entity = RequestRepository.update(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_UPDATED,
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            old_value=old_snapshot,
            new_value={
                "visitor_id": updated_entity.visitor_id,
                "host_id": updated_entity.host_id,
                "purpose": updated_entity.purpose,
                "scheduled_start_time": str(updated_entity.scheduled_start_time),
                "scheduled_end_time": str(updated_entity.scheduled_end_time)
            },
            ip_address=ip_address
        )

        return RequestMapper.to_request_response(updated_entity)

    @classmethod
    def approve_request(
        cls,
        db: Session,
        current_user: User,
        request_id: int,
        approval_data: Optional[ApprovalRequest] = None,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Approve visit request. Transitions status to APPROVED, triggers QR pass generation & notifications.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        RequestValidator.validate_state_transition(entity, target_action="APPROVE")

        entity.status = VisitRequestStatus.APPROVED
        entity.approved_by = current_user.id
        entity.approved_at = datetime.now()
        if approval_data and approval_data.approval_notes:
            entity.approval_notes = approval_data.approval_notes.strip()

        updated_entity = RequestRepository.update(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_APPROVED,
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            new_value={
                "request_code": updated_entity.request_code,
                "status": updated_entity.status.value,
                "approved_by": current_user.id,
                "approval_notes": updated_entity.approval_notes
            },
            ip_address=ip_address
        )

        # Downstream integrations: Generate Visitor QR Pass & send notifications
        PassService.generate_pass_for_approved_request(updated_entity)
        NotificationService.notify_request_approved(updated_entity)

        return RequestMapper.to_request_response(updated_entity)

    @classmethod
    def reject_request(
        cls,
        db: Session,
        current_user: User,
        request_id: int,
        rejection_data: RejectRequest,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Reject visit request with explicit rejection reason.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        RequestValidator.validate_state_transition(
            visit_request=entity,
            target_action="REJECT",
            rejection_reason=rejection_data.rejection_reason
        )

        entity.status = VisitRequestStatus.REJECTED
        entity.rejected_by = current_user.id
        entity.rejected_at = datetime.now()
        entity.rejection_reason = rejection_data.rejection_reason.strip()

        updated_entity = RequestRepository.update(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_REJECTED,
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            new_value={
                "request_code": updated_entity.request_code,
                "status": updated_entity.status.value,
                "rejected_by": current_user.id,
                "rejection_reason": updated_entity.rejection_reason
            },
            ip_address=ip_address
        )

        NotificationService.notify_request_rejected(updated_entity)

        return RequestMapper.to_request_response(updated_entity)

    @classmethod
    def cancel_request(
        cls,
        db: Session,
        current_user: User,
        request_id: int,
        cancel_data: CancelRequest,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Cancel visit request with explicit cancellation reason.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        RequestValidator.validate_state_transition(
            visit_request=entity,
            target_action="CANCEL",
            cancellation_reason=cancel_data.cancellation_reason
        )

        entity.status = VisitRequestStatus.CANCELLED
        entity.cancelled_by = current_user.id
        entity.cancelled_at = datetime.now()
        entity.cancellation_reason = cancel_data.cancellation_reason.strip()

        updated_entity = RequestRepository.update(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_CANCELLED,
            module=cls.MODULE_NAME,
            entity_id=updated_entity.id,
            new_value={
                "request_code": updated_entity.request_code,
                "status": updated_entity.status.value,
                "cancelled_by": current_user.id,
                "cancellation_reason": updated_entity.cancellation_reason
            },
            ip_address=ip_address
        )

        NotificationService.notify_request_cancelled(updated_entity)

        return RequestMapper.to_request_response(updated_entity)

    @classmethod
    def delete_request(
        cls,
        db: Session,
        current_user: User,
        request_id: int,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Soft delete visit request.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        deleted_entity = RequestRepository.delete(db, entity, deleted_by=current_user.id)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_DELETED,
            module=cls.MODULE_NAME,
            entity_id=deleted_entity.id,
            ip_address=ip_address
        )

        return RequestMapper.to_request_response(deleted_entity)

    @classmethod
    def restore_request(
        cls,
        db: Session,
        current_user: User,
        request_id: int,
        ip_address: Optional[str] = None
    ) -> VisitRequestResponse:
        """
        Restore a soft-deleted visit request.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entity = RequestRepository.find_by_id(db, request_id=request_id, tenant_id=tenant_id, include_deleted=True)
        if not entity:
            raise NotFoundException(f"Visit request with ID {request_id} not found")

        RequestValidator.validate_state_transition(entity, target_action="RESTORE")

        restored_entity = RequestRepository.restore(db, entity)

        AuditRepository.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=AuditActions.VISIT_REQUEST_RESTORED,
            module=cls.MODULE_NAME,
            entity_id=restored_entity.id,
            ip_address=ip_address
        )

        return RequestMapper.to_request_response(restored_entity)

    @classmethod
    def get_pending_requests(
        cls,
        db: Session,
        current_user: User
    ) -> List[VisitRequestResponse]:
        """
        Retrieve all pending requests awaiting review/approval for host or tenant admin.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        host_id = None if current_user.role and current_user.role.name in [SystemRoles.SUPER_ADMIN, SystemRoles.TENANT_ADMIN] else current_user.id
        
        entities = RequestRepository.find_pending_requests(db, tenant_id=tenant_id, host_id=host_id)
        return RequestMapper.to_request_response_list(entities)

    @classmethod
    def get_my_requests(
        cls,
        db: Session,
        current_user: User
    ) -> List[VisitRequestResponse]:
        """
        Retrieve all visit requests created by or hosted by the authenticated user.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entities = RequestRepository.find_by_host(db, host_id=current_user.id, tenant_id=tenant_id)
        return RequestMapper.to_request_response_list(entities)

    @classmethod
    def get_calendar(
        cls,
        db: Session,
        current_user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> VisitRequestCalendarResponse:
        """
        Retrieve request calendar feed.
        """
        tenant_id = None if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        entities = RequestRepository.get_calendar_events(db, tenant_id=tenant_id, start_date=start_date, end_date=end_date)
        return RequestMapper.to_calendar_response(entities, start_date=start_date, end_date=end_date)

    @classmethod
    def get_statistics(
        cls,
        db: Session,
        current_user: User,
        tenant_id: Optional[int] = None
    ) -> VisitRequestStatisticsResponse:
        """
        Retrieve request dashboard statistics.
        """
        target_tenant_id = tenant_id if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN else current_user.tenant_id
        stats = RequestRepository.get_statistics(db, tenant_id=target_tenant_id)
        return RequestMapper.to_statistics_response(stats)

    @classmethod
    def export_requests(
        cls,
        db: Session,
        current_user: User,
        params: VisitRequestPaginationRequest
    ) -> str:
        """
        Export filtered visit requests to CSV data format string.
        """
        if current_user.role and current_user.role.name != SystemRoles.SUPER_ADMIN:
            params.tenant_id = current_user.tenant_id

        params.page_size = 10000
        requests, _ = RequestRepository.find_all(db, params)
        return ExportService.export_requests_csv(requests)
