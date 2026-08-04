import csv
import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from config import settings
import database.session as db_session
from app.repositories.audit_repository import AuditRepository

client = TestClient(app)

def test_list_audit_logs():
    """
    Test GET /api/v1/audit endpoint with pagination and search parameters.
    """
    # 1. Login as Super Admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add an audit log entry
    db: Session = db_session.SessionLocal()
    try:
        AuditRepository.create_audit_log(
            db,
            user_id=1,
            action="TEST_ACTION",
            module="AUDIT_TEST",
            ip_address="127.0.0.1",
            new_value={"test": True}
        )
    finally:
        db.close()

    # 3. Query audit logs
    res = client.get("/api/v1/audit?module=AUDIT_TEST", headers=headers)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    assert "items" in res_json["data"]
    assert res_json["data"]["total"] >= 1
    assert res_json["data"]["items"][0]["module"] == "AUDIT_TEST"

def test_export_audit_logs_csv():
    """
    Test GET /api/v1/audit/export?format=csv returns CSV file response.
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/audit/export?format=csv", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=" in res.headers["content-disposition"]

    csv_reader = csv.reader(io.StringIO(res.text))
    rows = list(csv_reader)
    assert len(rows) >= 1  # Header row present
    assert rows[0] == [
        "ID", "Created At", "User ID", "User Email", "Tenant ID",
        "Module", "Action", "Entity ID", "IP Address", "Old Value", "New Value"
    ]

def test_export_audit_logs_json():
    """
    Test GET /api/v1/audit/export?format=json returns JSON file response.
    """
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.DEFAULT_SUPER_ADMIN_EMAIL,
        "password": settings.DEFAULT_SUPER_ADMIN_PASSWORD
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/audit/export?format=json", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/json"
    assert "attachment; filename=" in res.headers["content-disposition"]

    data = res.json()
    assert isinstance(data, list)
