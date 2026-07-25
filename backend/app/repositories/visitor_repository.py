from datetime import datetime, date, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.models.visitor import Visitor, VisitorStatus, VerificationStatus, VerificationMethod
from app.models.tenant import Tenant
from app.repositories.specifications.visitor_filters import VisitorFilters

class VisitorRepository:
    """
    Database access layer for Visitor entities incorporating tenant boundary filtering,
    soft deletion, dynamic specs, and statistics collection.
    """

    @staticmethod
    def generate_visitor_code(db: Session, tenant_id: int) -> str:
        """
        Generate tenant-aware sequential visitor code (e.g. VIS-TEN-000001-000001).
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        tenant_code = tenant.code if tenant and tenant.code else f"TEN-{tenant_id:06d}"
        
        max_id = db.query(func.max(Visitor.id)).scalar() or 0
        next_seq = max_id + 1
        return f"VIS-{tenant_code}-{next_seq:06d}"


    @staticmethod
    def find_by_id(
        db: Session, 
        visitor_id: int, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[Visitor]:
        """
        Find visitor by primary key ID with optional tenant isolation.
        """
        query = db.query(Visitor).filter(Visitor.id == visitor_id)
        if tenant_id is not None:
            query = query.filter(Visitor.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(Visitor.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_code(
        db: Session, 
        visitor_code: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[Visitor]:
        """
        Find visitor by tenant-aware visitor code.
        """
        query = db.query(Visitor).filter(Visitor.visitor_code == visitor_code.strip())
        if tenant_id is not None:
            query = query.filter(Visitor.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(Visitor.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_phone(
        db: Session, 
        phone: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[Visitor]:
        """
        Find visitor by phone number within optional tenant boundary.
        """
        query = db.query(Visitor).filter(Visitor.phone == phone.strip())
        if tenant_id is not None:
            query = query.filter(Visitor.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(Visitor.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_email(
        db: Session, 
        email: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[Visitor]:
        """
        Find visitor by email address within optional tenant boundary.
        """
        query = db.query(Visitor).filter(Visitor.email.ilike(email.strip()))
        if tenant_id is not None:
            query = query.filter(Visitor.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(Visitor.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def find_by_gov_id(
        db: Session, 
        government_id_number: str, 
        tenant_id: Optional[int] = None, 
        include_deleted: bool = False
    ) -> Optional[Visitor]:
        """
        Find visitor by government ID number within optional tenant boundary.
        """
        query = db.query(Visitor).filter(Visitor.government_id_number == government_id_number.strip())
        if tenant_id is not None:
            query = query.filter(Visitor.tenant_id == tenant_id)
        if not include_deleted:
            query = query.filter(Visitor.is_deleted.is_(False))
        return query.first()

    @staticmethod
    def create(db: Session, visitor_data: dict, creator_id: Optional[int] = None) -> Visitor:
        """
        Persist a new Visitor record. Generates tenant-aware code if missing.
        """
        tenant_id = visitor_data.get("tenant_id")
        if "visitor_code" not in visitor_data or not visitor_data["visitor_code"]:
            visitor_data["visitor_code"] = VisitorRepository.generate_visitor_code(db, tenant_id)

        visitor = Visitor(**visitor_data, created_by=creator_id)
        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def update(
        db: Session, 
        visitor: Visitor, 
        update_data: dict, 
        updater_id: Optional[int] = None
    ) -> Visitor:
        """
        Update fields on an existing Visitor record.
        """
        for key, value in update_data.items():
            if hasattr(visitor, key) and value is not None:
                setattr(visitor, key, value)

        visitor.updated_by = updater_id
        visitor.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def soft_delete(db: Session, visitor: Visitor, deleter_id: Optional[int] = None) -> Visitor:
        """
        Soft delete a Visitor record.
        """
        visitor.delete()
        visitor.deleted_by = deleter_id
        visitor.updated_by = deleter_id
        visitor.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def restore(db: Session, visitor: Visitor, updater_id: Optional[int] = None) -> Visitor:
        """
        Restore soft-deleted Visitor record.
        """
        visitor.restore()
        visitor.deleted_by = None
        visitor.updated_by = updater_id
        visitor.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def verify_visitor(
        db: Session,
        visitor: Visitor,
        verification_method: VerificationMethod,
        verifier_id: int,
        notes: Optional[str] = None
    ) -> Visitor:
        """
        Set visitor verification state to VERIFIED.
        """
        visitor.verified = True
        visitor.verification_status = VerificationStatus.VERIFIED
        visitor.verification_method = verification_method
        visitor.verification_date = datetime.now(timezone.utc).replace(tzinfo=None)
        visitor.verified_by = verifier_id
        visitor.updated_by = verifier_id
        visitor.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if visitor.status == VisitorStatus.PENDING:
            visitor.status = VisitorStatus.VERIFIED
        if notes:
            visitor.notes = f"{visitor.notes}\n[Verification Note]: {notes}" if visitor.notes else f"[Verification Note]: {notes}"

        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def blacklist_visitor(
        db: Session,
        visitor: Visitor,
        blacklisted: bool,
        reason: Optional[str] = None,
        updater_id: Optional[int] = None
    ) -> Visitor:
        """
        Toggle blacklist status and update visitor status accordingly.
        """
        visitor.blacklisted = blacklisted
        if blacklisted:
            visitor.blacklist_reason = reason
            visitor.status = VisitorStatus.BLACKLISTED
        else:
            visitor.blacklist_reason = None
            visitor.status = VisitorStatus.ACTIVE

        visitor.updated_by = updater_id
        visitor.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def update_status(
        db: Session,
        visitor: Visitor,
        status: VisitorStatus,
        updater_id: Optional[int] = None
    ) -> Visitor:
        """
        Update general visitor status (ACTIVE, INACTIVE, etc.).
        """
        visitor.status = status
        visitor.updated_by = updater_id
        visitor.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        return visitor

    @staticmethod
    def list_visitors_paginated(
        db: Session,
        tenant_id: Optional[int] = None,
        search: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        government_id_number: Optional[str] = None,
        visitor_code: Optional[str] = None,
        status: Optional[VisitorStatus] = None,
        verified: Optional[bool] = None,
        blacklisted: Optional[bool] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        is_deleted: bool = False,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> Tuple[List[Visitor], int]:
        """
        Retrieve paginated visitors matching dynamic search and filter specifications.
        """
        base_query = db.query(Visitor)

        filtered_query = VisitorFilters.apply_filters(
            query=base_query,
            tenant_id=tenant_id,
            search=search,
            name=name,
            phone=phone,
            email=email,
            company=company,
            government_id_number=government_id_number,
            visitor_code=visitor_code,
            status=status,
            verified=verified,
            blacklisted=blacklisted,
            created_from=created_from,
            created_to=created_to,
            is_deleted=is_deleted
        )

        total_records = filtered_query.count()
        sorted_query = VisitorFilters.apply_sorting(filtered_query, sort_by=sort_by, order=order)

        offset = (page - 1) * page_size
        visitors = sorted_query.offset(offset).limit(page_size).all()

        return visitors, total_records

    @staticmethod
    def get_all_visitors_for_export(
        db: Session,
        tenant_id: Optional[int] = None,
        search: Optional[str] = None,
        status: Optional[VisitorStatus] = None,
        verified: Optional[bool] = None,
        blacklisted: Optional[bool] = None,
        is_deleted: bool = False
    ) -> List[Visitor]:
        """
        Retrieve all visitors for exporting to CSV.
        """
        base_query = db.query(Visitor)
        filtered_query = VisitorFilters.apply_filters(
            query=base_query,
            tenant_id=tenant_id,
            search=search,
            status=status,
            verified=verified,
            blacklisted=blacklisted,
            is_deleted=is_deleted
        )
        return VisitorFilters.apply_sorting(filtered_query).all()

    @staticmethod
    def get_statistics(db: Session, tenant_id: Optional[int] = None) -> Dict[str, int]:
        """
        Gather analytics statistics for visitor management dashboard.
        """
        base_query = db.query(Visitor).filter(Visitor.is_deleted.is_(False))
        if tenant_id is not None:
            base_query = base_query.filter(Visitor.tenant_id == tenant_id)

        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day)
        month_start = datetime(now.year, now.month, 1)

        total_visitors = base_query.count()
        active_visitors = base_query.filter(Visitor.status == VisitorStatus.ACTIVE).count()
        inactive_visitors = base_query.filter(Visitor.status == VisitorStatus.INACTIVE).count()
        blacklisted_visitors = base_query.filter(Visitor.blacklisted.is_(True)).count()
        verified_visitors = base_query.filter(Visitor.verified.is_(True)).count()
        pending_verification = base_query.filter(Visitor.verification_status == VerificationStatus.PENDING).count()
        today_visitors = base_query.filter(Visitor.created_at >= today_start).count()
        this_month_visitors = base_query.filter(Visitor.created_at >= month_start).count()
        
        # Returning visitors count: Visitors with duplicate phone numbers or prior visits
        subq = db.query(Visitor.phone).filter(Visitor.is_deleted.is_(False))
        if tenant_id is not None:
            subq = subq.filter(Visitor.tenant_id == tenant_id)
        dup_phones = subq.group_by(Visitor.phone).having(func.count(Visitor.id) > 1).all()
        returning_visitors = len(dup_phones)

        return {
            "total_visitors": total_visitors,
            "active_visitors": active_visitors,
            "inactive_visitors": inactive_visitors,
            "blacklisted_visitors": blacklisted_visitors,
            "verified_visitors": verified_visitors,
            "pending_verification_visitors": pending_verification,
            "today_visitors": today_visitors,
            "this_month_visitors": this_month_visitors,
            "returning_visitors": returning_visitors
        }
