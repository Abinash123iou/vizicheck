from typing import List, Optional
from app.models.approval import Approval, ApprovalHistory
from app.schemas.approval import ApprovalResponse, ApprovalHistoryResponse


class ApprovalMapper:
    """
    Mapper layer converting Approval ORM entities to Pydantic DTO responses.
    """

    @staticmethod
    def to_history_response(history: ApprovalHistory) -> ApprovalHistoryResponse:
        actor_name = None
        if hasattr(history, "actor") and history.actor:
            actor_name = f"{history.actor.first_name} {history.actor.last_name}".strip()

        delegated_to_name = None
        if hasattr(history, "delegated_to") and history.delegated_to:
            delegated_to_name = f"{history.delegated_to.first_name} {history.delegated_to.last_name}".strip()

        return ApprovalHistoryResponse(
            id=history.id,
            approval_id=history.approval_id,
            tenant_id=history.tenant_id,
            step_number=history.step_number,
            actor_id=history.actor_id,
            actor_name=actor_name,
            action=history.action,
            previous_status=history.previous_status,
            new_status=history.new_status,
            comments=history.comments,
            delegated_to_id=history.delegated_to_id,
            delegated_to_name=delegated_to_name,
            created_at=history.created_at
        )

    @staticmethod
    def to_history_response_list(histories: List[ApprovalHistory]) -> List[ApprovalHistoryResponse]:
        return [ApprovalMapper.to_history_response(h) for h in histories]

    @staticmethod
    def to_response(approval: Approval, include_history: bool = True) -> ApprovalResponse:
        request_code = None
        visitor_name = None
        host_id = None
        host_name = None

        if hasattr(approval, "visit_request") and approval.visit_request:
            req = approval.visit_request
            request_code = req.request_code
            host_id = req.host_id
            if hasattr(req, "host") and req.host:
                host_name = f"{req.host.first_name} {req.host.last_name}".strip()
            if hasattr(req, "visitor") and req.visitor:
                visitor_name = f"{req.visitor.first_name} {req.visitor.last_name}".strip()

        current_approver_name = None
        if hasattr(approval, "current_approver") and approval.current_approver:
            current_approver_name = f"{approval.current_approver.first_name} {approval.current_approver.last_name}".strip()

        history_list = None
        if include_history and hasattr(approval, "history_entries") and approval.history_entries:
            history_list = ApprovalMapper.to_history_response_list(approval.history_entries)

        return ApprovalResponse(
            id=approval.id,
            tenant_id=approval.tenant_id,
            request_id=approval.request_id,
            request_code=request_code,
            visitor_name=visitor_name,
            host_id=host_id,
            host_name=host_name,
            approval_code=approval.approval_code,
            approval_type=approval.approval_type,
            current_step=approval.current_step,
            total_steps=approval.total_steps,
            current_approver_id=approval.current_approver_id,
            current_approver_name=current_approver_name,
            status=approval.status,
            expires_at=approval.expires_at,
            notes=approval.notes,
            created_at=approval.created_at,
            updated_at=approval.updated_at,
            history=history_list
        )

    @staticmethod
    def to_response_list(approvals: List[Approval], include_history: bool = False) -> List[ApprovalResponse]:
        return [ApprovalMapper.to_response(app, include_history=include_history) for app in approvals]
