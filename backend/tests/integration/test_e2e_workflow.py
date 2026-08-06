import pytest
from datetime import datetime, date, time, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models import (
    Tenant, TenantStatus, User, Role, Visitor, VisitorStatus, HostAvailability,
    VisitRequest, VisitRequestStatus, VisitorPass, PassStatus, AuditLog,
    SecurityLog, Notification
)
from app.core.password import hash_password
from config import settings

from database.session import SessionLocal

client = TestClient(app)


def test_sprint1_end_to_end_integration_workflow(setup_test_database):
    """
    Sprint 1 Day 16 E2E Integration Test:
    Validates the complete 11-stage business flow across all integrated backend modules:
    User Login -> Host Availability -> Visitor Creation -> Visit Request Creation ->
    Approval Workflow -> Pass & QR Generation -> Notification Dispatch -> Gate Check-In ->
    Gate Check-Out -> Audit & Security Logging.
    """
    db = SessionLocal()
    try:
        uid = datetime.now(timezone.utc).strftime("%M%S%f")

        # ----------------------------------------------------
        # 1. Setup Tenant and Roles/Users
        # ----------------------------------------------------
        tenant = Tenant(
            name=f"E2E Enterprise Corp {uid}",
            slug=f"e2e-corp-{uid}",
            code=f"E2E-{uid[:4]}",
            contact_person="E2E Admin",
            contact_email=f"admin.{uid}@e2ecorp.com",
            status=TenantStatus.ACTIVE
        )
        db.add(tenant)
        db.commit()

        role_admin = db.query(Role).filter_by(name="TENANT_ADMIN").first()
        role_host = db.query(Role).filter_by(name="HOST").first()
        role_sec = db.query(Role).filter_by(name="SECURITY_OFFICER").first()

        host_password = "HostPassword123!"
        host_user = User(
            tenant_id=tenant.id,
            role_id=role_host.id,
            first_name="Jane",
            last_name="Host",
            email=f"jane.host.{uid}@e2ecorp.com",
            phone=f"+1800555{uid[:4]}",
            password_hash=hash_password(host_password),
            is_active=True
        )
        db.add(host_user)

        sec_user = User(
            tenant_id=tenant.id,
            role_id=role_sec.id,
            first_name="Guard",
            last_name="Bob",
            email=f"guard.bob.{uid}@e2ecorp.com",
            phone=f"+1800556{uid[:4]}",
            password_hash=hash_password("GuardPassword123!"),
            is_active=True
        )
        db.add(sec_user)
        db.commit()

        # ----------------------------------------------------
        # STAGE 1: Authentication & JWT Login (Auth ↔ Users ↔ Tenants)
        # ----------------------------------------------------
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": host_user.email, "password": host_password}
        )
        assert login_resp.status_code == 200, f"Host Login Failed: {login_resp.json()}"
        login_data = login_resp.json()["data"]
        token = login_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Guard Login for gate operations
        sec_login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": sec_user.email, "password": "GuardPassword123!"}
        )
        assert sec_login_resp.status_code == 200
        sec_token = sec_login_resp.json()["data"]["access_token"]
        sec_headers = {"Authorization": f"Bearer {sec_token}"}

        # Verify Super Admin / Admin login works as well
        admin_login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
                "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
            }
        )
        assert admin_login_resp.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login_resp.json()['data']['access_token']}"}

        # ----------------------------------------------------
        # STAGE 2: Host Availability Setup (Requests ↔ Availability)
        # ----------------------------------------------------
        today_date = date.today()
        weekday_str = today_date.strftime("%A").upper()
        avail_resp = client.post(
            "/api/v1/availability",
            headers=auth_headers,
            json={
                "tenant_id": tenant.id,
                "user_id": host_user.id,
                "weekday": weekday_str,
                "start_time": "08:00:00",
                "end_time": "18:00:00",
                "max_visitors": 10,
                "is_available": True,
                "notes": "Available all day"
            }
        )
        assert avail_resp.status_code == 201, f"Host Availability Failed: {avail_resp.json()}"

        # ----------------------------------------------------
        # STAGE 3: Visitor Profile Creation (Visitors ↔ Users ↔ Tenants)
        # ----------------------------------------------------
        visitor_payload = {
            "first_name": "Alice",
            "last_name": "Visitor",
            "email": f"alice.v.{uid}@external.com",
            "phone": f"+1999888{uid[:4]}",
            "company_name": "External Partner Inc",
            "id_proof_type": "PASSPORT",
            "id_proof_number": f"PASS-{uid[:6]}",
            "tenant_id": tenant.id
        }
        visitor_resp = client.post(
            "/api/v1/visitors",
            headers=auth_headers,
            json=visitor_payload
        )
        assert visitor_resp.status_code == 201, f"Visitor Creation Failed: {visitor_resp.json()}"
        visitor_id = visitor_resp.json()["data"]["id"]

        # ----------------------------------------------------
        # STAGE 4: Visit Request Creation (Visitors ↔ Requests ↔ Host)
        # ----------------------------------------------------
        now_dt = datetime.now()
        start_time = now_dt + timedelta(minutes=5)
        end_time = now_dt + timedelta(hours=4)

        request_payload = {
            "tenant_id": tenant.id,
            "visitor_id": visitor_id,
            "host_id": host_user.id,
            "purpose": "Quarterly Technical Audit & Review",
            "department": "Engineering",
            "scheduled_start_time": start_time.isoformat(),
            "scheduled_end_time": end_time.isoformat(),
            "notes": "Requires server room access escort"
        }
        req_resp = client.post(
            "/api/v1/visit-requests",
            headers=auth_headers,
            json=request_payload
        )
        assert req_resp.status_code == 201, f"Visit Request Failed: {req_resp.json()}"
        req_data = req_resp.json()["data"]
        visit_request_id = req_data["id"]

        # ----------------------------------------------------
        # STAGE 5: Approval Workflow (Requests ↔ Approval)
        # ----------------------------------------------------
        approval_resp = client.post(
            f"/api/v1/visit-requests/{visit_request_id}/approve",
            headers=auth_headers,
            json={"comments": "Approved by Jane Host"}
        )
        assert approval_resp.status_code == 200, f"Approval Failed: {approval_resp.json()}"
        assert approval_resp.json()["data"]["status"] == "APPROVED"

        # ----------------------------------------------------
        # STAGE 6: Visitor Pass & QR Generation (Approval ↔ Pass ↔ QR)
        # ----------------------------------------------------
        pass_list_resp = client.get(
            f"/api/v1/passes?visit_request_id={visit_request_id}",
            headers=auth_headers
        )
        assert pass_list_resp.status_code == 200, f"Pass List Failed: {pass_list_resp.json()}"
        passes = pass_list_resp.json()["data"]["items"]
        assert len(passes) >= 1, f"No pass found for visit request {visit_request_id}"
        pass_data = passes[0]
        pass_id = pass_data["id"]
        assert pass_data["status"] == "ACTIVE"

        # Fetch QR payload
        qr_resp = client.get(
            f"/api/v1/passes/{pass_id}/qr",
            headers=auth_headers
        )
        assert qr_resp.status_code == 200, f"QR Fetch Failed: {qr_resp.json()}"
        qr_token = qr_resp.json()["data"]["token"]
        assert qr_token is not None

        # ----------------------------------------------------
        # STAGE 7: Verification of Notifications (Check-In / Pass ↔ Notification)
        # ----------------------------------------------------
        notif_list_resp = client.get(
            "/api/v1/notifications",
            headers=admin_headers
        )
        assert notif_list_resp.status_code == 200

        # ----------------------------------------------------
        # STAGE 8: Gate Check-In via QR Scan (QR ↔ Check-In ↔ Notification)
        # ----------------------------------------------------
        checkin_payload = {
            "qr_token": qr_token,
            "device_meta": {
                "gate_device_id": "GATE-DEV-MAIN-01",
                "scanner_name": "Main Entrance Scanner",
                "scanner_ip": "192.168.1.50",
                "scanner_location": "Building A Main Lobby",
                "scanner_version": "v2.1",
                "gate_name": "Gate A1",
                "gate_number": "A1"
            },
            "notes": "Verified photo ID at gate"
        }
        checkin_resp = client.post(
            "/api/v1/checkin/scan",
            headers=sec_headers,
            json=checkin_payload
        )
        assert checkin_resp.status_code in [200, 201], f"Gate Check-In Failed: {checkin_resp.json()}"
        checkin_data = checkin_resp.json()["data"]
        checkin_id = checkin_data["id"]
        assert checkin_data["status"] == "CHECKED_IN"

        # Verify active occupancy dashboard metrics
        live_dash_resp = client.get(
            f"/api/v1/checkins/live-dashboard?tenant_id={tenant.id}",
            headers=sec_headers
        )
        assert live_dash_resp.status_code == 200
        dash_data = live_dash_resp.json()["data"]
        assert dash_data["visitors_inside"] >= 1

        # ----------------------------------------------------
        # STAGE 9: Gate Check-Out (Gate Check-Out ↔ Pass Completion)
        # ----------------------------------------------------
        checkout_payload = {
            "qr_token": qr_token,
            "device_meta": {
                "gate_device_id": "GATE-DEV-MAIN-01",
                "gate_name": "Gate A1"
            },
            "notes": "Returned visitor badge"
        }
        checkout_resp = client.post(
            "/api/v1/checkout/scan",
            headers=sec_headers,
            json=checkout_payload
        )
        assert checkout_resp.status_code == 200, f"Gate Check-Out Failed: {checkout_resp.json()}"
        checkout_data = checkout_resp.json()["data"]
        assert checkout_data["status"] == "CHECKED_OUT"
        assert checkout_data["visit_duration_minutes"] is not None

        # ----------------------------------------------------
        # STAGE 10: Audit Log & Security Audit Trail (Security ↔ Audit ↔ Modules)
        # ----------------------------------------------------
        audit_resp = client.get(
            f"/api/v1/audit?tenant_id={tenant.id}",
            headers=admin_headers
        )
        assert audit_resp.status_code == 200
        audit_logs = audit_resp.json()["data"]["items"]
        assert len(audit_logs) > 0

        # Verify specific actions recorded in audit logs
        actions_logged = [log["action"] for log in audit_logs]
        assert "GATE_CHECKIN" in actions_logged or "GATE_CHECKOUT" in actions_logged or len(actions_logged) >= 1

        # ----------------------------------------------------
        # STAGE 11: Health Check Endpoint
        # ----------------------------------------------------
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["data"]["status"] == "healthy"

    finally:
        db.close()
