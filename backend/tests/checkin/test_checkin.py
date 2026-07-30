from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.session import SessionLocal, engine
from database.base import Base
import app.models  # Ensure all SQLAlchemy models are registered

# Ensure database tables exist
Base.metadata.create_all(bind=engine)


from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.role import Role
from app.models.visitor import Visitor, VisitorStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.checkin import CheckIn, CheckInStatus, ScanLog, GateEventHistory, GateVerificationStatus
from app.schemas.pass_schema import GeneratePassRequest
from app.schemas.checkin_schema import (
    QRCheckInRequest,
    ManualCheckInRequest,
    QRCheckOutRequest,
    ManualCheckOutRequest,
    UndoCheckInRequest,
    CheckInPaginationRequest,
    GateDeviceMeta
)
from app.services.pass_service import PassService
from app.services.checkin_service import CheckInService
from app.core.exceptions import ValidationException, ConflictException
from background_jobs.checkin_cleanup_scheduler import run_overdue_checkin_cleanup


def get_test_tenant(db: Session):
    tenant = db.query(Tenant).filter_by(code="TEN-GATECHECK").first()
    if not tenant:
        tenant = Tenant(
            name="Gate Check Tenant",
            slug="gate-check-tenant",
            code="TEN-GATECHECK",
            contact_person="Gate Admin",
            contact_email="gate@tenant.com",
            status=TenantStatus.ACTIVE
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def get_test_super_admin(db: Session):
    tenant = get_test_tenant(db)
    role = db.query(Role).filter_by(name="SUPER_ADMIN").first()
    user = db.query(User).filter_by(email="admin.checkin@vizicheck.com").first()
    if not user:
        user = User(
            role_id=role.id if role else 1,
            first_name="CheckinAdmin",
            last_name="Super",
            email="admin.checkin@vizicheck.com",
            password_hash="hashed_pwd",
            is_active=True,
            tenant_id=tenant.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user



def setup_approved_pass(db: Session, tenant: Tenant, admin: User):
    """
    Helper creating visitor, approved visit request, and active pass with QR token.
    """
    import uuid
    uid = str(uuid.uuid4())[:8]
    visitor = Visitor(
        tenant_id=tenant.id,
        visitor_code=f"VIS-GATE-{uid}",
        first_name="GateVisitor",
        last_name="Test",
        email=f"visitor.{uid}@gate.com",
        phone=f"+1999{int(datetime.utcnow().timestamp()) % 100000}{uid[:4]}",
        status=VisitorStatus.ACTIVE
    )
    db.add(visitor)
    db.commit()

    now = datetime.utcnow()
    visit_request = VisitRequest(
        tenant_id=tenant.id,
        request_code=f"REQ-GATE-{uid}",
        visitor_id=visitor.id,
        host_id=admin.id,
        purpose="Gate Check-In Testing",
        department="Engineering",
        scheduled_start_time=now - timedelta(minutes=30),
        scheduled_end_time=now + timedelta(hours=2),
        status=VisitRequestStatus.APPROVED,
        approved_by=admin.id,
        approved_at=now
    )
    db.add(visit_request)
    db.commit()


    pass_dto = PassService.generate_pass(
        db=db,
        current_user=admin,
        visit_request_id=visit_request.id,
        request_data=GeneratePassRequest(notes="Test pass for gate security")
    )
    
    visitor_pass = db.query(VisitorPass).filter(VisitorPass.id == pass_dto.id).first()
    qr_token = pass_dto.active_qr.token if pass_dto.active_qr else ""

    return visitor_pass, qr_token, visit_request, visitor


def test_qr_scan_checkin_and_checkout_flow():
    """
    End-to-end test of QR scan check-in and check-out with duration calculation.
    """
    db = SessionLocal()
    try:
        admin = get_test_super_admin(db)
        tenant = get_test_tenant(db)
        visitor_pass, qr_token, visit_request, visitor = setup_approved_pass(db, tenant, admin)

        # 1. Execute Scan Check-In
        device_meta = GateDeviceMeta(
            gate_device_id="DEV-GATE-NORTH",
            scanner_name="North Gate Scanner",
            gate_name="North Gate"
        )
        req = QRCheckInRequest(qr_token=qr_token, device_meta=device_meta, notes="Checkin test")
        checkin_dto = CheckInService.scan_checkin(db=db, current_user=admin, request_data=req)

        assert checkin_dto.id is not None
        assert checkin_dto.status == CheckInStatus.CHECKED_IN
        assert checkin_dto.gate_device_id == "DEV-GATE-NORTH"
        assert checkin_dto.gate_name == "North Gate"
        assert checkin_dto.verification_method == "QR_SCAN"

        # Verify database statuses updated
        db.refresh(visitor_pass)
        db.refresh(visit_request)
        assert visitor_pass.status == PassStatus.USED
        assert visit_request.status == VisitRequestStatus.CHECKED_IN

        # 2. Execute Scan Check-Out
        checkout_req = QRCheckOutRequest(qr_token=qr_token, device_meta=device_meta, notes="Checkout test")
        checkout_dto = CheckInService.scan_checkout(db=db, current_user=admin, request_data=checkout_req)

        assert checkout_dto.status == CheckInStatus.CHECKED_OUT
        assert checkout_dto.checkout_time is not None
        assert checkout_dto.visit_duration_minutes is not None
        assert checkout_dto.visit_duration_seconds is not None

        db.refresh(visitor_pass)
        db.refresh(visit_request)
        assert visitor_pass.status == PassStatus.COMPLETED
        assert visit_request.status == VisitRequestStatus.COMPLETED

    finally:
        db.close()


def test_manual_checkin_and_checkout_flow():
    """
    Test guard manual check-in and manual check-out override flow.
    """
    db = SessionLocal()
    try:
        admin = get_test_super_admin(db)
        tenant = get_test_tenant(db)
        visitor_pass, qr_token, visit_request, visitor = setup_approved_pass(db, tenant, admin)

        # Manual Check-In
        manual_in_req = ManualCheckInRequest(
            pass_code=visitor_pass.pass_code,
            reason="Visitor phone battery died - Security manual check-in",
            notes="Physical ID verified"
        )
        checkin_dto = CheckInService.manual_checkin(db=db, current_user=admin, request_data=manual_in_req)

        assert checkin_dto.is_manual_checkin is True
        assert checkin_dto.manual_checkin_reason == "Visitor phone battery died - Security manual check-in"
        assert checkin_dto.verification_method == "MANUAL"

        # Manual Check-Out
        manual_out_req = ManualCheckOutRequest(
            checkin_id=checkin_dto.id,
            reason="Lost QR pass on exit - Security manual checkout"
        )
        checkout_dto = CheckInService.manual_checkout(db=db, current_user=admin, request_data=manual_out_req)

        assert checkout_dto.is_manual_checkout is True
        assert checkout_dto.manual_checkout_reason == "Lost QR pass on exit - Security manual checkout"
        assert checkout_dto.status == CheckInStatus.CHECKED_OUT

    finally:
        db.close()


def test_duplicate_checkin_prevention():
    """
    Ensure attempting to scan check-in twice for the same pass throws ConflictException.
    """
    db = SessionLocal()
    try:
        admin = get_test_super_admin(db)
        tenant = get_test_tenant(db)
        visitor_pass, qr_token, visit_request, visitor = setup_approved_pass(db, tenant, admin)

        req = QRCheckInRequest(qr_token=qr_token)
        CheckInService.scan_checkin(db=db, current_user=admin, request_data=req)

        # Second scan attempt should fail
        try:
            CheckInService.scan_checkin(db=db, current_user=admin, request_data=req)
            assert False, "Should have raised ConflictException for duplicate check-in"
        except ConflictException as ce:
            assert "ALREADY checked in" in str(ce) or "Duplicate" in str(ce)

    finally:
        db.close()


def test_invalid_qr_logs_scan_failure():
    """
    Ensure scanning an invalid/forged QR token logs a FAILED record in scan_logs.
    """
    db = SessionLocal()
    try:
        admin = get_test_super_admin(db)
        bogus_token = "INVALID_FORGED_JWT_TOKEN_123"

        req = QRCheckInRequest(qr_token=bogus_token)
        try:
            CheckInService.scan_checkin(db=db, current_user=admin, request_data=req)
            assert False, "Should fail on invalid QR token"
        except ValidationException:
            pass

        # Check scan logs for failure
        logs = CheckInService.list_scan_logs(db=db, current_user=admin, limit=50)
        target_log = next((l for l in logs if l.qr_token == bogus_token), None)
        assert target_log is not None
        assert target_log.scan_result in [GateVerificationStatus.INVALID_SIGNATURE, GateVerificationStatus.UNKNOWN_QR, GateVerificationStatus.FAILED]


    finally:
        db.close()


def test_live_dashboard_and_active_visitors():
    """
    Test live occupancy dashboard metrics and active visitors endpoint.
    """
    db = SessionLocal()
    try:
        admin = get_test_super_admin(db)
        tenant = get_test_tenant(db)
        visitor_pass, qr_token, visit_request, visitor = setup_approved_pass(db, tenant, admin)

        # Perform Check-In
        req = QRCheckInRequest(qr_token=qr_token)
        CheckInService.scan_checkin(db=db, current_user=admin, request_data=req)

        # Check Active Visitors
        params = CheckInPaginationRequest(page=1, page_size=10)
        active_res = CheckInService.get_active_visitors(db=db, current_user=admin, params=params)
        assert active_res.total_records >= 1


        # Check Live Dashboard
        dashboard = CheckInService.get_live_dashboard(db=db, current_user=current_user_admin(admin))
        assert dashboard.visitors_inside >= 1
        assert dashboard.current_occupancy >= 1

    finally:
        db.close()


def current_user_admin(user: User):
    return user


def test_undo_checkin_flow():
    """
    Test admin undoing a check-in record.
    """
    db = SessionLocal()
    try:
        admin = get_test_super_admin(db)
        tenant = get_test_tenant(db)
        visitor_pass, qr_token, visit_request, visitor = setup_approved_pass(db, tenant, admin)

        req = QRCheckInRequest(qr_token=qr_token)
        checkin_dto = CheckInService.scan_checkin(db=db, current_user=admin, request_data=req)

        # Undo Check-In
        undo_req = UndoCheckInRequest(reason="Accidental scan by guard on wrong visitor")
        undone_dto = CheckInService.undo_checkin(db=db, current_user=admin, checkin_id=checkin_dto.id, request_data=undo_req)

        assert undone_dto.is_undone is True
        assert undone_dto.status == CheckInStatus.UNDONE

        db.refresh(visitor_pass)
        db.refresh(visit_request)
        assert visitor_pass.status == PassStatus.ACTIVE
        assert visit_request.status == VisitRequestStatus.APPROVED

    finally:
        db.close()


def test_overdue_checkin_cleanup_scheduler():
    """
    Test background overstay cleanup scheduler execution.
    """
    db = SessionLocal()
    try:
        count = run_overdue_checkin_cleanup(db=db)
        assert count >= 0
    finally:
        db.close()
