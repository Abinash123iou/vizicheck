import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from config import settings
from database.session import SessionLocal
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
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
    """Helper to dynamically fetch role ID from database."""
    db: Session = SessionLocal()
    try:
        role = db.query(Role).filter_by(name=role_name).first()
        if not role:
            pytest.fail(f"Role '{role_name}' not found in database")
        return role.id
    finally:
        db.close()

# --- POSITIVE TEST CASES ---

def test_create_user_success():
    """
    Test creating a new user account with Super Admin token.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    tenant_admin_role_id = get_role_id("TENANT_ADMIN")

    payload = {
        "first_name": "Test",
        "last_name": "CreateUser",
        "email": "create_user_test@vizicheck.com",
        "password": "Password@123",
        "phone": "+1234567890",
        "role_id": tenant_admin_role_id
    }

    res = client.post("/api/v1/users", json=payload, headers=headers)
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "create_user_test@vizicheck.com"
    assert res_data["data"]["first_name"] == "Test"
    assert res_data["data"]["is_active"] is True
    assert res_data["data"]["is_deleted"] is False

    # Cleanup
    db = SessionLocal()
    db.query(User).filter_by(email="create_user_test@vizicheck.com").delete()
    db.commit()
    db.close()

def test_get_and_list_users_with_pagination_and_search():
    """
    Test listing, pagination metadata, search, and getting single user by ID.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # List users
    res = client.get("/api/v1/users?page=1&page_size=5&search=admin", headers=headers)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    pagination_data = res_json["data"]
    assert "page" in pagination_data
    assert "total_records" in pagination_data
    assert "items" in pagination_data
    assert isinstance(pagination_data["items"], list)

    # Get single user by ID
    user_res = client.get("/api/v1/users/1", headers=headers)
    assert user_res.status_code == 200
    assert user_res.json()["data"]["id"] == 1

def test_update_activate_deactivate_user():
    """
    Test updating user details and toggling activation status.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    visitor_role_id = get_role_id("VISITOR")

    # 1. Create temporary user
    create_res = client.post("/api/v1/users", json={
        "first_name": "Update",
        "last_name": "Target",
        "email": "update_target@vizicheck.com",
        "password": "Password@123",
        "role_id": visitor_role_id
    }, headers=headers)
    user_id = create_res.json()["data"]["id"]

    try:
        # 2. Update user
        update_res = client.put(f"/api/v1/users/{user_id}", json={
            "first_name": "UpdatedName",
            "phone": "+9999999999"
        }, headers=headers)
        assert update_res.status_code == 200
        assert update_res.json()["data"]["first_name"] == "UpdatedName"
        assert update_res.json()["data"]["phone"] == "+9999999999"

        # 3. Deactivate user
        deact_res = client.patch(f"/api/v1/users/{user_id}/deactivate", headers=headers)
        assert deact_res.status_code == 200
        assert deact_res.json()["data"]["is_active"] is False

        # 4. Activate user
        act_res = client.patch(f"/api/v1/users/{user_id}/activate", headers=headers)
        assert act_res.status_code == 200
        assert act_res.json()["data"]["is_active"] is True
    finally:
        db = SessionLocal()
        db.query(User).filter_by(id=user_id).delete()
        db.commit()
        db.close()

def test_soft_delete_and_restore_user():
    """
    Test soft deleting a user and restoring soft-deleted user record.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    visitor_role_id = get_role_id("VISITOR")

    create_res = client.post("/api/v1/users", json={
        "first_name": "Delete",
        "last_name": "Me",
        "email": "delete_restore_test@vizicheck.com",
        "password": "Password@123",
        "role_id": visitor_role_id
    }, headers=headers)
    user_id = create_res.json()["data"]["id"]

    try:
        # Soft delete
        del_res = client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert del_res.status_code == 200

        # Verify user is not found in normal queries
        get_res = client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert get_res.status_code == 404

        # Restore user
        restore_res = client.patch(f"/api/v1/users/{user_id}/restore", headers=headers)
        assert restore_res.status_code == 200
        assert restore_res.json()["data"]["is_deleted"] is False

        # Verify active query works again
        get_res2 = client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert get_res2.status_code == 200
    finally:
        db = SessionLocal()
        db.query(User).filter_by(id=user_id).delete()
        db.commit()
        db.close()

def test_profile_get_and_update():
    """
    Test GET /profile and PUT /profile for authenticated user.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Get profile
    prof_res = client.get("/api/v1/profile", headers=headers)
    assert prof_res.status_code == 200
    assert "email" in prof_res.json()["data"]

    # Update profile
    upd_res = client.put("/api/v1/profile", json={"phone": "+1112223333"}, headers=headers)
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["phone"] == "+1112223333"

def test_change_and_reset_password():
    """
    Test user changing self password and admin resetting password.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    visitor_role_id = get_role_id("VISITOR")

    # Create target user
    create_res = client.post("/api/v1/users", json={
        "first_name": "Pass",
        "last_name": "User",
        "email": "pass_user@vizicheck.com",
        "password": "OldPassword@123",
        "role_id": visitor_role_id
    }, headers=headers)
    user_id = create_res.json()["data"]["id"]

    try:
        # 1. Admin reset password
        reset_res = client.patch(f"/api/v1/users/{user_id}/reset-password", json={
            "new_password": "NewResetPass@123"
        }, headers=headers)
        assert reset_res.status_code == 200

        # 2. Login with new password
        login_res = client.post("/api/v1/auth/login", json={
            "email": "pass_user@vizicheck.com",
            "password": "NewResetPass@123"
        })
        assert login_res.status_code == 200
        user_token = login_res.json()["data"]["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 3. User changes self password
        chg_res = client.patch("/api/v1/users/change-password", json={
            "current_password": "NewResetPass@123",
            "new_password": "UserSelfPass@123"
        }, headers=user_headers)
        assert chg_res.status_code == 200
    finally:
        db = SessionLocal()
        db.query(User).filter_by(id=user_id).delete()
        db.commit()
        db.close()


# --- NEGATIVE TEST CASES ---

def test_duplicate_email():
    """
    Test creating user with duplicate email returns HTTP 409.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    super_admin_role_id = get_role_id("SUPER_ADMIN")

    payload = {
        "first_name": "Dup",
        "last_name": "Admin",
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL, # Already exists
        "password": "Password@123",
        "role_id": super_admin_role_id
    }

    res = client.post("/api/v1/users", json=payload, headers=headers)
    assert res.status_code == 409
    assert res.json()["success"] is False
    assert "already exists" in res.json()["message"]

def test_weak_password_validation():
    """
    Test weak password returns HTTP 422 validation failure.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    visitor_role_id = get_role_id("VISITOR")

    payload = {
        "first_name": "Weak",
        "last_name": "Pass",
        "email": "weak_pass@vizicheck.com",
        "password": "weak", # Fails length & character requirements
        "role_id": visitor_role_id
    }

    res = client.post("/api/v1/users", json=payload, headers=headers)
    assert res.status_code == 422
    assert res.json()["success"] is False

def test_unauthorized_access_by_visitor():
    """
    Test regular visitor attempting administrative user endpoint returns HTTP 403.
    """
    db = SessionLocal()
    try:
        role = db.query(Role).filter_by(name="VISITOR").first()
        user = User(
            email="visitor_test@vizicheck.com",
            first_name="Vis",
            last_name="itor",
            password_hash=hash_password("Password@123"),
            is_active=True,
            role_id=role.id
        )
        db.add(user)
        db.commit()

        login_res = client.post("/api/v1/auth/login", json={
            "email": "visitor_test@vizicheck.com",
            "password": "Password@123"
        })
        vis_token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {vis_token}"}

        # Attempt to list users
        res = client.get("/api/v1/users", headers=headers)
        assert res.status_code == 403
        assert res.json()["success"] is False
    finally:
        db.query(User).filter_by(email="visitor_test@vizicheck.com").delete()
        db.commit()
        db.close()

def test_cross_tenant_access_restriction():
    """
    Test Tenant Admin cannot manage user belonging to another tenant.
    """
    db = SessionLocal()
    try:
        # Create two distinct tenants
        tenant_a = Tenant(name="Tenant A", contact_person="A", contact_email="a@test.com", status=TenantStatus.ACTIVE)
        tenant_b = Tenant(name="Tenant B", contact_person="B", contact_email="b@test.com", status=TenantStatus.ACTIVE)
        db.add_all([tenant_a, tenant_b])
        db.flush()

        role_ta = db.query(Role).filter_by(name="TENANT_ADMIN").first()
        role_vis = db.query(Role).filter_by(name="VISITOR").first()

        # User A in Tenant A (Tenant Admin)
        admin_a = User(
            email="admin_a@tenanta.com",
            first_name="Admin",
            last_name="A",
            password_hash=hash_password("Password@123"),
            is_active=True,
            role_id=role_ta.id,
            tenant_id=tenant_a.id
        )
        # User B in Tenant B
        user_b = User(
            email="user_b@tenantb.com",
            first_name="User",
            last_name="B",
            password_hash=hash_password("Password@123"),
            is_active=True,
            role_id=role_vis.id,
            tenant_id=tenant_b.id
        )
        db.add_all([admin_a, user_b])
        db.commit()

        # Admin A logs in
        login_res = client.post("/api/v1/auth/login", json={
            "email": "admin_a@tenanta.com",
            "password": "Password@123"
        })
        token_a = login_res.json()["data"]["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Attempt to access User B (Tenant B)
        res = client.get(f"/api/v1/users/{user_b.id}", headers=headers_a)
        assert res.status_code in [403, 404]
    finally:
        db.query(User).filter(User.email.in_(["admin_a@tenanta.com", "user_b@tenantb.com"])).delete()
        db.query(Tenant).filter(Tenant.name.in_(["Tenant A", "Tenant B"])).delete()
        db.commit()
        db.close()

def test_invalid_user_id_and_missing_token():
    """
    Test non-existent user ID returns 404 and missing token returns 401.
    """
    token = get_super_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 404 for missing user ID
    res404 = client.get("/api/v1/users/999999", headers=headers)
    assert res404.status_code == 404

    # 401 for missing token
    res401 = client.get("/api/v1/users")
    assert res401.status_code == 401
