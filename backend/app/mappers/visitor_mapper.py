import math
from typing import List, Dict, Any
from app.models.visitor import Visitor
from app.models.audit_log import AuditLog
from app.schemas.user import EnhancedPaginationResponse
from app.schemas.visitor import VisitorResponse, VisitorActivityResponse, VisitorStatisticsResponse

class VisitorMapper:
    """
    Mapper layer converting ORM Visitor models and AuditLog entities into standardized Pydantic DTO responses.
    """

    @staticmethod
    def to_visitor_response(visitor: Visitor) -> VisitorResponse:
        """
        Convert Visitor ORM entity to VisitorResponse DTO.
        """
        return VisitorResponse.model_validate(visitor)

    @staticmethod
    def to_visitor_response_list(visitors: List[Visitor]) -> List[VisitorResponse]:
        """
        Convert list of Visitor ORM entities to list of VisitorResponse DTOs.
        """
        return [VisitorMapper.to_visitor_response(v) for v in visitors]

    @staticmethod
    def to_paginated_response(
        visitors: List[Visitor], 
        total_records: int, 
        page: int, 
        page_size: int
    ) -> EnhancedPaginationResponse[VisitorResponse]:
        """
        Wrap list of visitors in EnhancedPaginationResponse container.
        """
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        items = VisitorMapper.to_visitor_response_list(visitors)

        return EnhancedPaginationResponse[VisitorResponse](
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
            items=items
        )

    @staticmethod
    def to_activity_response(log: AuditLog) -> VisitorActivityResponse:
        """
        Convert AuditLog model to VisitorActivityResponse.
        """
        return VisitorActivityResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            module=log.module,
            entity_id=log.entity_id,
            old_value=log.old_value,
            new_value=log.new_value,
            ip_address=log.ip_address,
            created_at=log.created_at
        )

    @staticmethod
    def to_activity_response_list(logs: List[AuditLog]) -> List[VisitorActivityResponse]:
        """
        Convert list of AuditLog entities to list of VisitorActivityResponse DTOs.
        """
        return [VisitorMapper.to_activity_response(log) for log in logs]

    @staticmethod
    def to_statistics_response(stats: Dict[str, Any]) -> VisitorStatisticsResponse:
        """
        Convert raw repository statistics dict to VisitorStatisticsResponse DTO.
        """
        return VisitorStatisticsResponse(
            total_visitors=stats.get("total_visitors", 0),
            active_visitors=stats.get("active_visitors", 0),
            inactive_visitors=stats.get("inactive_visitors", 0),
            blacklisted_visitors=stats.get("blacklisted_visitors", 0),
            verified_visitors=stats.get("verified_visitors", 0),
            pending_verification_visitors=stats.get("pending_verification_visitors", 0),
            today_visitors=stats.get("today_visitors", 0),
            this_month_visitors=stats.get("this_month_visitors", 0),
            returning_visitors=stats.get("returning_visitors", 0)
        )
