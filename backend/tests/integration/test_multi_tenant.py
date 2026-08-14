import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token
from app.models import User, Tenant, Role, Visitor, VisitRequest, VisitRequestStatus

client = TestClient(app)

@pytest.fixture
def multi_tenant_setup(db_session):
    role_admin = db_session.query(Role).filter_by(name="TENANT_ADMIN").first()

    tenant_a = db_session.query(Tenant).filter_by(code="ALPHA_MULTI").first()
    if not tenant_a:
        tenant_a = Tenant(name="Tenant Alpha Multi", code="ALPHA_MULTI", domain="alpha-multi-test.com", contact_person="Alpha Contact", contact_email="contact@alpha.com")
        db_session.add(tenant_a)
        db_session.commit()

    user_a = db_session.query(User).filter_by(email="admin@alpha.com").first()
    if not user_a:
        user_a = User(
            email="admin@alpha.com",
            first_name="Alpha",
            last_name="Admin",
            password_hash="hash",
            is_active=True,
            tenant_id=tenant_a.id,
            role_id=role_admin.id
        )
        db_session.add(user_a)

    tenant_b = db_session.query(Tenant).filter_by(code="BETA_MULTI").first()
    if not tenant_b:
        tenant_b = Tenant(name="Tenant Beta Multi", code="BETA_MULTI", domain="beta-multi-test.com", contact_person="Beta Contact", contact_email="contact@beta.com")
        db_session.add(tenant_b)
        db_session.commit()

    user_b = db_session.query(User).filter_by(email="admin@beta.com").first()
    if not user_b:
        user_b = User(
            email="admin@beta.com",
            first_name="Beta",
            last_name="Admin",
            password_hash="hash",
            is_active=True,
            tenant_id=tenant_b.id,
            role_id=role_admin.id
        )
        db_session.add(user_b)

    db_session.commit()

    visitor_b = db_session.query(Visitor).filter_by(visitor_code="VIS-BETA-01").first()
    if not visitor_b:
        visitor_b = Visitor(
            tenant_id=tenant_b.id,
            first_name="John",
            last_name="BetaVisitor",
            visitor_code="VIS-BETA-01",
            phone="+1999888777",
            email="john@betavisitor.com"
        )
        db_session.add(visitor_b)
        db_session.commit()

    token_a = create_access_token(data={"sub": str(user_a.id)})
    token_b = create_access_token(data={"sub": str(user_b.id)})

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "user_a_headers": {"Authorization": f"Bearer {token_a}"},
        "user_b_headers": {"Authorization": f"Bearer {token_b}"},
        "visitor_b": visitor_b
    }


def test_tenant_a_cannot_read_tenant_b_visitor(multi_tenant_setup):
    """Verify Tenant A user receives 403/404/cannot access Tenant B's visitor record."""
    headers_a = multi_tenant_setup["user_a_headers"]
    visitor_b_id = multi_tenant_setup["visitor_b"].id

    # Get specific visitor B using Tenant A headers
    response = client.get(f"/api/v1/visitors/{visitor_b_id}", headers=headers_a)
    assert response.status_code in [403, 404]

    # List visitors using Tenant A headers
    response_list = client.get("/api/v1/visitors", headers=headers_a)
    assert response_list.status_code == 200
    items = response_list.json()["data"]["items"]
    visitor_ids = [item["id"] for item in items]
    assert visitor_b_id not in visitor_ids


def test_tenant_a_cannot_update_tenant_b_visitor(multi_tenant_setup):
    """Verify Tenant A user cannot update Tenant B's visitor."""
    headers_a = multi_tenant_setup["user_a_headers"]
    visitor_b_id = multi_tenant_setup["visitor_b"].id

    update_payload = {"first_name": "HackedName"}
    response = client.put(f"/api/v1/visitors/{visitor_b_id}", json=update_payload, headers=headers_a)
    assert response.status_code in [403, 404]


def test_tenant_b_can_read_own_visitor(multi_tenant_setup):
    """Verify Tenant B user CAN read its own visitor record."""
    headers_b = multi_tenant_setup["user_b_headers"]
    visitor_b_id = multi_tenant_setup["visitor_b"].id

    response = client.get(f"/api/v1/visitors/{visitor_b_id}", headers=headers_b)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == visitor_b_id
