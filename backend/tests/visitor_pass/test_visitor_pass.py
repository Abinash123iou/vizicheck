from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import pytest
from database.session import SessionLocal, engine
from database.base import Base

import app.models  # Ensure all SQLAlchemy models are registered
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.role import Role
from app.models.visitor import Visitor
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.checkin import CheckIn, ScanLog, GateEventHistory


@pytest.fixture(autouse=True, scope="function")
def cleanup_passes():
    """Ensure clean database state for pass tests."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        db.query(ScanLog).delete()
        db.query(GateEventHistory).delete()
        db.query(CheckIn).delete()
        db.query(VisitorPass).delete()
        db.query(VisitRequest).delete()
        db.commit()
    finally:
        db.close()

from app.schemas.pass_schema import GeneratePassRequest, RevokePassRequest, UpdatePassRequest
from app.services.pass_service import PassService
from app.services.qr_service import QRService
from app.core.exceptions import ConflictException, ValidationException
from background_jobs.pass_expiration_scheduler import run_pass_expiration_check


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def super_admin_user(db: Session):
    role = db.query(Role).filter_by(name="SUPER_ADMIN").first()
    user = db.query(User).filter_by(email="admin@vizicheck.com").first()
    if not user:
        user = User(
            role_id=role.id if role else 1,
            first_name="Super",
            last_name="Admin",
            email="admin@vizicheck.com",
            password_hash="hashed_password",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def sample_tenant(db: Session):
    tenant = db.query(Tenant).filter_by(code="TEN-TESTPASS").first()
    if not tenant:
        tenant = Tenant(
            name="Test Pass Org",
            slug="test-pass-org",
            code="TEN-TESTPASS",
            contact_person="Test Contact",
            contact_email="contact@testpass.com",
            status=TenantStatus.ACTIVE
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


@pytest.fixture
def approved_visit_request(db: Session, sample_tenant: Tenant, super_admin_user: User):
    visitor = db.query(Visitor).filter_by(email="pass.visitor@example.com").first()
    if not visitor:
        visitor = Visitor(
            tenant_id=sample_tenant.id,
            visitor_code=f"VIS-{int(datetime.now().timestamp())}-1",
            first_name="PassTest",
            last_name="Visitor",
            email="pass.visitor@example.com",
            phone="+1234567890",
            company="Pass Vendor Inc"
        )
        db.add(visitor)
        db.commit()
        db.refresh(visitor)

    now = datetime.now()
    req = VisitRequest(
        tenant_id=sample_tenant.id,
        request_code=f"VR-TEST-{int(now.timestamp())}",
        visitor_id=visitor.id,
        host_id=super_admin_user.id,
        purpose="Pass Test Business",
        scheduled_start_time=now,
        scheduled_end_time=now + timedelta(hours=4),
        status=VisitRequestStatus.APPROVED,
        created_by=super_admin_user.id
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req



def test_generate_pass_code_and_jwt_claims(db: Session, super_admin_user: User, approved_visit_request: VisitRequest):
    """
    Test pass generation: code format, active status, JWT claims breakdown.
    """
    pass_dto = PassService.generate_pass(
        db=db,
        current_user=super_admin_user,
        visit_request_id=approved_visit_request.id,
        request_data=GeneratePassRequest(tenant_id=approved_visit_request.tenant_id)
    )

    assert pass_dto.id is not None
    assert pass_dto.pass_code.startswith(f"VP-{datetime.now().year}-")
    assert pass_dto.status == PassStatus.ACTIVE
    assert pass_dto.latest_qr_version == 1
    assert pass_dto.active_qr is not None
    assert pass_dto.active_qr.token_type == "VISITOR_PASS"
    assert pass_dto.active_qr.iss == "ViziCheck"
    assert pass_dto.active_qr.aud == "GateScanner"
    assert pass_dto.active_qr.sub == pass_dto.uuid
    assert pass_dto.active_qr.visitor_id == approved_visit_request.visitor_id


def test_prevent_duplicate_pass_generation(db: Session, super_admin_user: User, approved_visit_request: VisitRequest):
    """
    Test duplicate pass generation returns 409 Conflict.
    """
    # First generation
    PassService.generate_pass(
        db=db,
        current_user=super_admin_user,
        visit_request_id=approved_visit_request.id,
        request_data=GeneratePassRequest(tenant_id=approved_visit_request.tenant_id)
    )

    # Second generation should raise ConflictException
    caught = False
    try:
        PassService.generate_pass(
            db=db,
            current_user=super_admin_user,
            visit_request_id=approved_visit_request.id,
            request_data=GeneratePassRequest(tenant_id=approved_visit_request.tenant_id)
        )
    except ConflictException as e:
        caught = True
        assert e.status_code == 409
        assert "Pass Already Exists" in e.message

    assert caught is True


def test_qr_token_regeneration(db: Session, super_admin_user: User, approved_visit_request: VisitRequest):
    """
    Test QR regeneration increments version and deactivates old token.
    """
    pass_dto = PassService.generate_pass(
        db=db,
        current_user=super_admin_user,
        visit_request_id=approved_visit_request.id,
        request_data=GeneratePassRequest(tenant_id=approved_visit_request.tenant_id)
    )
    
    new_qr = PassService.regenerate_qr_token(db, super_admin_user, pass_id=pass_dto.id)

    assert new_qr.version == 2
    assert new_qr.is_active is True

    updated_pass = PassService.get_pass_by_id(db, super_admin_user, pass_id=pass_dto.id)
    assert updated_pass.latest_qr_version == 2


def test_revoke_pass(db: Session, super_admin_user: User, approved_visit_request: VisitRequest):
    """
    Test pass revocation transitions status to REVOKED and deactivates QR tokens.
    """
    pass_dto = PassService.generate_pass(
        db=db,
        current_user=super_admin_user,
        visit_request_id=approved_visit_request.id,
        request_data=GeneratePassRequest(tenant_id=approved_visit_request.tenant_id)
    )
    
    revoked_dto = PassService.revoke_pass(
        db=db,
        current_user=super_admin_user,
        pass_id=pass_dto.id,
        revocation_data=RevokePassRequest(revocation_reason="Security Concern")
    )

    assert revoked_dto.status == PassStatus.REVOKED
    assert revoked_dto.revocation_reason == "Security Concern"
    assert len(revoked_dto.status_history) >= 2
    assert revoked_dto.status_history[-1].new_status == PassStatus.REVOKED



def test_pass_expiration_background_scheduler(db: Session, sample_tenant: Tenant, super_admin_user: User):
    """
    Test background pass expiration scheduler automatically expires passes past valid_until.
    """
    visitor = db.query(Visitor).filter_by(email="expired.visitor@example.com").first()
    if not visitor:
        visitor = Visitor(
            tenant_id=sample_tenant.id,
            visitor_code=f"VIS-{int(datetime.now().timestamp())}-2",
            first_name="Expired",
            last_name="Visitor",
            email="expired.visitor@example.com",
            phone="+1234567899"
        )
        db.add(visitor)
        db.commit()
        db.refresh(visitor)

    past_start = datetime.now() - timedelta(hours=5)
    past_until = datetime.now() - timedelta(hours=1)

    req = VisitRequest(
        tenant_id=sample_tenant.id,
        request_code=f"VR-EXP-{int(datetime.now().timestamp())}",
        visitor_id=visitor.id,
        host_id=super_admin_user.id,
        purpose="Expired Test",
        scheduled_start_time=past_start,
        scheduled_end_time=past_until,
        status=VisitRequestStatus.APPROVED,
        created_by=super_admin_user.id
    )
    db.add(req)
    db.commit()

    past_pass = VisitorPass(
        tenant_id=sample_tenant.id,
        visit_request_id=req.id,
        visitor_id=visitor.id,
        host_id=super_admin_user.id,
        pass_code=f"VP-TESTEXP-{int(datetime.now().timestamp())}",
        status=PassStatus.ACTIVE,
        valid_from=past_start,
        valid_until=past_until,
        created_by=super_admin_user.id
    )
    db.add(past_pass)
    db.commit()
    db.refresh(past_pass)

    expired_count = run_pass_expiration_check(db)
    assert expired_count >= 1

    db.refresh(past_pass)
    assert past_pass.status == PassStatus.EXPIRED
