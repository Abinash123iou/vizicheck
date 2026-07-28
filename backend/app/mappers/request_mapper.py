import math
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from app.models.visit_request import VisitRequest
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.request import (
    VisitRequestResponse,
    VisitRequestStatisticsResponse,
    VisitRequestCalendarItem,
    VisitRequestCalendarResponse
)

class RequestMapper:
    """
    Mapper layer converting ORM VisitRequest models into standardized Pydantic DTO responses.
    """

    @staticmethod
    def to_request_response(request: VisitRequest) -> VisitRequestResponse:
        """
        Convert VisitRequest ORM entity to VisitRequestResponse DTO, enriching with visitor and host details.
        """
        visitor_name = f"{request.visitor.first_name} {request.visitor.last_name}" if request.visitor else None
        visitor_phone = request.visitor.phone if request.visitor else None
        visitor_email = request.visitor.email if request.visitor else None

        host_name = f"{request.host.first_name} {request.host.last_name}" if request.host else None
        host_email = request.host.email if request.host else None

        return VisitRequestResponse(
            id=request.id,
            tenant_id=request.tenant_id,
            request_code=request.request_code,
            visitor_id=request.visitor_id,
            visitor_name=visitor_name,
            visitor_phone=visitor_phone,
            visitor_email=visitor_email,
            host_id=request.host_id,
            host_name=host_name,
            host_email=host_email,
            purpose=request.purpose,
            department=request.department,
            scheduled_start_time=request.scheduled_start_time,
            scheduled_end_time=request.scheduled_end_time,
            actual_checkin=request.actual_checkin,
            actual_checkout=request.actual_checkout,
            additional_visitors_count=request.additional_visitors_count,
            notes=request.notes,
            status=request.status,
            approved_by=request.approved_by,
            approved_at=request.approved_at,
            approval_notes=request.approval_notes,
            rejected_by=request.rejected_by,
            rejected_at=request.rejected_at,
            rejection_reason=request.rejection_reason,
            cancelled_by=request.cancelled_by,
            cancelled_at=request.cancelled_at,
            cancellation_reason=request.cancellation_reason,
            created_by=request.created_by,
            created_at=request.created_at,
            updated_at=request.updated_at,
            is_deleted=request.is_deleted
        )

    @staticmethod
    def to_request_response_list(requests: List[VisitRequest]) -> List[VisitRequestResponse]:
        """
        Convert list of VisitRequest ORM entities to list of VisitRequestResponse DTOs.
        """
        return [RequestMapper.to_request_response(r) for r in requests]

    @staticmethod
    def to_paginated_response(
        requests: List[VisitRequest], 
        total_records: int, 
        page: int, 
        page_size: int
    ) -> EnhancedPaginationResponse[VisitRequestResponse]:
        """
        Wrap list of VisitRequest DTOs in EnhancedPaginationResponse container.
        """
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        items = RequestMapper.to_request_response_list(requests)

        return EnhancedPaginationResponse[VisitRequestResponse](
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
            items=items
        )

    @staticmethod
    def to_statistics_response(stats: Dict[str, Any]) -> VisitRequestStatisticsResponse:
        """
        Convert raw repository statistics dict into VisitRequestStatisticsResponse DTO.
        """
        return VisitRequestStatisticsResponse(
            total_requests=stats.get("total_requests", 0),
            pending_requests=stats.get("pending_requests", 0),
            approved_requests=stats.get("approved_requests", 0),
            rejected_requests=stats.get("rejected_requests", 0),
            cancelled_requests=stats.get("cancelled_requests", 0),
            checked_in_requests=stats.get("checked_in_requests", 0),
            checked_out_requests=stats.get("checked_out_requests", 0),
            completed_requests=stats.get("completed_requests", 0),
            expired_requests=stats.get("expired_requests", 0),
            today_requests=stats.get("today_requests", 0),
            average_approval_time_minutes=stats.get("average_approval_time_minutes", 0.0),
            peak_visiting_hours=stats.get("peak_visiting_hours", {})
        )

    @staticmethod
    def to_calendar_response(
        requests: List[VisitRequest], 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> VisitRequestCalendarResponse:
        """
        Group VisitRequest entities into date-based calendar items.
        """
        now = datetime.now()
        effective_start = start_date or now
        effective_end = end_date or (now + float_days(30))

        # Grouping by YYYY-MM-DD
        grouped: Dict[str, Dict[str, int]] = {}
        for req in requests:
            day_str = req.scheduled_start_time.strftime("%Y-%m-%d") if req.scheduled_start_time else "Unknown"
            if day_str not in grouped:
                grouped[day_str] = {"total": 0, "pending": 0, "approved": 0, "completed": 0}
            grouped[day_str]["total"] += 1
            if req.status.value == "PENDING":
                grouped[day_str]["pending"] += 1
            elif req.status.value == "APPROVED":
                grouped[day_str]["approved"] += 1
            elif req.status.value in ["COMPLETED", "CHECKED_OUT"]:
                grouped[day_str]["completed"] += 1

        days_list = [
            VisitRequestCalendarItem(
                date=day_str,
                total_count=counts["total"],
                pending_count=counts["pending"],
                approved_count=counts["approved"],
                completed_count=counts["completed"]
            )
            for day_str, counts in sorted(grouped.items())
        ]

        response_items = RequestMapper.to_request_response_list(requests)

        return VisitRequestCalendarResponse(
            start_date=effective_start,
            end_date=effective_end,
            total_requests=len(requests),
            days=days_list,
            requests=response_items
        )

def float_days(num_days: int):
    from datetime import timedelta
    return timedelta(days=num_days)
