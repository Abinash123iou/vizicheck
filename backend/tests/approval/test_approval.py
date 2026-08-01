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
from app.models.permission import Permission
from app.constants.permissions import Permissions
from app.models.user import User
from app.models.visitor import Visitor, VisitorStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.approval import Approval, ApprovalHistory, ApprovalStatus, ApprovalType, ApprovalAction
from app.core.security import create_access_token
from app.core.password import hash_password


client = TestClient(fastapi_app)


@pytest.fixture
def approval_test_setup():
    db: Session = SessionLocal()
    uid = datetime.now().strftime("%f")

    # 1. Create Tenant
    tenant = Tenant(
        name=f"Approval Test Tenant {uid}",
        code=f"APPTEN-{uid[:4]}",
        slug=f"app-ten-{uid[:4]}",
        contact_person="Admin Contact",
        contact_email=f"contact.{uid}@apptest.com",
        domain=f"apptest{uid}.com",
        status=TenantStatus.ACTIVE
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # 2. Permissions & Roles
    permissions_list = [
        Permissions.APPROVAL_CREATE,
        Permissions.APPROVAL_READ,
        Permissions.APPROVAL_ACTION,
        Permissions.APPROVAL_DELEGATE,
        Permissions.APPROVAL_ESCALATE
    ]
    perm_objs = []
    for p_name in permissions_list:
        p_obj = db.query(Permission).filter_by(name=p_name).first()
        if not p_obj:
            p_obj = Permission(name=p_name, code=p_name, description=f"Permission {p_name}")
            db.add(p_obj)
            db.commit()
            db.refresh(p_obj)

        perm_objs.append(p_obj)

    admin_role = db.query(Role).filter_by(name="SUPER_ADMIN").first()
    if not admin_role:
        admin_role = Role(name="SUPER_ADMIN", description="Super Admin Role", permissions=perm_objs)
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
    else:
        for po in perm_objs:
            if po not in admin_role.permissions:
                admin_role.permissions.append(po)
        db.commit()

    employee_role = db.query(Role).filter_by(name="TENANT_ADMIN").first()
    if not employee_role:
        employee_role = Role(name="TENANT_ADMIN", description="Tenant Admin Role", permissions=perm_objs)
        db.add(employee_role)
        db.commit()
        db.refresh(employee_role)
    else:
        for po in perm_objs:
            if po not in employee_role.permissions:
                employee_role.permissions.append(po)
        db.commit()


    # 3. Create Admin User
    admin_user = User(
        tenant_id=tenant.id,
        role_id=admin_role.id,
        email=f"admin.{uid}@apptest.com",
        password_hash=hash_password("Password123!"),

        first_name="Admin",
        last_name="User",
        phone=f"+9198{uid[:8]}",
        is_active=True
    )
    db.add(admin_user)

    # 4. Create Host User
    host_user = User(
        tenant_id=tenant.id,
        role_id=employee_role.id,
        email=f"host.{uid}@apptest.com",
        password_hash=hash_password("Password123!"),

        first_name="Vikram",
        last_name="Host",
        phone=f"+9197{uid[:8]}",
        is_active=True
    )
    db.add(host_user)

    # 5. Create Delegate User
    delegate_user = User(
        tenant_id=tenant.id,
        role_id=employee_role.id,
        email=f"delegate.{uid}@apptest.com",
        password_hash=hash_password("Password123!"),

        first_name="Delegate",
        last_name="Approver",
        phone=f"+9196{uid[:8]}",
        is_active=True
    )
    db.add(delegate_user)

    db.commit()
    db.refresh(admin_user)
    db.refresh(host_user)
    db.refresh(delegate_user)

    # 6. Create Visitor
    visitor = Visitor(
        tenant_id=tenant.id,
        visitor_code=f"VIS-APP-{uid[:4]}",
        first_name="Rahul",
        last_name="Sharma",
        email=f"visitor.{uid}@guest.com",
        phone=f"+9195{uid[:8]}",
        company="Tech Corp",
        government_id_type="AADHAAR",
        government_id_number=f"7890-4567-{uid[:4]}",
        status=VisitorStatus.ACTIVE
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)

    # 7. Create Pending Visit Request
    start_dt = datetime.now() + timedelta(days=1)
    end_dt = start_dt + timedelta(hours=2)
    visit_request = VisitRequest(
        tenant_id=tenant.id,
        request_code=f"VR-APP-{uid[:4]}",
        visitor_id=visitor.id,
        host_id=host_user.id,
        purpose="Enterprise Client Meeting",
        scheduled_start_time=start_dt,
        scheduled_end_time=end_dt,
        status=VisitRequestStatus.PENDING
    )
    db.add(visit_request)
    db.commit()
    db.refresh(visit_request)

    # Tokens & Headers
    admin_token = create_access_token(data={"sub": str(admin_user.id), "email": admin_user.email, "tenant_id": tenant.id})
    host_token = create_access_token(data={"sub": str(host_user.id), "email": host_user.email, "tenant_id": tenant.id})

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    host_headers = {"Authorization": f"Bearer {host_token}"}


    yield {
        "tenant": tenant,
        "admin": admin_user,
        "host": host_user,
        "delegate": delegate_user,
        "visitor": visitor,
        "visit_request": visit_request,
        "admin_headers": admin_headers,
        "host_headers": host_headers
    }

    db.close()


def test_create_single_level_approval_success(approval_test_setup):
    setup = approval_test_setup
    payload = {
        "request_id": setup["visit_request"].id,
        "tenant_id": setup["tenant"].id,
        "approval_type": "SINGLE_LEVEL",
        "total_steps": 1,
        "current_approver_id": setup["host"].id,
        "notes": "Standard host approval requested"
    }

    res = client.post("/api/v1/approvals", json=payload, headers=setup["admin_headers"])
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["status"] == "PENDING"
    assert data["current_approver_id"] == setup["host"].id
    assert data["request_id"] == setup["visit_request"].id


def test_create_approval_duplicate_fails(approval_test_setup):
    setup = approval_test_setup
    payload = {
        "request_id": setup["visit_request"].id,
        "tenant_id": setup["tenant"].id
    }

    # First creation succeeds
    res1 = client.post("/api/v1/approvals", json=payload, headers=setup["admin_headers"])
    assert res1.status_code == 201

    # Duplicate creation fails
    res2 = client.post("/api/v1/approvals", json=payload, headers=setup["admin_headers"])
    assert res2.status_code == 400
    assert "already has an active pending approval" in res2.json()["errors"][0]


def test_approve_single_level_approval_workflow(approval_test_setup):
    setup = approval_test_setup

    # Create approval
    create_res = client.post("/api/v1/approvals", json={"request_id": setup["visit_request"].id}, headers=setup["admin_headers"])
    approval_id = create_res.json()["data"]["id"]

    # Action: APPROVE
    action_payload = {
        "action": "APPROVE",
        "comments": "Approved by Host Vikram"
    }

    act_res = client.patch(f"/api/v1/approvals/{approval_id}/action", json=action_payload, headers=setup["host_headers"])
    assert act_res.status_code == 200
    data = act_res.json()["data"]
    assert data["status"] == "APPROVED"

    # Verify visit request status transitioned to APPROVED in DB
    db = SessionLocal()
    req = db.query(VisitRequest).filter_by(id=setup["visit_request"].id).first()
    assert req.status == VisitRequestStatus.APPROVED
    assert req.approved_by == setup["host"].id
    db.close()


def test_reject_approval_workflow(approval_test_setup):
    setup = approval_test_setup

    create_res = client.post("/api/v1/approvals", json={"request_id": setup["visit_request"].id}, headers=setup["admin_headers"])
    approval_id = create_res.json()["data"]["id"]

    action_payload = {
        "action": "REJECT",
        "comments": "Host is traveling out of office"
    }

    act_res = client.patch(f"/api/v1/approvals/{approval_id}/action", json=action_payload, headers=setup["host_headers"])
    assert act_res.status_code == 200
    assert act_res.json()["data"]["status"] == "REJECTED"

    # Verify visit request status transitioned to REJECTED in DB
    db = SessionLocal()
    req = db.query(VisitRequest).filter_by(id=setup["visit_request"].id).first()
    assert req.status == VisitRequestStatus.REJECTED
    assert req.rejected_by == setup["host"].id
    db.close()


def test_delegate_approval_workflow(approval_test_setup):
    setup = approval_test_setup

    create_res = client.post("/api/v1/approvals", json={"request_id": setup["visit_request"].id}, headers=setup["admin_headers"])
    approval_id = create_res.json()["data"]["id"]

    action_payload = {
        "action": "DELEGATE",
        "comments": "Delegated to secondary host",
        "target_user_id": setup["delegate"].id
    }

    act_res = client.patch(f"/api/v1/approvals/{approval_id}/action", json=action_payload, headers=setup["host_headers"])
    assert act_res.status_code == 200
    data = act_res.json()["data"]
    assert data["status"] == "DELEGATED"
    assert data["current_approver_id"] == setup["delegate"].id


def test_escalate_approval_workflow(approval_test_setup):
    setup = approval_test_setup

    create_res = client.post("/api/v1/approvals", json={"request_id": setup["visit_request"].id}, headers=setup["admin_headers"])
    approval_id = create_res.json()["data"]["id"]

    action_payload = {
        "action": "ESCALATE",
        "comments": "Escalated to Admin Manager",
        "target_user_id": setup["admin"].id
    }

    act_res = client.patch(f"/api/v1/approvals/{approval_id}/action", json=action_payload, headers=setup["host_headers"])
    assert act_res.status_code == 200
    data = act_res.json()["data"]
    assert data["status"] == "ESCALATED"
    assert data["current_approver_id"] == setup["admin"].id


def test_multi_level_approval_workflow(approval_test_setup):
    setup = approval_test_setup

    payload = {
        "request_id": setup["visit_request"].id,
        "tenant_id": setup["tenant"].id,
        "approval_type": "MULTI_LEVEL",
        "total_steps": 2,
        "current_approver_id": setup["host"].id
    }

    create_res = client.post("/api/v1/approvals", json=payload, headers=setup["admin_headers"])
    approval_id = create_res.json()["data"]["id"]

    # Step 1 Approve -> Advances to Step 2
    step1_payload = {
        "action": "APPROVE",
        "comments": "Host approved step 1",
        "target_user_id": setup["admin"].id
    }
    step1_res = client.patch(f"/api/v1/approvals/{approval_id}/action", json=step1_payload, headers=setup["host_headers"])
    assert step1_res.status_code == 200
    data1 = step1_res.json()["data"]
    assert data1["current_step"] == 2
    assert data1["current_approver_id"] == setup["admin"].id

    # Step 2 Approve -> Finalizes workflow
    step2_payload = {
        "action": "APPROVE",
        "comments": "Admin approved step 2 final"
    }
    step2_res = client.patch(f"/api/v1/approvals/{approval_id}/action", json=step2_payload, headers=setup["admin_headers"])
    assert step2_res.status_code == 200
    data2 = step2_res.json()["data"]
    assert data2["status"] == "APPROVED"


def test_approval_history_and_stats(approval_test_setup):
    setup = approval_test_setup

    create_res = client.post("/api/v1/approvals", json={"request_id": setup["visit_request"].id}, headers=setup["admin_headers"])
    approval_id = create_res.json()["data"]["id"]

    # History timeline check
    hist_res = client.get(f"/api/v1/approvals/{approval_id}/history", headers=setup["admin_headers"])
    assert hist_res.status_code == 200
    history_items = hist_res.json()["data"]
    assert len(history_items) >= 1
    assert history_items[0]["action"] == "CREATED"

    # Stats check
    stats_res = client.get(f"/api/v1/approvals/stats?tenant_id={setup['tenant'].id}", headers=setup["admin_headers"])
    assert stats_res.status_code == 200
    stats = stats_res.json()["data"]
    assert stats["pending_count"] >= 1
