from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, or_, and_, extract
from sqlalchemy.orm import Session

from app.models.visitor_pass import VisitorPass, PassStatus, PassStatusHistory
from app.models.tenant import Tenant
from app.models.qr_token import QRToken
from app.schemas.pass_schema import PassPaginationRequest
from app.repositories.specifications.pass_filters import PassFilters


class PassRepository:
    """
    Database access layer for VisitorPass & PassStatusHistory entities.
    Enforces tenant isolation, soft-deletion, audit history logging, and stats.
    """

    @staticmethod
    def generate_pass_code(db: Session, tenant_id: int) -> str:
        """
        Generate tenant-aware sequential visitor pass code: VP-YYYY-TENXXXX-XXXXXX
        (e.g., VP-2026-TEN000138-000001).
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        tenant_code = tenant.code if tenant and tenant.code else f"TEN{tenant_id:06d}"
        
        current_year = datetime.now().year
        max_id = db.query(func.max(VisitorPass.id)).scalar() or 0
        next_seq = max_id + 1
        return f"VP-{current_year}-{tenant_code}-{next_seq:06d}"

    @staticmethod
    def find_by_id(
        db: Session, 
        pass_id: int, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[VisitorPass]:
        """
        Find visitor pass by integer primary key ID.
        """
        query = db.query(VisitorPass).filter(VisitorPass.id == pass_id)
        if tenant_id is not None:
            query = query.filter(VisitorPass.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(VisitorPass.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_uuid(
        db: Session, 
        pass_uuid: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[VisitorPass]:
        """
        Find visitor pass by UUID string.
        """
        query = db.query(VisitorPass).filter(VisitorPass.uuid == pass_uuid.strip())
        if tenant_id is not None:
            query = query.filter(VisitorPass.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(VisitorPass.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_pass_code(
        db: Session, 
        pass_code: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[VisitorPass]:
        """
        Find visitor pass by pass code.
        """
        query = db.query(VisitorPass).filter(VisitorPass.pass_code == pass_code.strip())
        if tenant_id is not None:
            query = query.filter(VisitorPass.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(VisitorPass.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_visit_request_id(
        db: Session, 
        visit_request_id: int, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[VisitorPass]:
        """
        Find visitor pass by visit request ID.
        """
        query = db.query(VisitorPass).filter(VisitorPass.visit_request_id == visit_request_id)
        if tenant_id is not None:
            query = query.filter(VisitorPass.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(VisitorPass.is_deleted.is_(False))
        return query.order_by(VisitorPass.created_at.desc()).first()

    @staticmethod
    def find_active_existing_pass_for_request(
        db: Session, 
        visit_request_id: int, 
        tenant_id: int
    ) -> Optional[VisitorPass]:
        """
        Find if an existing non-terminated pass (PENDING, ACTIVE, USED) exists for a visit request.
        """
        active_statuses = [PassStatus.PENDING, PassStatus.ACTIVE, PassStatus.USED]
        return db.query(VisitorPass).filter(
            VisitorPass.tenant_id == tenant_id,
            VisitorPass.visit_request_id == visit_request_id,
            VisitorPass.status.in_(active_statuses),
            VisitorPass.is_deleted.is_(False)
        ).first()

    @staticmethod
    def find_expired_active_passes(db: Session) -> List[VisitorPass]:
        """
        Find all ACTIVE passes whose valid_until timestamp is in the past.
        """
        now = datetime.now()
        return db.query(VisitorPass).filter(
            VisitorPass.status == PassStatus.ACTIVE,
            VisitorPass.valid_until < now,
            VisitorPass.is_deleted.is_(False)
        ).all()

    @staticmethod
    def find_all(
        db: Session, 
        params: PassPaginationRequest
    ) -> Tuple[List[VisitorPass], int]:
        """
        Retrieve paginated, searched, filtered, and sorted visitor passes.
        """
        query = db.query(VisitorPass)
        query = PassFilters.apply_filters(
            query=query,
            tenant_id=params.tenant_id,
            search=params.search,
            status=params.status,
            visitor_id=params.visitor_id,
            host_id=params.host_id,
            visit_request_id=params.visit_request_id,
            is_deleted=params.is_deleted
        )

        total_count = query.count()
        query = PassFilters.apply_sorting(query, sort_by=params.sort_by, order=params.order)

        offset = (params.page - 1) * params.page_size
        results = query.offset(offset).limit(params.page_size).all()
        return results, total_count

    @staticmethod
    def get_statistics(db: Session, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate dashboard analytics metrics for Visitor Passes.
        """
        base_query = db.query(VisitorPass).filter(VisitorPass.is_deleted.is_(False))
        if tenant_id is not None:
            base_query = base_query.filter(VisitorPass.tenant_id == tenant_id)

        total_passes = base_query.count()

        # Status counts
        status_counts = db.query(
            VisitorPass.status, func.count(VisitorPass.id)
        ).filter(
            VisitorPass.is_deleted.is_(False)
        )
        if tenant_id is not None:
            status_counts = status_counts.filter(VisitorPass.tenant_id == tenant_id)
        status_map = dict(status_counts.group_by(VisitorPass.status).all())

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Today's generated
        today_generated = base_query.filter(
            VisitorPass.created_at >= today_start,
            VisitorPass.created_at < today_end
        ).count()

        # Today's expired
        today_expired = base_query.filter(
            VisitorPass.status == PassStatus.EXPIRED,
            VisitorPass.valid_until >= today_start,
            VisitorPass.valid_until < today_end
        ).count()

        # Today's revoked
        today_revoked = base_query.filter(
            VisitorPass.status == PassStatus.REVOKED,
            VisitorPass.revoked_at >= today_start,
            VisitorPass.revoked_at < today_end
        ).count()

        # Currently valid
        currently_valid = base_query.filter(
            VisitorPass.status == PassStatus.ACTIVE,
            VisitorPass.valid_from <= now,
            VisitorPass.valid_until >= now
        ).count()

        # Average validity duration in minutes
        valid_passes = base_query.all()
        total_duration_minutes = 0.0
        if valid_passes:
            for p in valid_passes:
                if p.valid_until and p.valid_from:
                    delta = (p.valid_until - p.valid_from).total_seconds() / 60.0
                    total_duration_minutes += max(delta, 0.0)
            avg_duration = round(total_duration_minutes / len(valid_passes), 2)
        else:
            avg_duration = 0.0

        # QR regeneration count (tokens version > 1)
        qr_regen_query = db.query(func.count(QRToken.id)).filter(QRToken.version > 1)
        if tenant_id is not None:
            qr_regen_query = qr_regen_query.filter(QRToken.tenant_id == tenant_id)
        qr_regen_count = qr_regen_query.scalar() or 0

        return {
            "total_passes": total_passes,
            "pending_passes": status_map.get(PassStatus.PENDING, 0),
            "active_passes": status_map.get(PassStatus.ACTIVE, 0),
            "used_passes": status_map.get(PassStatus.USED, 0),
            "completed_passes": status_map.get(PassStatus.COMPLETED, 0),
            "expired_passes": status_map.get(PassStatus.EXPIRED, 0),
            "revoked_passes": status_map.get(PassStatus.REVOKED, 0),
            "today_generated": today_generated,
            "today_expired": today_expired,
            "today_revoked": today_revoked,
            "currently_valid": currently_valid,
            "average_validity_duration_minutes": avg_duration,
            "qr_regeneration_count": qr_regen_count
        }

    @staticmethod
    def create(db: Session, pass_entity: VisitorPass) -> VisitorPass:
        """
        Persist a new VisitorPass entity.
        """
        db.add(pass_entity)
        db.commit()
        db.refresh(pass_entity)
        return pass_entity

    @staticmethod
    def update(db: Session, pass_entity: VisitorPass) -> VisitorPass:
        """
        Save changes to an existing VisitorPass entity.
        """
        db.commit()
        db.refresh(pass_entity)
        return pass_entity

    @staticmethod
    def delete(db: Session, pass_entity: VisitorPass, deleted_by: Optional[int] = None) -> VisitorPass:
        """
        Soft delete a VisitorPass entity.
        """
        pass_entity.is_deleted = True
        pass_entity.deleted_at = datetime.now()
        pass_entity.deleted_by = deleted_by
        db.commit()
        db.refresh(pass_entity)
        return pass_entity

    @staticmethod
    def restore(db: Session, pass_entity: VisitorPass) -> VisitorPass:
        """
        Restore a soft-deleted VisitorPass entity.
        """
        pass_entity.is_deleted = False
        pass_entity.deleted_at = None
        pass_entity.deleted_by = None
        db.commit()
        db.refresh(pass_entity)
        return pass_entity

    @staticmethod
    def record_status_change(
        db: Session, 
        pass_id: int, 
        old_status: Optional[PassStatus], 
        new_status: PassStatus, 
        changed_by: Optional[int] = None, 
        remarks: Optional[str] = None
    ) -> PassStatusHistory:
        """
        Record a status transition entry in pass_status_history table.
        """
        history = PassStatusHistory(
            pass_id=pass_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            changed_at=datetime.now(),
            remarks=remarks
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
