import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from config import settings
import database.session as db_session
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.models.role import Role
from app.core.password import hash_password
from app.core.jwt import create_access_token, create_refresh_token

client = TestClient(app)

def test_login_success():
    """
    Test successful login using default super admin credentials.
    """
    payload = {
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["message"] == "Login successful"
    assert "access_token" in res_json["data"]
    assert "refresh_token" in res_json["data"]
    assert res_json["data"]["token_type"] == "bearer"
    assert res_json["data"]["user"]["email"] == settings.DEFAULT_SUPER_ADMIN_EMAIL
    assert res_json["data"]["user"]["role_name"] == "SUPER_ADMIN"

def test_get_me_success():
    """
    Test retrieving user profile via GET /me endpoint using a valid access token.
    """
    # 1. Login to get access token
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    token = login_res.json()["data"]["access_token"]

    # 2. Call GET /me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_json = me_res.json()
    assert me_json["success"] is True
    assert me_json["data"]["email"] == settings.DEFAULT_SUPER_ADMIN_EMAIL
    assert "USER_CREATE" in me_json["data"]["permissions"]

def test_refresh_token_success():
    """
    Test refreshing JWT access token using a valid refresh token.
    """
    # 1. Login to get refresh token
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    refresh_token = login_res.json()["data"]["refresh_token"]

    # 2. Call POST /refresh
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    ref_json = ref_res.json()
    assert ref_json["success"] is True
    assert "access_token" in ref_json["data"]
    assert "refresh_token" in ref_json["data"]

def test_logout_success():
    """
    Test user logout endpoint recording audit log.
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    logout_json = logout_res.json()
    assert logout_json["success"] is True
    assert logout_json["message"] == "Logout successful"

def test_invalid_password():
    """
    Test login with wrong password returns HTTP 401.
    """
    response = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": "WrongPassword!123"
    })
    assert response.status_code == 401
    res_json = response.json()
    assert res_json["success"] is False
    assert "Invalid email or password" in res_json["message"]

def test_disabled_user():
    """
    Test login attempt for inactive user returns HTTP 401.
    """
    db: Session = db_session.SessionLocal()
    try:
        # Create an inactive user
        role = db.query(Role).filter_by(name="VISITOR").first()
        inactive_user = User(
            email="disabled_test@vizicheck.com",
            first_name="Disabled",
            last_name="User",
            password_hash=hash_password("Password@123"),
            is_active=False,
            role_id=role.id
        )
        db.add(inactive_user)
        db.commit()

        # Attempt login
        response = client.post("/api/v1/auth/login", json={
            "email": "disabled_test@vizicheck.com",
            "password": "Password@123"
        })
        assert response.status_code == 401
        res_json = response.json()
        assert res_json["success"] is False
        assert "inactive or disabled" in res_json["message"]
    finally:
        # Cleanup
        db.query(User).filter_by(email="disabled_test@vizicheck.com").delete()
        db.commit()
        db.close()

def test_suspended_tenant_user():
    """
    Test user attached to a suspended tenant organization returns HTTP 403.
    """
    db: Session = db_session.SessionLocal()
    try:
        # Create suspended tenant
        tenant = Tenant(
            name="Suspended Corp",
            contact_person="John Doe",
            contact_email="john@suspended.com",
            status=TenantStatus.SUSPENDED
        )
        db.add(tenant)
        db.flush()

        role = db.query(Role).filter_by(name="TENANT_ADMIN").first()
        tenant_user = User(
            email="tenant_admin@suspended.com",
            first_name="Tenant",
            last_name="Admin",
            password_hash=hash_password("Password@123"),
            is_active=True,
            tenant_id=tenant.id,
            role_id=role.id
        )
        db.add(tenant_user)
        db.commit()

        # Attempt login
        response = client.post("/api/v1/auth/login", json={
            "email": "tenant_admin@suspended.com",
            "password": "Password@123"
        })
        assert response.status_code == 403
        res_json = response.json()
        assert res_json["success"] is False
        assert "Tenant organization is inactive or suspended" in res_json["message"]
    finally:
        # Cleanup
        db.query(User).filter_by(email="tenant_admin@suspended.com").delete()
        db.query(Tenant).filter_by(name="Suspended Corp").delete()
        db.commit()
        db.close()

def test_invalid_and_expired_jwt():
    """
    Test access to protected route with invalid and expired tokens.
    """
    # Invalid JWT
    bad_res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert bad_res.status_code == 401
    assert bad_res.json()["success"] is False

    # Expired JWT
    expired_token = create_access_token(
        data={"sub": "1", "email": settings.DEFAULT_SUPER_ADMIN_EMAIL, "role": "SUPER_ADMIN", "permissions": []},
        expires_delta=timedelta(seconds=-10)
    )
    exp_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert exp_res.status_code == 401
    assert exp_res.json()["success"] is False
    assert "expired" in exp_res.json()["message"].lower()

def test_missing_authorization_header():
    """
    Test access to protected route without Authorization header returns HTTP 401.
    """
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    res_json = res.json()
    assert res_json["success"] is False
    assert "Missing Authorization header" in res_json["message"]
