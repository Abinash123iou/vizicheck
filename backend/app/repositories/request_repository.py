from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, or_, and_, extract
from sqlalchemy.orm import Session
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.tenant import Tenant
from app.schemas.request import VisitRequestPaginationRequest
from app.repositories.specifications.request_filters import RequestFilters

class RequestRepository:
    """
    Database access layer for VisitRequest entities with tenant boundary security,
    soft deletion, dynamic specifications, statistics calculations, and overlap detection.
    """

    @staticmethod
    def generate_request_code(db: Session, tenant_id: int) -> str:
        """
        Generate tenant-aware sequential visit request code (e.g. VR-TEN-000001-000001).
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        tenant_code = tenant.code if tenant and tenant.code else f"TEN-{tenant_id:06d}"
        
        max_id = db.query(func.max(VisitRequest.id)).scalar() or 0
        next_seq = max_id + 1
        return f"VR-{tenant_code}-{next_seq:06d}"

    @staticmethod
    def find_by_id(
        db: Session, 
        request_id: int, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[VisitRequest]:
        """
        Find visit request by primary key ID with optional tenant isolation.
        """
        query = db.query(VisitRequest).filter(VisitRequest.id == request_id)
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(VisitRequest.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_request_code(
        db: Session, 
        request_code: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[VisitRequest]:
        """
        Find visit request by code with optional tenant isolation.
        """
        query = db.query(VisitRequest).filter(VisitRequest.request_code == request_code.strip())
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(VisitRequest.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_pending_requests(
        db: Session, 
        tenant_id: Optional[int] = None, 
        host_id: Optional[int] = None
    ) -> List[VisitRequest]:
        """
        Find all pending visit requests awaiting review/approval for host or tenant.
        """
        query = db.query(VisitRequest).filter(
            VisitRequest.status == VisitRequestStatus.PENDING,
            VisitRequest.is_deleted.is_(False)
        )
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        if host_id is not None:
            query = query.filter(VisitRequest.host_id == host_id)
        return query.order_by(VisitRequest.created_at.asc()).all()

    @staticmethod
    def find_today_requests(
        db: Session, 
        tenant_id: Optional[int] = None
    ) -> List[VisitRequest]:
        """
        Find all visit requests scheduled for today.
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        query = db.query(VisitRequest).filter(
            VisitRequest.scheduled_start_time >= today_start,
            VisitRequest.scheduled_start_time < today_end,
            VisitRequest.is_deleted.is_(False)
        )
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        return query.order_by(VisitRequest.scheduled_start_time.asc()).all()

    @staticmethod
    def find_by_host(
        db: Session, 
        host_id: int, 
        tenant_id: Optional[int] = None
    ) -> List[VisitRequest]:
        """
        Find all visit requests associated with a specific employee host.
        """
        query = db.query(VisitRequest).filter(
            VisitRequest.host_id == host_id,
            VisitRequest.is_deleted.is_(False)
        )
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        return query.order_by(VisitRequest.scheduled_start_time.desc()).all()

    @staticmethod
    def find_by_visitor(
        db: Session, 
        visitor_id: int, 
        tenant_id: Optional[int] = None
    ) -> List[VisitRequest]:
        """
        Find all visit requests for a given visitor.
        """
        query = db.query(VisitRequest).filter(
            VisitRequest.visitor_id == visitor_id,
            VisitRequest.is_deleted.is_(False)
        )
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        return query.order_by(VisitRequest.scheduled_start_time.desc()).all()

    @staticmethod
    def check_overlapping_request(
        db: Session, 
        tenant_id: int, 
        visitor_id: int, 
        start_time: datetime, 
        end_time: datetime, 
        exclude_id: Optional[int] = None
    ) -> Optional[VisitRequest]:
        """
        Check if visitor has any active overlapping visit request during the target time window.
        Overlapping condition: existing_start < new_end AND existing_end > new_start.
        """
        start_naive = start_time.replace(tzinfo=None) if start_time and start_time.tzinfo else start_time
        end_naive = end_time.replace(tzinfo=None) if end_time and end_time.tzinfo else end_time

        active_statuses = [VisitRequestStatus.PENDING, VisitRequestStatus.APPROVED, VisitRequestStatus.CHECKED_IN]
        query = db.query(VisitRequest).filter(
            VisitRequest.tenant_id == tenant_id,
            VisitRequest.visitor_id == visitor_id,
            VisitRequest.status.in_(active_statuses),
            VisitRequest.is_deleted.is_(False),
            VisitRequest.scheduled_start_time < end_naive,
            VisitRequest.scheduled_end_time > start_naive
        )
        if exclude_id is not None:
            query = query.filter(VisitRequest.id != exclude_id)
        return query.first()

    @staticmethod
    def find_all(
        db: Session, 
        params: VisitRequestPaginationRequest
    ) -> Tuple[List[VisitRequest], int]:
        """
        Retrieve filtered, sorted, and paginated list of visit requests alongside total matching count.
        """
        query = db.query(VisitRequest)
        query = RequestFilters.apply_filters(
            query=query,
            tenant_id=params.tenant_id,
            search=params.search,
            status=params.status,
            visitor_id=params.visitor_id,
            host_id=params.host_id,
            department=params.department,
            request_code=params.request_code,
            start_date=params.start_date,
            end_date=params.end_date,
            is_deleted=params.is_deleted
        )

        total_count = query.count()
        query = RequestFilters.apply_sorting(query, sort_by=params.sort_by, order=params.order)

        offset = (params.page - 1) * params.page_size
        results = query.offset(offset).limit(params.page_size).all()
        return results, total_count

    @staticmethod
    def get_statistics(db: Session, tenant_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive dashboard analytics statistics for Visit Requests.
        """
        base_query = db.query(VisitRequest).filter(VisitRequest.is_deleted.is_(False))
        if tenant_id is not None:
            base_query = base_query.filter(VisitRequest.tenant_id == tenant_id)

        total_requests = base_query.count()
        
        # Status counts
        status_counts = db.query(
            VisitRequest.status, func.count(VisitRequest.id)
        ).filter(
            VisitRequest.is_deleted.is_(False)
        )
        if tenant_id is not None:
            status_counts = status_counts.filter(VisitRequest.tenant_id == tenant_id)
        status_map = dict(status_counts.group_by(VisitRequest.status).all())

        # Today's count
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_query = base_query.filter(
            VisitRequest.scheduled_start_time >= today_start,
            VisitRequest.scheduled_start_time < today_end
        )
        today_requests = today_query.count()

        # Average approval time calculation (for approved requests)
        approved_requests = base_query.filter(
            VisitRequest.status == VisitRequestStatus.APPROVED,
            VisitRequest.approved_at.isnot(None)
        ).all()
        
        total_approval_minutes = 0.0
        if approved_requests:
            for req in approved_requests:
                if req.approved_at and req.created_at:
                    delta = (req.approved_at - req.created_at).total_seconds() / 60.0
                    total_approval_minutes += max(delta, 0.0)
            avg_approval_time = round(total_approval_minutes / len(approved_requests), 2)
        else:
            avg_approval_time = 0.0

        # Peak visiting hours calculation (grouped by hour of scheduled_start_time)
        peak_hours_query = db.query(
            extract('hour', VisitRequest.scheduled_start_time).label('hour'),
            func.count(VisitRequest.id).label('cnt')
        ).filter(
            VisitRequest.is_deleted.is_(False)
        )
        if tenant_id is not None:
            peak_hours_query = peak_hours_query.filter(VisitRequest.tenant_id == tenant_id)
        peak_hours_raw = peak_hours_query.group_by('hour').all()
        
        peak_visiting_hours = {}
        for hour_num, cnt in peak_hours_raw:
            if hour_num is not None:
                hour_str = f"{int(hour_num):02d}:00"
                peak_visiting_hours[hour_str] = cnt

        return {
            "total_requests": total_requests,
            "pending_requests": status_map.get(VisitRequestStatus.PENDING, 0),
            "approved_requests": status_map.get(VisitRequestStatus.APPROVED, 0),
            "rejected_requests": status_map.get(VisitRequestStatus.REJECTED, 0),
            "cancelled_requests": status_map.get(VisitRequestStatus.CANCELLED, 0),
            "checked_in_requests": status_map.get(VisitRequestStatus.CHECKED_IN, 0),
            "checked_out_requests": status_map.get(VisitRequestStatus.CHECKED_OUT, 0),
            "completed_requests": status_map.get(VisitRequestStatus.COMPLETED, 0),
            "expired_requests": status_map.get(VisitRequestStatus.EXPIRED, 0),
            "today_requests": today_requests,
            "average_approval_time_minutes": avg_approval_time,
            "peak_visiting_hours": peak_visiting_hours
        }

    @staticmethod
    def get_calendar_events(
        db: Session, 
        tenant_id: Optional[int] = None, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[VisitRequest]:
        """
        Retrieve requests for calendar representation within optional date range.
        """
        query = db.query(VisitRequest).filter(VisitRequest.is_deleted.is_(False))
        if tenant_id is not None:
            query = query.filter(VisitRequest.tenant_id == tenant_id)
        if start_date:
            query = query.filter(VisitRequest.scheduled_start_time >= start_date)
        if end_date:
            query = query.filter(VisitRequest.scheduled_start_time <= end_date)
        return query.order_by(VisitRequest.scheduled_start_time.asc()).all()

    @staticmethod
    def create(db: Session, request_entity: VisitRequest) -> VisitRequest:
        """
        Persist a new VisitRequest entity.
        """
        db.add(request_entity)
        db.commit()
        db.refresh(request_entity)
        return request_entity

    @staticmethod
    def update(db: Session, request_entity: VisitRequest) -> VisitRequest:
        """
        Save changes to an existing VisitRequest entity.
        """
        db.commit()
        db.refresh(request_entity)
        return request_entity

    @staticmethod
    def delete(db: Session, request_entity: VisitRequest, deleted_by: Optional[int] = None) -> VisitRequest:
        """
        Soft delete a VisitRequest entity.
        """
        request_entity.is_deleted = True
        request_entity.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        request_entity.deleted_by = deleted_by
        db.commit()
        db.refresh(request_entity)
        return request_entity

    @staticmethod
    def restore(db: Session, request_entity: VisitRequest) -> VisitRequest:
        """
        Restore a soft-deleted VisitRequest entity.
        """
        request_entity.is_deleted = False
        request_entity.deleted_at = None
        request_entity.deleted_by = None
        db.commit()
        db.refresh(request_entity)
        return request_entity
