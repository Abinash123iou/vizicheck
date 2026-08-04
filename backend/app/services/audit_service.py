import csv
import io
import json
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.core.exceptions import ValidationException

class AuditService:
    """
    Service layer providing audit log querying, multi-tenant isolation,
    entity change history, and export capabilities (CSV/JSON).
    """

    @classmethod
    def get_audit_logs(
        cls,
        db: Session,
        current_user: User,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> AuditLogListResponse:
        """
        Retrieve paginated audit logs with strict multi-tenant RBAC enforcement.
        """
        # RBAC Multi-tenant isolation enforcement
        if current_user.is_super_admin:
            eff_tenant_id = tenant_id
            eff_user_id = user_id
        elif current_user.role and current_user.role.name in ["TENANT_ADMIN", "SECURITY_OFFICER"]:
            eff_tenant_id = current_user.tenant_id
            eff_user_id = user_id
        else:
            eff_tenant_id = current_user.tenant_id
            eff_user_id = current_user.id

        items, total = AuditRepository.get_audit_logs(
            db,
            tenant_id=eff_tenant_id,
            user_id=eff_user_id,
            module=module,
            action=action,
            start_date=start_date,
            end_date=end_date,
            search=search,
            page=page,
            limit=limit
        )

        dtos = []
        for item in items:
            dto = AuditLogResponse(
                id=item.id,
                user_id=item.user_id,
                user_email=item.user.email if item.user else None,
                tenant_id=item.tenant_id,
                tenant_name=item.tenant.name if item.tenant else None,
                action=item.action,
                module=item.module,
                entity_id=item.entity_id,
                old_value=item.old_value,
                new_value=item.new_value,
                ip_address=item.ip_address,
                created_at=item.created_at
            )
            dtos.append(dto)

        pages = (total + limit - 1) // limit if limit > 0 else 1
        return AuditLogListResponse(
            items=dtos,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )

    @classmethod
    def export_audit_logs(
        cls,
        db: Session,
        current_user: User,
        export_format: str = "csv",
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[bytes, str, str]:
        """
        Export audit logs into CSV or JSON file streams.
        Returns tuple: (bytes_content, media_type, filename)
        """
        export_format = export_format.lower()
        if export_format not in ["csv", "json"]:
            raise ValidationException("Export format must be either 'csv' or 'json'")

        # RBAC Multi-tenant isolation enforcement
        if current_user.is_super_admin:
            eff_tenant_id = tenant_id
            eff_user_id = user_id
        elif current_user.role and current_user.role.name in ["TENANT_ADMIN", "SECURITY_OFFICER"]:
            eff_tenant_id = current_user.tenant_id
            eff_user_id = user_id
        else:
            eff_tenant_id = current_user.tenant_id
            eff_user_id = current_user.id

        items = AuditRepository.get_all_audit_logs_for_export(
            db,
            tenant_id=eff_tenant_id,
            user_id=eff_user_id,
            module=module,
            action=action,
            start_date=start_date,
            end_date=end_date
        )

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            # Write header
            writer.writerow([
                "ID", "Created At", "User ID", "User Email", "Tenant ID",
                "Module", "Action", "Entity ID", "IP Address", "Old Value", "New Value"
            ])

            for item in items:
                writer.writerow([
                    item.id,
                    item.created_at.isoformat() if item.created_at else "",
                    item.user_id or "",
                    item.user.email if item.user else "",
                    item.tenant_id or "",
                    item.module or "",
                    item.action or "",
                    item.entity_id or "",
                    item.ip_address or "",
                    json.dumps(item.old_value) if item.old_value else "",
                    json.dumps(item.new_value) if item.new_value else ""
                ])

            filename = f"audit_logs_{timestamp_str}.csv"
            return output.getvalue().encode("utf-8"), "text/csv", filename

        else:
            # JSON format
            export_data = []
            for item in items:
                export_data.append({
                    "id": item.id,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "user_id": item.user_id,
                    "user_email": item.user.email if item.user else None,
                    "tenant_id": item.tenant_id,
                    "tenant_name": item.tenant.name if item.tenant else None,
                    "module": item.module,
                    "action": item.action,
                    "entity_id": item.entity_id,
                    "ip_address": item.ip_address,
                    "old_value": item.old_value,
                    "new_value": item.new_value
                })

            filename = f"audit_logs_{timestamp_str}.json"
            content = json.dumps(export_data, indent=2).encode("utf-8")
            return content, "application/json", filename
