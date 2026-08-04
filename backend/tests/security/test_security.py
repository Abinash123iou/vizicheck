import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from config import settings
import database.session as db_session
from app.models.user import User
from app.models.role import Role
from app.core.password import hash_password
from app.validators.security_validator import SecurityValidator
from app.core.exceptions import ValidationException, AccountLockedException
from app.repositories.security_repository import SecurityRepository

client = TestClient(app)

def test_password_policy_validation():
    """
    Test SecurityValidator.validate_password_strength against valid and invalid passwords.
    """
    # Valid password
    SecurityValidator.validate_password_strength("StrongP@ss123!")

    # Invalid: too short
    with pytest.raises(ValidationException) as exc_info:
        SecurityValidator.validate_password_strength("Short1!")
    assert "at least 8 characters" in str(exc_info.value.errors)

    # Invalid: missing uppercase
    with pytest.raises(ValidationException) as exc_info:
        SecurityValidator.validate_password_strength("lowercase123!")
    assert "uppercase letter" in str(exc_info.value.errors)

    # Invalid: missing special char
    with pytest.raises(ValidationException) as exc_info:
        SecurityValidator.validate_password_strength("NoSpecialChar123")
    assert "special character" in str(exc_info.value.errors)

def test_active_session_listing_and_revocation():
    """
    Test creating a session on login, listing sessions, and revoking a session.
    """
    # 1. Login to get access token
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List sessions
    sessions_res = client.get("/api/v1/security/sessions", headers=headers)
    assert sessions_res.status_code == 200
    sessions_data = sessions_res.json()["data"]
    assert len(sessions_data["sessions"]) >= 1

    session_to_revoke = sessions_data["sessions"][0]
    session_id = session_to_revoke["id"]

    # 3. Revoke session
    revoke_res = client.delete(f"/api/v1/security/sessions/{session_id}", headers=headers)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["success"] is True

    # 4. Requesting with revoked token should fail
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 401
    assert "revoked" in me_res.json()["message"].lower()

def test_account_lockout_mechanism():
    """
    Test account locking after 5 failed login attempts.
    """
    db: Session = db_session.SessionLocal()
    test_email = "lockout_test@vizicheck.com"
    try:
        role = db.query(Role).filter_by(name="VISITOR").first()
        user = User(
            email=test_email,
            first_name="Lockout",
            last_name="Tester",
            password_hash=hash_password("Password@123!"),
            is_active=True,
            role_id=role.id,
            failed_login_attempts=0
        )
        db.add(user)
        db.commit()

        # Perform 5 bad login attempts
        for i in range(5):
            res = client.post("/api/v1/auth/login", json={
                "email": test_email,
                "password": "WrongPassword!"
            })
            assert res.status_code == 401

        # 6th attempt should fail with Account Locked message
        locked_res = client.post("/api/v1/auth/login", json={
            "email": test_email,
            "password": "Password@123!"
        })
        assert locked_res.status_code == 401
        assert "temporarily locked" in locked_res.json()["message"]

    finally:
        db.query(User).filter_by(email=test_email).delete()
        db.commit()
        db.close()

def test_security_activity_logs_and_dashboard():
    """
    Test GET /api/v1/security/activity and GET /api/v1/security/dashboard endpoints.
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Security dashboard
    dashboard_res = client.get("/api/v1/security/dashboard", headers=headers)
    assert dashboard_res.status_code == 200
    dash_json = dashboard_res.json()
    assert dash_json["success"] is True
    assert "metrics" in dash_json["data"]

    # Security activity logs
    activity_res = client.get("/api/v1/security/activity", headers=headers)
    assert activity_res.status_code == 200
    act_json = activity_res.json()
    assert act_json["success"] is True
    assert "activities" in act_json["data"]
