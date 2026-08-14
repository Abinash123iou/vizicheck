import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token
from app.models import User, Tenant, Role, Permission

client = TestClient(app)

@pytest.fixture
def rbac_users(db_session):
    roles = {r.name: r for r in db_session.query(Role).all()}
    
    tenant = db_session.query(Tenant).first()
    if not tenant:
        tenant = Tenant(name="RBAC Test Tenant", code="RBAC_TENANT", domain="rbac.com")
        db_session.add(tenant)
        db_session.commit()

    users = {}
    for role_name in ["SUPER_ADMIN", "TENANT_ADMIN", "SECURITY_OFFICER", "HOST", "RECEPTIONIST"]:
        role = roles.get(role_name)
        if not role:
            role = Role(name=role_name, description=f"{role_name} Role")
            db_session.add(role)
            db_session.commit()
            
        email = f"user_{role_name.lower()}@rbac.com"
        user = db_session.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                first_name=role_name,
                last_name="Test",
                password_hash="hashed",
                is_active=True,
                tenant_id=tenant.id if role_name != "SUPER_ADMIN" else None,
                role_id=role.id
            )
            db_session.add(user)
            db_session.commit()

        token = create_access_token(data={"sub": str(user.id)})
        users[role_name] = {"user": user, "headers": {"Authorization": f"Bearer {token}"}}

    return users


def test_unauthenticated_requests_return_401():
    """Verify unauthenticated access to protected routes returns 401."""
    protected_urls = [
        "/api/v1/users",
        "/api/v1/tenants",
        "/api/v1/visitors",
        "/api/v1/visit-requests",
        "/api/v1/passes",
        "/api/v1/checkins/active",
        "/api/v1/availability",
        "/api/v1/approvals/pending",
        "/api/v1/notifications",
        "/api/v1/security/sessions",
        "/api/v1/audit",
        "/api/v1/reports/summary"
    ]
    for url in protected_urls:
        response = client.get(url)
        assert response.status_code == 401, f"Expected 401 for {url}, got {response.status_code}"


def test_host_user_forbidden_on_tenant_management(rbac_users):
    """Verify HOST user cannot manage or list tenants (403 Forbidden)."""
    headers = rbac_users["HOST"]["headers"]
    response = client.get("/api/v1/tenants", headers=headers)
    assert response.status_code == 403


def test_receptionist_forbidden_on_security_activity(rbac_users):
    """Verify RECEPTIONIST user cannot view security activity logs (403 Forbidden)."""
    headers = rbac_users["RECEPTIONIST"]["headers"]
    response = client.get("/api/v1/security/activity", headers=headers)
    assert response.status_code == 403


def test_super_admin_authorized_access(rbac_users):
    """Verify SUPER_ADMIN can access high-privilege routes."""
    headers = rbac_users["SUPER_ADMIN"]["headers"]
    response = client.get("/api/v1/tenants", headers=headers)
    assert response.status_code == 200
