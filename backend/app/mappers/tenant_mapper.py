import math
from typing import List, Dict, Optional
from app.models.tenant import Tenant
from app.models.audit_log import AuditLog
from app.schemas.tenant import (
    TenantResponse, 
    TenantSettingsDTO, 
    EnhancedPaginationResponse,
    TenantStatisticsResponse,
    TenantOverviewStats,
    UserStatsSummary,
    VisitorStatsSummary,
    RequestStatsSummary,
    PassStatsSummary,
    TenantActivityResponse
)

class TenantMapper:
    """
    Mapper class responsible for transforming Tenant ORM models to response DTOs.
    """

    @staticmethod
    def to_tenant_response(tenant: Tenant, user_count: int = 0) -> TenantResponse:
        """
        Convert Tenant ORM model to TenantResponse DTO.
        """
        settings_dto = None
        if tenant.settings:
            settings_dto = TenantSettingsDTO(
                timezone=tenant.settings.timezone,
                language=tenant.settings.language,
                currency=tenant.settings.currency,
                date_format=tenant.settings.date_format,
                max_users=tenant.settings.max_users,
                max_visitors=tenant.settings.max_visitors,
                allowed_login_methods=tenant.settings.allowed_login_methods or ["PASSWORD"]
            )
        else:
            settings_dto = TenantSettingsDTO()

        return TenantResponse(
            id=tenant.id,
            code=tenant.code,
            name=tenant.name,
            slug=tenant.slug,
            domain=tenant.domain,
            description=tenant.description,
            contact_person=tenant.contact_person,
            contact_email=tenant.contact_email,
            contact_phone=tenant.contact_phone,
            status=tenant.status,
            is_deleted=getattr(tenant, "is_deleted", False),
            user_count=user_count,
            settings=settings_dto,
            created_by_id=tenant.created_by_id,
            updated_by_id=tenant.updated_by_id,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )

    @classmethod
    def to_paginated_response(
        cls,
        tenants: List[Tenant],
        user_counts_map: Dict[int, int],
        total_records: int,
        page: int,
        page_size: int
    ) -> EnhancedPaginationResponse[TenantResponse]:
        """
        Construct EnhancedPaginationResponse containing mapped TenantResponse items and metadata.
        """
        items = [cls.to_tenant_response(t, user_counts_map.get(t.id, 0)) for t in tenants]
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1 and total_pages > 0

        return EnhancedPaginationResponse(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            items=items
        )

    @staticmethod
    def to_statistics_response(stats_dict: dict) -> TenantStatisticsResponse:
        """
        Map dictionary of calculated statistics to TenantStatisticsResponse DTO.
        """
        return TenantStatisticsResponse(
            tenant_overview=TenantOverviewStats(**stats_dict.get("tenant_overview", {})),
            user_stats=UserStatsSummary(**stats_dict.get("user_stats", {})),
            visitor_stats=VisitorStatsSummary(**stats_dict.get("visitor_stats", {})),
            request_stats=RequestStatsSummary(**stats_dict.get("request_stats", {})),
            pass_stats=PassStatsSummary(**stats_dict.get("pass_stats", {}))
        )

    @staticmethod
    def to_activity_response(log: AuditLog) -> TenantActivityResponse:
        """
        Convert AuditLog entity to TenantActivityResponse DTO.
        """
        return TenantActivityResponse(
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
