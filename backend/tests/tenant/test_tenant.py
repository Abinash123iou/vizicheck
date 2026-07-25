import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from main import app
from config import settings
from database.session import SessionLocal
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_settings import TenantSettings
from app.models.user import User
from app.models.role import Role
from app.core.password import hash_password

client = TestClient(app)

def get_super_admin_token() -> str:
    """Helper to acquire valid Super Admin access token."""
    res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    return res.json()["data"]["access_token"]

def get_role_id(role_name: str) -> int:
    """Helper to fetch role ID from database."""
    db: Session = SessionLocal()
    try:
        role = db.query(Role).filter_by(name=role_name).first()
        if not role:
            pytest.fail(f"Role '{role_name}' not found in database")
        return role.id
    finally:
        db.close()

# --- POSITIVE TEST CASES ---

def test_create_tenant_success():
    """
    Test creating a new tenant organization with custom settings and code generation.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Pre-test cleanup
    db = SessionLocal()
    t = db.query(Tenant).filter((Tenant.name == "Acme Corp") | (Tenant.slug == "acme-corp") | (Tenant.domain == "acme.vizicheck.com")).first()
    if t:
        db.query(TenantSettings).filter_by(tenant_id=t.id).delete()
        db.query(Tenant).filter_by(id=t.id).delete()
        db.commit()
    db.close()



    payload = {
        "name": "Acme Corp",
        "slug": "acme-corp",
        "domain": "acme.vizicheck.com",
        "description": "Enterprise Acme Corporation",
        "contact_person": "Jane Doe",
        "contact_email": "jane@acme.com",
        "contact_phone": "+15551234567",
        "settings": {
            "timezone": "America/New_York",
            "language": "en",
            "currency": "USD",
            "date_format": "MM/DD/YYYY",
            "max_users": 50,
            "max_visitors": 500,
            "allowed_login_methods": ["PASSWORD", "SSO"]
        }
    }

    res = client.post("/api/v1/tenants", json=payload, headers=headers)
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["name"] == "Acme Corp"
    assert data["slug"] == "acme-corp"
    assert data["domain"] == "acme.vizicheck.com"
    assert data["code"].startswith("TEN-")
    assert data["status"] == "ACTIVE"
    assert data["settings"]["timezone"] == "America/New_York"
    assert data["settings"]["max_users"] == 50

    tenant_id = data["id"]

    # Cleanup
    db = SessionLocal()
    db.query(TenantSettings).filter_by(tenant_id=tenant_id).delete()
    db.query(Tenant).filter_by(id=tenant_id).delete()
    db.commit()
    db.close()

def test_get_and_list_tenants_with_pagination_and_search():
    """
    Test listing, searching, pagination, and getting single tenant details by ID.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create temporary tenant
    create_res = client.post("/api/v1/tenants", json={
        "name": "Beta Tech",
        "slug": "beta-tech",
        "domain": "beta.com",
        "contact_person": "Bob Smith",
        "contact_email": "bob@beta.com"
    }, headers=headers)
    tenant_id = create_res.json()["data"]["id"]

    try:
        # List tenants with search
        res = client.get("/api/v1/tenants?page=1&page_size=5&search=beta", headers=headers)
        assert res.status_code == 200
        res_json = res.json()
        assert res_json["success"] is True
        items = res_json["data"]["items"]
        assert len(items) >= 1
        assert items[0]["slug"] == "beta-tech"

        # Get single tenant
        get_res = client.get(f"/api/v1/tenants/{tenant_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["data"]["name"] == "Beta Tech"
    finally:
        db = SessionLocal()
        db.query(TenantSettings).filter_by(tenant_id=tenant_id).delete()
        db.query(Tenant).filter_by(id=tenant_id).delete()
        db.commit()
        db.close()

def test_update_suspend_activate_tenant():
    """
    Test updating tenant details, settings, and toggling suspension/activation.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/v1/tenants", json={
        "name": "Gamma Solutions",
        "contact_person": "Alice",
        "contact_email": "alice@gamma.com"
    }, headers=headers)
    tenant_id = create_res.json()["data"]["id"]

    try:
        # 1. Update tenant and settings
        upd_res = client.put(f"/api/v1/tenants/{tenant_id}", json={
            "contact_person": "Alice Smith",
            "settings": {
                "timezone": "Europe/London",
                "max_users": 200
            }
        }, headers=headers)
        assert upd_res.status_code == 200
        assert upd_res.json()["data"]["contact_person"] == "Alice Smith"
        assert upd_res.json()["data"]["settings"]["timezone"] == "Europe/London"

        # 2. Suspend tenant
        susp_res = client.patch(f"/api/v1/tenants/{tenant_id}/suspend", headers=headers)
        assert susp_res.status_code == 200
        assert susp_res.json()["data"]["status"] == "SUSPENDED"

        # 3. Activate tenant
        act_res = client.patch(f"/api/v1/tenants/{tenant_id}/activate", headers=headers)
        assert act_res.status_code == 200
        assert act_res.json()["data"]["status"] == "ACTIVE"
    finally:
        db = SessionLocal()
        db.query(TenantSettings).filter_by(tenant_id=tenant_id).delete()
        db.query(Tenant).filter_by(id=tenant_id).delete()
        db.commit()
        db.close()

def test_soft_delete_and_restore_tenant():
    """
    Test soft deleting a tenant and restoring soft-deleted record.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/v1/tenants", json={
        "name": "Delta Logistics",
        "contact_person": "Charlie",
        "contact_email": "charlie@delta.com"
    }, headers=headers)
    tenant_id = create_res.json()["data"]["id"]

    try:
        # Soft delete
        del_res = client.delete(f"/api/v1/tenants/{tenant_id}", headers=headers)
        assert del_res.status_code == 200

        # Normal GET should fail 404
        get_res = client.get(f"/api/v1/tenants/{tenant_id}", headers=headers)
        assert get_res.status_code == 404

        # Restore tenant
        rest_res = client.patch(f"/api/v1/tenants/{tenant_id}/restore", headers=headers)
        assert rest_res.status_code == 200
        assert rest_res.json()["data"]["is_deleted"] is False

        # Active query works again
        get_res2 = client.get(f"/api/v1/tenants/{tenant_id}", headers=headers)
        assert get_res2.status_code == 200
    finally:
        db = SessionLocal()
        db.query(TenantSettings).filter_by(tenant_id=tenant_id).delete()
        db.query(Tenant).filter_by(id=tenant_id).delete()
        db.commit()
        db.close()

def test_tenant_statistics_export_and_activity():
    """
    Test GET /statistics, GET /export CSV, and GET /{id}/activity.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/v1/tenants", json={
        "name": "Epsilon Systems",
        "contact_person": "Eve",
        "contact_email": "eve@epsilon.com"
    }, headers=headers)
    tenant_id = create_res.json()["data"]["id"]

    try:
        # 1. Dashboard statistics
        stats_res = client.get("/api/v1/tenants/statistics", headers=headers)
        assert stats_res.status_code == 200
        stats_data = stats_res.json()["data"]
        assert "tenant_overview" in stats_data
        assert "user_stats" in stats_data
        assert stats_data["tenant_overview"]["total"] >= 1

        # 2. Export CSV
        export_res = client.get("/api/v1/tenants/export", headers=headers)
        assert export_res.status_code == 200
        assert "text/csv" in export_res.headers["content-type"]
        assert "Epsilon Systems" in export_res.text

        # 3. Activity timeline
        activity_res = client.get(f"/api/v1/tenants/{tenant_id}/activity", headers=headers)
        assert activity_res.status_code == 200
        activity_data = activity_res.json()["data"]
        assert isinstance(activity_data, list)
        assert len(activity_data) >= 1
        assert activity_data[0]["action"] == "TENANT_CREATED"
    finally:
        db = SessionLocal()
        db.query(TenantSettings).filter_by(tenant_id=tenant_id).delete()
        db.query(Tenant).filter_by(id=tenant_id).delete()
        db.commit()
        db.close()

# --- NEGATIVE TEST CASES & VALIDATION ---

def test_duplicate_name_slug_domain():
    """
    Test unique constraints return 409 conflict for duplicate name, slug, or domain.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/tenants", json={
        "name": "Unique Tenant",
        "slug": "unique-slug",
        "domain": "unique.com",
        "contact_person": "Owner",
        "contact_email": "owner@unique.com"
    }, headers=headers)

    db = SessionLocal()
    tenant = db.query(Tenant).filter_by(name="Unique Tenant").first()
    tenant_id = tenant.id

    try:
        # Duplicate name
        res1 = client.post("/api/v1/tenants", json={
            "name": "Unique Tenant",
            "contact_person": "Other",
            "contact_email": "other@unique.com"
        }, headers=headers)
        assert res1.status_code == 409

        # Duplicate slug
        res2 = client.post("/api/v1/tenants", json={
            "name": "Other Name",
            "slug": "unique-slug",
            "contact_person": "Other",
            "contact_email": "other2@unique.com"
        }, headers=headers)
        assert res2.status_code == 409

        # Duplicate domain
        res3 = client.post("/api/v1/tenants", json={
            "name": "Other Name 2",
            "domain": "unique.com",
            "contact_person": "Other",
            "contact_email": "other3@unique.com"
        }, headers=headers)
        assert res3.status_code == 409
    finally:
        db.query(TenantSettings).filter_by(tenant_id=tenant_id).delete()
        db.query(Tenant).filter_by(id=tenant_id).delete()
        db.commit()
        db.close()

def test_tenant_isolation_and_rbac_restrictions():
    """
    Test Tenant Admin cannot create/delete tenants or view another tenant's details.
    """
    db = SessionLocal()
    old_t = db.query(Tenant).filter((Tenant.name == "Tenant Isolation Corp") | (Tenant.code == "TEN-999999")).first()
    if old_t:
        db.query(User).filter_by(tenant_id=old_t.id).delete()
        db.query(TenantSettings).filter_by(tenant_id=old_t.id).delete()
        db.query(Tenant).filter_by(id=old_t.id).delete()
        db.commit()

    try:
        # Create test tenant and user
        tenant_org = Tenant(name="Tenant Isolation Corp", code="TEN-999999", contact_person="Admin", contact_email="admin@iso.com", status=TenantStatus.ACTIVE)

        db.add(tenant_org)
        db.flush()

        role_ta = db.query(Role).filter_by(name="TENANT_ADMIN").first()
        ta_user = User(
            email="tenant_admin@iso.com",
            first_name="TA",
            last_name="User",
            password_hash=hash_password("Password@123"),
            is_active=True,
            role_id=role_ta.id,
            tenant_id=tenant_org.id
        )
        db.add(ta_user)
        db.commit()

        login_res = client.post("/api/v1/auth/login", json={
            "email": "tenant_admin@iso.com",
            "password": "Password@123"
        })
        token_ta = login_res.json()["data"]["access_token"]
        headers_ta = {"Authorization": f"Bearer {token_ta}"}

        # 1. Tenant Admin cannot create tenant (403)
        res_create = client.post("/api/v1/tenants", json={
            "name": "Forbidden Tenant",
            "contact_person": "X",
            "contact_email": "x@forbidden.com"
        }, headers=headers_ta)
        assert res_create.status_code == 403

        # 2. Tenant Admin cannot view stats (403)
        res_stats = client.get("/api/v1/tenants/statistics", headers=headers_ta)
        assert res_stats.status_code == 403

        # 3. Tenant Admin can access own tenant
        res_own = client.get(f"/api/v1/tenants/{tenant_org.id}", headers=headers_ta)
        assert res_own.status_code == 200

        # 4. Tenant Admin cannot access another tenant ID (e.g. 9999) (403)
        res_other = client.get("/api/v1/tenants/999999", headers=headers_ta)
        assert res_other.status_code in [403, 404]
    finally:
        db.query(User).filter_by(email="tenant_admin@iso.com").delete()
        db.query(TenantSettings).filter_by(tenant_id=tenant_org.id).delete()
        db.query(Tenant).filter_by(id=tenant_org.id).delete()
        db.commit()
        db.close()

def test_delete_safety_checks():
    """
    Test deleting active tenant with active users is blocked (HTTP 400 BusinessRuleException).
    """
    db = SessionLocal()
    old_t = db.query(Tenant).filter((Tenant.name == "Safety Tenant") | (Tenant.code == "TEN-888888")).first()
    if old_t:
        db.query(User).filter_by(tenant_id=old_t.id).delete()
        db.query(TenantSettings).filter_by(tenant_id=old_t.id).delete()
        db.query(Tenant).filter_by(id=old_t.id).delete()
        db.commit()

    try:
        tenant_org = Tenant(name="Safety Tenant", code="TEN-888888", contact_person="Owner", contact_email="owner@safety.com", status=TenantStatus.ACTIVE)

        db.add(tenant_org)
        db.flush()

        role_vis = db.query(Role).filter_by(name="VISITOR").first()
        user = User(
            email="user@safety.com",
            first_name="Active",
            last_name="User",
            password_hash=hash_password("Password@123"),
            is_active=True,
            role_id=role_vis.id,
            tenant_id=tenant_org.id
        )
        db.add(user)
        db.commit()

        token = get_super_admin_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to delete tenant with active users
        del_res = client.delete(f"/api/v1/tenants/{tenant_org.id}", headers=headers)
        assert del_res.status_code == 400
        assert "active user account" in del_res.json()["message"]
    finally:
        db.query(User).filter_by(email="user@safety.com").delete()
        db.query(TenantSettings).filter_by(tenant_id=tenant_org.id).delete()
        db.query(Tenant).filter_by(id=tenant_org.id).delete()
        db.commit()
        db.close()
