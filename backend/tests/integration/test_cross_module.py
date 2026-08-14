import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from main import app
from app.core.security import create_access_token
from app.models import (
    User, Tenant, Role, Visitor, VisitRequest, VisitRequestStatus,
    VisitorPass, PassStatus, CheckIn, CheckInStatus, AuditLog, QRToken
)
from app.services.qr_service import QRService

client = TestClient(app)

@pytest.fixture
def cross_module_setup(db_session):
    role_admin = db_session.query(Role).filter_by(name="TENANT_ADMIN").first()
    role_host = db_session.query(Role).filter_by(name="HOST").first()

    tenant = db_session.query(Tenant).filter_by(code="CROSS_CORP").first()
    if not tenant:
        tenant = Tenant(name="CrossModule Corp", code="CROSS_CORP", domain="crossmodule.com", contact_person="Cross Contact", contact_email="contact@crossmodule.com")
        db_session.add(tenant)
        db_session.commit()

    admin = db_session.query(User).filter_by(email="admin@crossmodule.com").first()
    if not admin:
        admin = User(
            email="admin@crossmodule.com",
            first_name="Admin",
            last_name="Cross",
            password_hash="hash",
            is_active=True,
            tenant_id=tenant.id,
            role_id=role_admin.id
        )
        db_session.add(admin)

    host = db_session.query(User).filter_by(email="host@crossmodule.com").first()
    if not host:
        host = User(
            email="host@crossmodule.com",
            first_name="Host",
            last_name="Cross",
            password_hash="hash",
            is_active=True,
            tenant_id=tenant.id,
            role_id=role_host.id
        )
        db_session.add(host)

    db_session.commit()

    visitor = db_session.query(Visitor).filter_by(visitor_code="VIS-CROSS-01").first()
    if not visitor:
        visitor = Visitor(
            tenant_id=tenant.id,
            first_name="Alice",
            last_name="Visitor",
            visitor_code="VIS-CROSS-01",
            phone="+1555000111",
            email="alice@cross.com"
        )
        db_session.add(visitor)
        db_session.commit()

    admin_token = create_access_token(data={"sub": str(admin.id)})
    host_token = create_access_token(data={"sub": str(host.id)})

    return {
        "tenant": tenant,
        "admin": admin,
        "host": host,
        "visitor": visitor,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "host_headers": {"Authorization": f"Bearer {host_token}"}
    }


def test_rejected_visit_request_lifecycle(cross_module_setup, db_session):
    """
    Negative Workflow: Create Visit Request -> Reject -> Verify Pass is NOT generated.
    """
    headers = cross_module_setup["admin_headers"]
    host = cross_module_setup["host"]
    visitor = cross_module_setup["visitor"]

    now = datetime.now()
    start_time = (now + timedelta(hours=1)).isoformat()
    end_time = (now + timedelta(hours=3)).isoformat()

    req_payload = {
        "visitor_id": visitor.id,
        "host_id": host.id,
        "purpose": "Negative Test Rejection",
        "scheduled_start_time": start_time,
        "scheduled_end_time": end_time
    }
    create_res = client.post("/api/v1/visit-requests", json=req_payload, headers=headers)
    assert create_res.status_code == 201
    request_id = create_res.json()["data"]["id"]

    # Reject request
    reject_res = client.post(
        f"/api/v1/visit-requests/{request_id}/reject",
        json={"rejection_reason": "Security policy violation"},
        headers=headers
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["status"] == "REJECTED"

    # Verify attempting to generate pass for rejected request fails
    pass_gen_res = client.post(f"/api/v1/passes/generate/{request_id}", headers=headers)
    assert pass_gen_res.status_code in [400, 422]


def test_duplicate_checkin_rejection(cross_module_setup, db_session):
    """
    Negative Workflow: Approve Request -> Pass & QR -> Check-In -> Second Check-In fails.
    """
    headers = cross_module_setup["admin_headers"]
    host = cross_module_setup["host"]
    visitor = cross_module_setup["visitor"]

    now = datetime.now()
    start_time = (now + timedelta(minutes=5)).isoformat()
    end_time = (now + timedelta(hours=2)).isoformat()

    # 1. Create Visit Request
    req_res = client.post("/api/v1/visit-requests", json={
        "visitor_id": visitor.id,
        "host_id": host.id,
        "purpose": "Duplicate Checkin Test",
        "scheduled_start_time": start_time,
        "scheduled_end_time": end_time
    }, headers=headers)
    assert req_res.status_code == 201
    req_id = req_res.json()["data"]["id"]

    # 2. Approve Request (automatically generates Visitor Pass & QR Token)
    approve_res = client.post(f"/api/v1/visit-requests/{req_id}/approve", json={"approval_notes": "Approved"}, headers=headers)
    assert approve_res.status_code == 200

    # 3. Retrieve Auto-Generated Pass & QR
    passes_list = client.get(f"/api/v1/passes?visit_request_id={req_id}", headers=headers)
    assert passes_list.status_code == 200
    pass_data = passes_list.json()["data"]["items"][0]
    pass_id = pass_data["id"]
    pass_uuid = pass_data["uuid"]

    qr_info_res = client.get(f"/api/v1/passes/{pass_id}/qr", headers=headers)
    jwt_token = qr_info_res.json()["data"]["token"]
    raw_qr = f"VIZICHECK:PASS:{pass_uuid}:V1:{jwt_token}"

    # 4. First Check-In
    checkin_payload = {"qr_token": raw_qr, "gate_device_id": "GATE-01"}
    first_scan = client.post("/api/v1/checkin/scan", json=checkin_payload, headers=headers)
    assert first_scan.status_code == 201
    assert first_scan.json()["success"] is True

    # 5. Second Duplicate Check-In (Must fail because pass is already checked in)
    second_scan = client.post("/api/v1/checkin/scan", json=checkin_payload, headers=headers)
    assert second_scan.status_code in [400, 409, 422]
    assert second_scan.json()["success"] is False
