import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token
from app.models import User, Tenant, Role

from config import settings

client = TestClient(app)

@pytest.fixture
def super_admin_headers(db_session):
    user = db_session.query(User).filter_by(email=settings.DEFAULT_SUPER_ADMIN_EMAIL).first()
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_get_summary_report(super_admin_headers):
    response = client.get("/api/v1/reports/summary", headers=super_admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_visitors" in data["data"]
    assert "total_visit_requests" in data["data"]


def test_get_visitor_analytics_report(super_admin_headers):
    response = client.get("/api/v1/reports/visitors", headers=super_admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_visitors" in data["data"]


def test_get_gate_activity_report(super_admin_headers):
    response = client.get("/api/v1/reports/gate", headers=super_admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_checkins" in data["data"]


def test_export_summary_report_csv(super_admin_headers):
    response = client.get("/api/v1/reports/export", headers=super_admin_headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Tenant ID" in response.text
