import os
import sys
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
from app.models.visitor import Visitor, VisitorStatus, VerificationStatus, VerificationMethod
from app.models.role import Role

client = TestClient(fastapi_app)


@pytest.fixture(autouse=True, scope="module")
def setup_database():
    """Ensure database tables exist before running test suite."""
    Base.metadata.create_all(bind=engine)


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
        tenant = db.query(Tenant).filter_by(name="Visitor Test Organization").first()
        if not tenant:
            tenant = Tenant(
                name="Visitor Test Organization",
                code="TEN-777777",
                slug="visitor-test-org",
                contact_person="Admin Tester",
                contact_email="tester@visitortest.com"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        return tenant
    finally:
        db.close()



def cleanup_test_visitor(visitor_id: int):
    """Helper cleanup function."""
    db: Session = SessionLocal()
    try:
        db.query(Visitor).filter_by(id=visitor_id).delete()
        db.commit()
    finally:
        db.close()

# --- TEST CASES ---

def test_create_visitor_success():
    """
    Test registering a new visitor with complete profile data and code generation.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "phone": "+19876543210",
        "email": "alice.smith@example.com",
        "tenant_id": tenant.id,
        "gender": "FEMALE",
        "company": "Acme Innovations",
        "designation": "Security Specialist",
        "government_id_type": "PASSPORT",
        "government_id_number": "P123456789",
        "government_id_front": "https://cdn.example.com/id_front.jpg",
        "government_id_back": "https://cdn.example.com/id_back.jpg",
        "profile_photo_url": "https://cdn.example.com/photo.jpg",
        "emergency_contact_name": "Bob Smith",
        "emergency_contact_phone": "+19876543211",
        "notes": "VIP Guest for Annual Summit"
    }

    res = client.post("/api/v1/visitors", json=payload, headers=headers)
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["phone"] == "+19876543210"
    assert data["email"] == "alice.smith@example.com"
    assert data["visitor_code"].startswith("VIS-")
    assert data["status"] == "ACTIVE"
    assert data["verified"] is False
    assert data["blacklisted"] is False
    assert data["government_id_front"] == "https://cdn.example.com/id_front.jpg"
    assert data["profile_photo_url"] == "https://cdn.example.com/photo.jpg"

    visitor_id = data["id"]
    cleanup_test_visitor(visitor_id)


def test_list_visitors_paginated_and_filtered():
    """
    Test listing visitors with dynamic search and pagination.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    # Create temporary visitor
    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Charlie",
        "last_name": "Brown",
        "phone": "+15550001111",
        "email": "charlie.brown@peanuts.com",
        "company": "Peanuts Inc",
        "tenant_id": tenant.id
    }, headers=headers)
    assert create_res.status_code == 201
    v_data = create_res.json()["data"]
    visitor_id = v_data["id"]

    # Search query
    res = client.get(f"/api/v1/visitors?search=Charlie&tenant_id={tenant.id}", headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["data"]["total_records"] >= 1
    items = res_data["data"]["items"]
    assert any(item["id"] == visitor_id for item in items)

    cleanup_test_visitor(visitor_id)


def test_get_visitor_by_id_and_code():
    """
    Test fetching visitor by ID and lookup by visitor_code.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Diana",
        "last_name": "Prince",
        "phone": "+15552223333",
        "email": "diana.prince@wonder.com",
        "tenant_id": tenant.id
    }, headers=headers)
    visitor_id = create_res.json()["data"]["id"]
    visitor_code = create_res.json()["data"]["visitor_code"]

    # Get by ID
    res_id = client.get(f"/api/v1/visitors/{visitor_id}", headers=headers)
    assert res_id.status_code == 200
    assert res_id.json()["data"]["visitor_code"] == visitor_code

    # Get by Code
    res_code = client.get(f"/api/v1/visitors/code/{visitor_code}", headers=headers)
    assert res_code.status_code == 200
    assert res_code.json()["data"]["id"] == visitor_id

    cleanup_test_visitor(visitor_id)


def test_update_visitor_profile():
    """
    Test updating visitor fields.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Edward",
        "last_name": "Elric",
        "phone": "+15553334444",
        "email": "edward@alchemy.org",
        "tenant_id": tenant.id
    }, headers=headers)
    visitor_id = create_res.json()["data"]["id"]

    # Update company and phone
    update_res = client.put(f"/api/v1/visitors/{visitor_id}", json={
        "company": "State Alchemists Corp",
        "phone": "+15553334455"
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["data"]["company"] == "State Alchemists Corp"
    assert update_res.json()["data"]["phone"] == "+15553334455"

    cleanup_test_visitor(visitor_id)


def test_verify_visitor_identity():
    """
    Test verifying visitor identity proof.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Fiona",
        "last_name": "Gallagher",
        "phone": "+15554445555",
        "tenant_id": tenant.id
    }, headers=headers)
    visitor_id = create_res.json()["data"]["id"]

    verify_res = client.patch(f"/api/v1/visitors/{visitor_id}/verify", json={
        "verification_method": "PASSPORT",
        "notes": "Verified against physical passport at security desk"
    }, headers=headers)
    assert verify_res.status_code == 200
    data = verify_res.json()["data"]
    assert data["verified"] is True
    assert data["verification_status"] == "VERIFIED"
    assert data["verification_method"] == "PASSPORT"

    cleanup_test_visitor(visitor_id)


def test_blacklist_and_remove_blacklist():
    """
    Test blacklisting a visitor and removing blacklist status.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    # Pre-test cleanup
    db = SessionLocal()
    db.query(Visitor).filter_by(phone="+15555556666").delete()
    db.commit()
    db.close()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "George",
        "last_name": "Costanza",
        "phone": "+15555556666",
        "tenant_id": tenant.id
    }, headers=headers)
    assert create_res.status_code == 201
    visitor_id = create_res.json()["data"]["id"]

    # Blacklist
    bl_res = client.patch(f"/api/v1/visitors/{visitor_id}/blacklist", json={
        "blacklisted": True,
        "reason": "Security protocol violation"
    }, headers=headers)
    assert bl_res.status_code == 200
    bl_data = bl_res.json()["data"]
    assert bl_data["blacklisted"] is True
    assert bl_data["status"] == "BLACKLISTED"
    assert bl_data["blacklist_reason"] == "Security protocol violation"

    # Verify attempt on blacklisted visitor fails with 422 ValidationException
    v_res = client.patch(f"/api/v1/visitors/{visitor_id}/verify", json={
        "verification_method": "MANUAL"
    }, headers=headers)
    assert v_res.status_code == 422


    # Remove Blacklist
    rm_res = client.patch(f"/api/v1/visitors/{visitor_id}/remove-blacklist", headers=headers)
    assert rm_res.status_code == 200
    rm_data = rm_res.json()["data"]
    assert rm_data["blacklisted"] is False
    assert rm_data["status"] == "ACTIVE"

    cleanup_test_visitor(visitor_id)


def test_activate_and_deactivate_visitor():
    """
    Test toggling active/inactive status.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    db = SessionLocal()
    db.query(Visitor).filter_by(phone="+15556667777").delete()
    db.commit()
    db.close()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Hannah",
        "last_name": "Abbott",
        "phone": "+15556667777",
        "tenant_id": tenant.id
    }, headers=headers)
    assert create_res.status_code == 201
    visitor_id = create_res.json()["data"]["id"]

    # Deactivate
    deact_res = client.patch(f"/api/v1/visitors/{visitor_id}/deactivate", headers=headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["status"] == "INACTIVE"

    # Activate
    act_res = client.patch(f"/api/v1/visitors/{visitor_id}/activate", headers=headers)
    assert act_res.status_code == 200
    assert act_res.json()["data"]["status"] == "ACTIVE"

    cleanup_test_visitor(visitor_id)


def test_soft_delete_and_restore_visitor():
    """
    Test soft deleting visitor record and restoring it.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    db = SessionLocal()
    db.query(Visitor).filter_by(phone="+15557778888").delete()
    db.commit()
    db.close()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Ian",
        "last_name": "Malcolm",
        "phone": "+15557778888",
        "tenant_id": tenant.id
    }, headers=headers)
    assert create_res.status_code == 201
    visitor_id = create_res.json()["data"]["id"]

    # Soft delete
    del_res = client.delete(f"/api/v1/visitors/{visitor_id}", headers=headers)
    assert del_res.status_code == 200

    # Get by ID should fail with 404
    get_res = client.get(f"/api/v1/visitors/{visitor_id}", headers=headers)
    assert get_res.status_code == 404

    # Restore
    rest_res = client.patch(f"/api/v1/visitors/{visitor_id}/restore", headers=headers)
    assert rest_res.status_code == 200
    assert rest_res.json()["data"]["is_deleted"] is False

    cleanup_test_visitor(visitor_id)


def test_visitor_activity_timeline():
    """
    Test fetching visitor activity timeline logs.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    db = SessionLocal()
    db.query(Visitor).filter_by(phone="+15558889999").delete()
    db.commit()
    db.close()

    create_res = client.post("/api/v1/visitors", json={
        "first_name": "Jack",
        "last_name": "Sparrow",
        "phone": "+15558889999",
        "tenant_id": tenant.id
    }, headers=headers)
    assert create_res.status_code == 201
    visitor_id = create_res.json()["data"]["id"]

    act_res = client.get(f"/api/v1/visitors/{visitor_id}/activity", headers=headers)
    assert act_res.status_code == 200
    res_data = act_res.json()
    assert res_data["success"] is True
    assert len(res_data["data"]) >= 1
    assert res_data["data"][0]["action"] == "VISITOR_CREATED"

    cleanup_test_visitor(visitor_id)



def test_visitor_statistics_endpoint():
    """
    Test visitor statistics overview endpoint.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    res = client.get(f"/api/v1/visitors/statistics?tenant_id={tenant.id}", headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    stats = res_data["data"]
    assert "total_visitors" in stats
    assert "active_visitors" in stats
    assert "blacklisted_visitors" in stats
    assert "verified_visitors" in stats
    assert "returning_visitors" in stats


def test_visitor_export_csv():
    """
    Test exporting visitors to CSV payload.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/visitors/export", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Visitor Code" in res.text


def test_triple_duplicate_validation_failures():
    """
    Test duplicate validation failure on phone, email, and government ID number.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant = get_or_create_test_tenant()

    # Pre-test cleanup
    db = SessionLocal()
    db.query(Visitor).filter(
        (Visitor.phone == "+15559990000") | 
        (Visitor.email == "kevin.bacon@hollywood.com") | 
        (Visitor.government_id_number == "GOV-DUP-100")
    ).delete(synchronize_session=False)
    db.commit()
    db.close()

    # Create initial visitor
    client.post("/api/v1/visitors", json={
        "first_name": "Kevin",
        "last_name": "Bacon",
        "phone": "+15559990000",
        "email": "kevin.bacon@hollywood.com",
        "government_id_number": "GOV-DUP-100",
        "tenant_id": tenant.id
    }, headers=headers)

    # Duplicate phone
    res_phone = client.post("/api/v1/visitors", json={
        "first_name": "Different",
        "last_name": "Name",
        "phone": "+15559990000",
        "tenant_id": tenant.id
    }, headers=headers)
    assert res_phone.status_code == 422
    assert "already exists" in res_phone.json()["message"]

    # Duplicate email
    res_email = client.post("/api/v1/visitors", json={
        "first_name": "Different",
        "last_name": "Name",
        "phone": "+15559990001",
        "email": "kevin.bacon@hollywood.com",
        "tenant_id": tenant.id
    }, headers=headers)
    assert res_email.status_code == 422
    assert "already exists" in res_email.json()["message"]

    # Duplicate Government ID
    res_gov = client.post("/api/v1/visitors", json={
        "first_name": "Different",
        "last_name": "Name",
        "phone": "+15559990002",
        "government_id_number": "GOV-DUP-100",
        "tenant_id": tenant.id
    }, headers=headers)
    assert res_gov.status_code == 422
    assert "already exists" in res_gov.json()["message"]

    # Clean up created initial visitor
    db = SessionLocal()
    db.query(Visitor).filter(
        (Visitor.phone == "+15559990000") | 
        (Visitor.phone == "+15559990001") | 
        (Visitor.phone == "+15559990002")
    ).delete(synchronize_session=False)
    db.commit()
    db.close()

