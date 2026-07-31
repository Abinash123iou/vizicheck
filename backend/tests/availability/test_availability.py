import os
import sys
import pytest
from datetime import date, time, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import app.models  # Ensure all models are registered
from main import app as fastapi_app
from database.session import SessionLocal, engine
from database.base import Base

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

from app.models.tenant import Tenant, TenantStatus
from app.models.role import Role
from app.models.user import User
from app.models.availability import HostAvailability, AvailabilityException, Weekday, RecurrenceType, ExceptionType
from app.core.security import create_access_token
from app.core.password import hash_password

client = TestClient(fastapi_app)


@pytest.fixture
def db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()



@pytest.fixture
def availability_test_setup(db: Session):
    """
    Fixture providing test Tenant, Host User, Regular User, and Auth Headers.
    """
    role_admin = db.query(Role).filter_by(name="SUPER_ADMIN").first()
    if not role_admin:
        role_admin = Role(name="SUPER_ADMIN", description="Super Admin")
        db.add(role_admin)
        db.commit()

    role_host = db.query(Role).filter_by(name="TENANT_ADMIN").first()
    if not role_host:
        role_host = Role(name="TENANT_ADMIN", description="Tenant Admin Host")
        db.add(role_host)
        db.commit()

    # 1. Create Tenant
    uid = datetime.utcnow().strftime("%f")
    tenant = Tenant(
        name=f"Avail Test Tenant {uid}",
        slug=f"avail-tenant-{uid}",
        code=f"TEN-AV-{uid[:4]}",
        contact_person="Host Admin",
        contact_email=f"host.admin.{uid}@example.com",
        status=TenantStatus.ACTIVE
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # 2. Create Host User
    pwd_hash = hash_password("TestPassword123!")
    host_user = User(
        tenant_id=tenant.id,
        role_id=role_host.id,
        first_name="Vikram",
        last_name="Host",
        email=f"vikram.host.{uid}@example.com",
        password_hash=pwd_hash,
        is_active=True
    )
    db.add(host_user)
    db.commit()
    db.refresh(host_user)

    # 3. Create Super Admin User
    admin_user = User(
        tenant_id=tenant.id,
        role_id=role_admin.id,
        first_name="Super",
        last_name="Admin",
        email=f"super.admin.{uid}@example.com",
        password_hash=pwd_hash,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    token_admin = create_access_token(data={"sub": str(admin_user.id), "email": admin_user.email, "tenant_id": tenant.id})
    token_host = create_access_token(data={"sub": str(host_user.id), "email": host_user.email, "tenant_id": tenant.id})

    return {
        "tenant": tenant,
        "host": host_user,
        "admin": admin_user,
        "admin_headers": {"Authorization": f"Bearer {token_admin}"},
        "host_headers": {"Authorization": f"Bearer {token_host}"}
    }


def test_create_availability_schedule_success(availability_test_setup):
    setup = availability_test_setup
    payload = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "MONDAY",
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "break_start": "13:00:00",
        "break_end": "14:00:00",
        "max_visitors": 5,
        "is_available": True,
        "notes": "Monday Working Hours"
    }

    response = client.post("/api/v1/availability", json=payload, headers=setup["admin_headers"])
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["weekday"] == "MONDAY"
    assert res_json["data"]["start_time"] == "09:00:00"
    assert res_json["data"]["end_time"] == "17:00:00"


def test_create_availability_overlapping_schedule_fails(availability_test_setup):
    setup = availability_test_setup
    payload_1 = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "TUESDAY",
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    resp1 = client.post("/api/v1/availability", json=payload_1, headers=setup["admin_headers"])
    assert resp1.status_code == 201

    # Attempting to create an overlapping schedule on Tuesday (10:00 - 12:00)
    payload_2 = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "TUESDAY",
        "start_time": "10:00:00",
        "end_time": "12:00:00"
    }
    resp2 = client.post("/api/v1/availability", json=payload_2, headers=setup["admin_headers"])
    assert resp2.status_code == 400
    assert "overlapping availability schedule" in resp2.json()["message"]


def test_create_availability_invalid_break_timing_fails(availability_test_setup):
    setup = availability_test_setup
    payload = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "WEDNESDAY",
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "break_start": "18:00:00",  # Break outside working hours
        "break_end": "19:00:00"
    }

    response = client.post("/api/v1/availability", json=payload, headers=setup["admin_headers"])
    assert response.status_code == 400
    assert "must fall entirely inside working hours" in response.json()["message"]


def test_list_and_get_availability_schedules(availability_test_setup):
    setup = availability_test_setup
    payload = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "THURSDAY",
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    create_res = client.post("/api/v1/availability", json=payload, headers=setup["admin_headers"])
    avail_id = create_res.json()["data"]["id"]

    # List schedules
    list_res = client.get(f"/api/v1/availability?tenant_id={setup['tenant'].id}&user_id={setup['host'].id}", headers=setup["admin_headers"])
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]["items"]) >= 1

    # Get single schedule
    get_res = client.get(f"/api/v1/availability/{avail_id}", headers=setup["admin_headers"])
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == avail_id


def test_update_and_delete_availability_schedule(availability_test_setup):
    setup = availability_test_setup
    payload = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "FRIDAY",
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    create_res = client.post("/api/v1/availability", json=payload, headers=setup["admin_headers"])
    avail_id = create_res.json()["data"]["id"]

    # Update schedule
    update_res = client.put(f"/api/v1/availability/{avail_id}", json={"max_visitors": 10, "notes": "Updated capacity"}, headers=setup["admin_headers"])
    assert update_res.status_code == 200
    assert update_res.json()["data"]["max_visitors"] == 10

    # Delete schedule
    delete_res = client.delete(f"/api/v1/availability/{avail_id}", headers=setup["admin_headers"])
    assert delete_res.status_code == 200

    # Verify 404 on get after delete
    get_res = client.get(f"/api/v1/availability/{avail_id}", headers=setup["admin_headers"])
    assert get_res.status_code == 404


def test_availability_exceptions_flow(availability_test_setup):
    setup = availability_test_setup
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    exception_payload = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "title": "Annual Team Offsite",
        "exception_type": "HOLIDAY",
        "start_date": today_str,
        "end_date": tomorrow_str,
        "is_full_day": True,
        "notes": "Company Offsite"
    }

    create_res = client.post("/api/v1/availability/exceptions", json=exception_payload, headers=setup["admin_headers"])
    assert create_res.status_code == 201
    exc_id = create_res.json()["data"]["id"]

    # List exceptions
    list_res = client.get(f"/api/v1/availability/exceptions?tenant_id={setup['tenant'].id}", headers=setup["admin_headers"])
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # Delete exception
    del_res = client.delete(f"/api/v1/availability/exceptions/{exc_id}", headers=setup["admin_headers"])
    assert del_res.status_code == 200


def test_check_host_available_slots(availability_test_setup):

    setup = availability_test_setup
    # Determine next Monday date
    today = date.today()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)

    payload = {
        "tenant_id": setup["tenant"].id,
        "user_id": setup["host"].id,
        "weekday": "MONDAY",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "break_start": "10:00:00",
        "break_end": "10:30:00",
        "max_visitors": 2
    }
    client.post("/api/v1/availability", json=payload, headers=setup["admin_headers"])

    # Query available slots for next Monday
    slots_res = client.get(
        f"/api/v1/availability/slots?host_id={setup['host'].id}&date={next_monday.isoformat()}&slot_duration_minutes=30",
        headers=setup["admin_headers"]
    )

    assert slots_res.status_code == 200
    res_json = slots_res.json()
    assert res_json["success"] is True
    assert res_json["data"]["is_working_day"] is True
    slots = res_json["data"]["slots"]
    assert len(slots) >= 3
    # Break slot (10:00 - 10:30) should be marked unavailable
    break_slot = next(s for s in slots if s["start_time"] == "10:00:00")
    assert break_slot["is_available"] is False
    assert "Break" in break_slot["reason"]
