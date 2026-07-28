import os
import sys
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from main import app as fastapi_app
from config import settings
from database.session import SessionLocal, engine
from database.base import Base
import app.models  # Ensure all models are registered
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.visitor import Visitor, VisitorStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus

client = TestClient(fastapi_app)


@pytest.fixture(autouse=True, scope="function")
def cleanup_visit_requests():
    """Ensure clean table state for visit requests before each test."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        db.query(VisitRequest).delete()
        db.commit()
    finally:
        db.close()


def get_super_admin_token() -> str:
    """Helper to acquire valid Super Admin access token."""
    res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    if res.status_code != 200:
        pytest.fail(f"Failed to authenticate Super Admin: {res.text}")
    return res.json()["data"]["access_token"]


def get_or_create_test_tenant() -> Tenant:
    """Helper to get or create a valid tenant entity for testing."""
    db: Session = SessionLocal()
    try:
        tenant = db.query(Tenant).filter_by(code="TEN-888888").first()
        if not tenant:
            tenant = Tenant(
                name="Request Test Organization",
                code="TEN-888888",
                slug="request-test-org",
                contact_person="Request Tester",
                contact_email="tester@requesttest.com"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        return tenant
    finally:
        db.close()


def get_or_create_test_visitor(tenant_id: int, blacklisted: bool = False) -> Visitor:
    """Helper to create a visitor entity for request testing."""
    db: Session = SessionLocal()
    try:
        suffix = "blacklisted" if blacklisted else "active"
        phone = "+1999888001" if blacklisted else "+1999888002"
        visitor = db.query(Visitor).filter_by(tenant_id=tenant_id, phone=phone).first()
        if not visitor:
            visitor = Visitor(
                tenant_id=tenant_id,
                visitor_code=f"VIS-REQ-{suffix}",
                first_name="ReqVisitor",
                last_name=suffix.capitalize(),
                phone=phone,
                email=f"visitor_{suffix}@test.com",
                blacklisted=blacklisted,
                blacklist_reason="Security violation" if blacklisted else None,
                status=VisitorStatus.ACTIVE
            )
            db.add(visitor)
            db.commit()
            db.refresh(visitor)
        return visitor
    finally:
        db.close()


def get_or_create_test_host(tenant_id: int, active: bool = True) -> User:
    """Helper to create a host employee user."""
    db: Session = SessionLocal()
    try:
        email = f"host_{'active' if active else 'inactive'}@test.com"
        host = db.query(User).filter_by(email=email).first()
        if not host:
            role = db.query(Role).first()
            host = User(
                tenant_id=tenant_id,
                role_id=role.id if role else 1,
                first_name="Host",
                last_name="Employee",
                email=email,
                password_hash="hashed_pw",
                is_active=active
            )
            db.add(host)
            db.commit()
            db.refresh(host)
        return host
    finally:
        db.close()


def test_create_visit_request_success():
    """Verify creating a valid visit request returns 201 with generated request_code."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    visitor = get_or_create_test_visitor(tenant.id, blacklisted=False)
    host = get_or_create_test_host(tenant.id, active=True)

    start_time = (datetime.now() + timedelta(days=1)).isoformat()
    end_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat()

    payload = {
        "tenant_id": tenant.id,
        "visitor_id": visitor.id,
        "host_id": host.id,
        "purpose": "Vendor Operations Meeting",
        "department": "Engineering",
        "scheduled_start_time": start_time,
        "scheduled_end_time": end_time,
        "additional_visitors_count": 1,
        "notes": "Bringing laptop for presentation"
    }

    res = client.post(
        "/api/v1/visit-requests",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["status"] == "PENDING"
    assert data["request_code"].startswith("VR-")
    assert data["visitor_id"] == visitor.id
    assert data["host_id"] == host.id
    assert data["purpose"] == "Vendor Operations Meeting"


def test_create_visit_request_blacklisted_visitor_fails():
    """Verify creating a visit request for a blacklisted visitor fails with validation error (422)."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    blacklisted_visitor = get_or_create_test_visitor(tenant.id, blacklisted=True)
    host = get_or_create_test_host(tenant.id, active=True)

    start_time = (datetime.now() + timedelta(days=2)).isoformat()
    end_time = (datetime.now() + timedelta(days=2, hours=2)).isoformat()

    payload = {
        "tenant_id": tenant.id,
        "visitor_id": blacklisted_visitor.id,
        "host_id": host.id,
        "purpose": "Personal Visit",
        "scheduled_start_time": start_time,
        "scheduled_end_time": end_time
    }

    res = client.post(
        "/api/v1/visit-requests",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code in [400, 422]
    assert "blacklisted" in res.json()["message"].lower()


def test_create_visit_request_inactive_host_fails():
    """Verify creating a visit request with an inactive host employee fails (422)."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    visitor = get_or_create_test_visitor(tenant.id, blacklisted=False)
    inactive_host = get_or_create_test_host(tenant.id, active=False)

    start_time = (datetime.now() + timedelta(days=3)).isoformat()
    end_time = (datetime.now() + timedelta(days=3, hours=2)).isoformat()

    payload = {
        "tenant_id": tenant.id,
        "visitor_id": visitor.id,
        "host_id": inactive_host.id,
        "purpose": "Consultation",
        "scheduled_start_time": start_time,
        "scheduled_end_time": end_time
    }

    res = client.post(
        "/api/v1/visit-requests",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code in [400, 422]
    assert "inactive" in res.json()["message"].lower()


def test_create_visit_request_invalid_time_range_fails():
    """Verify end time before start time raises validation error (422)."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    visitor = get_or_create_test_visitor(tenant.id, blacklisted=False)
    host = get_or_create_test_host(tenant.id, active=True)

    start_time = (datetime.now() + timedelta(days=4, hours=2)).isoformat()
    end_time = (datetime.now() + timedelta(days=4)).isoformat()  # End before start

    payload = {
        "tenant_id": tenant.id,
        "visitor_id": visitor.id,
        "host_id": host.id,
        "purpose": "Invalid Window",
        "scheduled_start_time": start_time,
        "scheduled_end_time": end_time
    }

    res = client.post(
        "/api/v1/visit-requests",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code in [400, 422]
    assert "scheduled end time must be after" in res.json()["message"].lower()


def test_approve_visit_request_workflow():
    """Verify approving a PENDING visit request transitions status to APPROVED and records approval notes."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    visitor = get_or_create_test_visitor(tenant.id, blacklisted=False)
    host = get_or_create_test_host(tenant.id, active=True)

    # 1. Create request
    start_time = (datetime.now() + timedelta(days=5)).isoformat()
    end_time = (datetime.now() + timedelta(days=5, hours=3)).isoformat()

    res_create = client.post(
        "/api/v1/visit-requests",
        json={
            "tenant_id": tenant.id,
            "visitor_id": visitor.id,
            "host_id": host.id,
            "purpose": "Approval Test Visit",
            "scheduled_start_time": start_time,
            "scheduled_end_time": end_time
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_create.status_code == 201, res_create.text
    request_id = res_create.json()["data"]["id"]

    # 2. Approve via POST /approve
    res_approve = client.post(
        f"/api/v1/visit-requests/{request_id}/approve",
        json={"approval_notes": "Approved for VIP access"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res_approve.status_code == 200, res_approve.text
    data = res_approve.json()["data"]
    assert data["status"] == "APPROVED"
    assert data["approval_notes"] == "Approved for VIP access"
    assert data["approved_at"] is not None


def test_reject_visit_request_workflow():
    """Verify rejecting a visit request records rejection_reason and transitions status to REJECTED."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    visitor = get_or_create_test_visitor(tenant.id, blacklisted=False)
    host = get_or_create_test_host(tenant.id, active=True)

    start_time = (datetime.now() + timedelta(days=6)).isoformat()
    end_time = (datetime.now() + timedelta(days=6, hours=1)).isoformat()

    res_create = client.post(
        "/api/v1/visit-requests",
        json={
            "tenant_id": tenant.id,
            "visitor_id": visitor.id,
            "host_id": host.id,
            "purpose": "Rejection Test Visit",
            "scheduled_start_time": start_time,
            "scheduled_end_time": end_time
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_create.status_code == 201, res_create.text
    request_id = res_create.json()["data"]["id"]

    # Reject via PATCH /reject
    res_reject = client.patch(
        f"/api/v1/visit-requests/{request_id}/reject",
        json={"rejection_reason": "Host is unavailable during requested hours"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res_reject.status_code == 200, res_reject.text
    data = res_reject.json()["data"]
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Host is unavailable during requested hours"
    assert data["rejected_at"] is not None


def test_cancel_visit_request_workflow():
    """Verify cancelling an approved visit request records cancellation_reason and updates status to CANCELLED."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()
    visitor = get_or_create_test_visitor(tenant.id, blacklisted=False)
    host = get_or_create_test_host(tenant.id, active=True)

    start_time = (datetime.now() + timedelta(days=7)).isoformat()
    end_time = (datetime.now() + timedelta(days=7, hours=2)).isoformat()

    res_create = client.post(
        "/api/v1/visit-requests",
        json={
            "tenant_id": tenant.id,
            "visitor_id": visitor.id,
            "host_id": host.id,
            "purpose": "Cancellation Test Visit",
            "scheduled_start_time": start_time,
            "scheduled_end_time": end_time
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_create.status_code == 201, res_create.text
    request_id = res_create.json()["data"]["id"]

    res_cancel = client.post(
        f"/api/v1/visit-requests/{request_id}/cancel",
        json={"cancellation_reason": "Meeting rescheduled by client"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res_cancel.status_code == 200, res_cancel.text
    data = res_cancel.json()["data"]
    assert data["status"] == "CANCELLED"
    assert data["cancellation_reason"] == "Meeting rescheduled by client"


def test_list_statistics_calendar_and_export():
    """Verify list, statistics, calendar, and CSV export endpoints return valid data."""
    token = get_super_admin_token()

    # List requests
    res_list = client.get("/api/v1/visit-requests", headers={"Authorization": f"Bearer {token}"})
    assert res_list.status_code == 200
    assert "items" in res_list.json()["data"]

    # Statistics
    res_stats = client.get("/api/v1/visit-requests/statistics", headers={"Authorization": f"Bearer {token}"})
    assert res_stats.status_code == 200
    stats = res_stats.json()["data"]
    assert "total_requests" in stats
    assert "pending_requests" in stats
    assert "peak_visiting_hours" in stats

    # Calendar
    res_cal = client.get("/api/v1/visit-requests/calendar", headers={"Authorization": f"Bearer {token}"})
    assert res_cal.status_code == 200
    assert "days" in res_cal.json()["data"]

    # CSV Export
    res_export = client.get("/api/v1/visit-requests/export", headers={"Authorization": f"Bearer {token}"})
    assert res_export.status_code == 200
    assert res_export.headers["content-type"].startswith("text/csv")
    assert "Request Code" in res_export.text
