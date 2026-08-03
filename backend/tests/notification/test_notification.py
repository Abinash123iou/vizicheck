import os
import sys
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from main import app as fastapi_app
from config import settings
from database.session import SessionLocal, engine
from database.base import Base
import app.models  # Register all ORM models
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.notification import Notification, NotificationTemplate, NotificationPreference, NotificationStatus, NotificationChannel

client = TestClient(fastapi_app)


@pytest.fixture(autouse=True, scope="function")
def cleanup_notifications():
    """Ensure clean database table state for notifications before each test."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        db.query(Notification).delete()
        db.query(NotificationTemplate).delete()
        db.query(NotificationPreference).delete()
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
    """Helper to retrieve or initialize a tenant for testing."""
    db: Session = SessionLocal()
    try:
        tenant = db.query(Tenant).filter_by(code="TEN-NOTIF-01").first()
        if not tenant:
            tenant = Tenant(
                name="Notification Test Corp",
                code="TEN-NOTIF-01",
                slug="notif-test-corp",
                contact_person="Notif Tester",
                contact_email="tester@notifcorp.com"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        return tenant
    finally:
        db.close()


def test_send_notification_email_success():
    """Verify sending an EMAIL notification returns 201 Created with status DELIVERED."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()

    payload = {
        "tenant_id": tenant.id,
        "recipient_email": "visitor.test@example.com",
        "notification_type": "VISIT_REQUEST_APPROVED",
        "channel": "EMAIL",
        "title": "Visit Request Approved",
        "message": "Your visit request VR-1002 has been approved.",
        "priority": "HIGH"
    }

    res = client.post(
        "/api/v1/notifications/send",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["status"] == "DELIVERED"
    assert data["channel"] == "EMAIL"
    assert data["recipient_email"] == "visitor.test@example.com"
    assert data["uuid"] is not None


def test_send_notification_sms_and_inapp():
    """Verify sending SMS and IN_APP notifications."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()

    # 1. SMS
    res_sms = client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_phone": "+1999888777",
            "notification_type": "PASS_GENERATED",
            "channel": "SMS",
            "title": "Pass Generated",
            "message": "Your Visitor Pass VP-2001 is ready."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_sms.status_code == 201, res_sms.text
    assert res_sms.json()["data"]["channel"] == "SMS"

    # 2. IN_APP
    res_inapp = client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_user_id": 1,
            "notification_type": "VISITOR_CHECKED_IN",
            "channel": "IN_APP",
            "title": "Visitor Checked In",
            "message": "John Doe has arrived at Gate 1."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_inapp.status_code == 201, res_inapp.text
    assert res_inapp.json()["data"]["channel"] == "IN_APP"


def test_user_preference_opt_out_rejection():
    """Verify notification dispatch fails if recipient user has opted out of target channel."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()

    # 1. Update user preference to disable SMS
    res_pref = client.put(
        "/api/v1/notifications/preferences?user_id=1",
        json={
            "email_enabled": True,
            "sms_enabled": False,
            "inapp_enabled": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_pref.status_code == 200, res_pref.text
    assert res_pref.json()["data"]["sms_enabled"] is False

    # 2. Attempt to dispatch SMS notification to user_id=1 -> expecting validation failure (400 or 422)
    res_send = client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_user_id": 1,
            "recipient_phone": "+1222333444",
            "channel": "SMS",
            "title": "Alert",
            "message": "Test Message"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_send.status_code in [400, 422]
    assert "opted out of sms" in res_send.json()["message"].lower()


def test_template_create_and_variable_interpolation():
    """Verify template creation and interpolation of variables in notification body."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()

    # 1. Create Template
    res_tpl = client.post(
        "/api/v1/notifications/templates",
        json={
            "tenant_id": tenant.id,
            "template_code": "TPL_VISIT_APPROVED",
            "name": "Visit Request Approved Template",
            "channel": "EMAIL",
            "subject": "Visit Request {request_code} Approved",
            "body": "Dear {visitor_name}, your request to visit {host_name} on {visit_date} is approved.",
            "variables": ["request_code", "visitor_name", "host_name", "visit_date"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_tpl.status_code == 201, res_tpl.text

    # 2. Send notification using template_code and template_variables
    res_send = client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_email": "interpolated.visitor@example.com",
            "channel": "EMAIL",
            "title": "Default Title",
            "message": "Default Body",
            "template_code": "TPL_VISIT_APPROVED",
            "template_variables": {
                "request_code": "VR-9999",
                "visitor_name": "Alice Smith",
                "host_name": "Dr. Bob Johnson",
                "visit_date": "2026-08-10"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_send.status_code == 201, res_send.text
    data = res_send.json()["data"]
    assert data["title"] == "Visit Request VR-9999 Approved"
    assert "Dear Alice Smith, your request to visit Dr. Bob Johnson on 2026-08-10 is approved." in data["message"]


def test_list_notifications_paginated_and_filtered():
    """Verify listing notifications history with filtering and pagination."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()

    # Create two notification records
    client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_email": "list1@test.com",
            "channel": "EMAIL",
            "title": "Notification One",
            "message": "Message body one"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_phone": "+1888777666",
            "channel": "SMS",
            "title": "Notification Two",
            "message": "Message body two"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # List with channel filter = SMS
    res = client.get(
        "/api/v1/notifications?channel=SMS",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["total_records"] == 1
    assert data["items"][0]["channel"] == "SMS"


def test_mark_notification_as_read():
    """Verify marking an in-app notification as READ updates status."""
    token = get_super_admin_token()
    tenant = get_or_create_test_tenant()

    # Create in-app notification
    res_create = client.post(
        "/api/v1/notifications/send",
        json={
            "tenant_id": tenant.id,
            "recipient_user_id": 1,
            "channel": "IN_APP",
            "title": "Unread Alert",
            "message": "Please read this message."
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    notif_id = res_create.json()["data"]["id"]

    # Mark as read
    res_read = client.patch(
        f"/api/v1/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_read.status_code == 200, res_read.text
    assert res_read.json()["data"]["status"] == "READ"


def test_notification_statistics_endpoint():
    """Verify statistics endpoint returns aggregated metrics."""
    token = get_super_admin_token()
    res = client.get(
        "/api/v1/notifications/statistics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert "total_notifications" in data
    assert "delivered_count" in data
    assert "success_rate_percentage" in data
