import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from database.session import SessionLocal, engine
from database.base import Base
import app.models  # Register all SQLAlchemy models

from app.models.tenant import Tenant, TenantStatus
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.visitor import Visitor, VisitorStatus
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.qr_token import QRToken
from app.models.checkin import CheckIn, CheckInStatus, ScanLog, GateEventHistory, GateVerificationStatus
from app.core.password import hash_password
from app.services.qr_service import QRService


def seed_testing_data():
    """
    Idempotent database seeder for complete ViziCheck API Testing.
    Populates 2 Tenants, Users, Visitors, Visit Requests, Passes, QR Tokens, Check-Ins.
    """
    print("==================================================")
    print("STARTING VIZICHECK MOCK DATASEEDER FOR POSTMAN TEST SUITE")
    print("==================================================")

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Fetch or Verify System Roles
        role_map = {}
        for role_name in ["SUPER_ADMIN", "TENANT_ADMIN", "SECURITY_OFFICER", "VISITOR"]:
            role = db.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} system role")
                db.add(role)
                db.commit()
                db.refresh(role)
            role_map[role_name] = role.id

        password_hash = hash_password("TestPassword123!")

        # 2. Seed Super Admin (Platform-wide)
        super_admin = db.query(User).filter_by(email="admin@vizicheck.com").first()
        if not super_admin:
            super_admin = User(
                role_id=role_map["SUPER_ADMIN"],
                first_name="Super",
                last_name="Admin",
                email="admin@vizicheck.com",
                password_hash=password_hash,
                phone="+919876543210",
                is_active=True
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)


        # 3. Seed Tenant 1: Capnis Infotech Pvt Ltd
        tenant1 = db.query(Tenant).filter_by(code="TEN-CAPNIS01").first()
        if not tenant1:
            tenant1 = Tenant(
                name="Capnis Infotech Pvt Ltd",
                slug="capnis-infotech",
                code="TEN-CAPNIS01",
                contact_person="Rajesh Sharma",
                contact_email="contact@capnis.com",
                contact_phone="+918041234567",
                description="Building 4, Electronic City Phase 1, Bengaluru, Karnataka 560100",
                status=TenantStatus.ACTIVE
            )
            db.add(tenant1)
            db.commit()
            db.refresh(tenant1)

        # 4. Seed Tenant 2: Tata Consultancy Services
        tenant2 = db.query(Tenant).filter_by(code="TEN-TCS02").first()
        if not tenant2:
            tenant2 = Tenant(
                name="Tata Consultancy Services",
                slug="tata-consultancy",
                code="TEN-TCS02",
                contact_person="Ananya Verma",
                contact_email="contact@tcs.com",
                contact_phone="+912267778888",
                description="TCS House, Raveline Street, Fort, Mumbai, Maharashtra 400001",
                status=TenantStatus.ACTIVE
            )
            db.add(tenant2)
            db.commit()
            db.refresh(tenant2)


        tenants = [tenant1, tenant2]

        for tenant in tenants:
            print(f"\n--- Seeding Dataset for Tenant: '{tenant.name}' (ID: {tenant.id}) ---")

            # Seed Tenant Users (Tenant Admin, Host 1, Host 2, Security Officer, Receptionist)
            users_data = [
                ("admin", "admin." + tenant.slug + "@vizicheck.com", "TENANT_ADMIN"),
                ("vikram", "vikram.singh@" + tenant.slug + ".com", "SUPER_ADMIN"),
                ("priya", "priya.nair@" + tenant.slug + ".com", "SUPER_ADMIN"),
                ("guard", "security." + tenant.slug + "@vizicheck.com", "SECURITY_OFFICER"),
                ("frontdesk", "reception." + tenant.slug + "@vizicheck.com", "SECURITY_OFFICER")
            ]

            tenant_users = []
            for fname, email, rname in users_data:
                usr = db.query(User).filter_by(email=email).first()
                if not usr:
                    usr = User(
                        tenant_id=tenant.id,
                        role_id=role_map[rname],
                        first_name=fname.capitalize(),
                        last_name="Kumar" if fname != "priya" else "Nair",
                        email=email,
                        password_hash=password_hash,
                        phone=f"+9198{tenant.id:02d}{len(tenant_users):04d}",
                        is_active=True
                    )
                    db.add(usr)
                    db.commit()
                    db.refresh(usr)
                tenant_users.append(usr)


            host_user = tenant_users[1]

            # Seed 20 Visitors per Tenant
            visitors = []
            visitor_companies = ["Infosys Ltd", "Wipro Digital", "Reliance Jio", "HCL Tech", "Tech Mahindra"]
            for i in range(1, 21):
                vemail = f"visitor{i}.{tenant.id}@example.in"
                v = db.query(Visitor).filter_by(tenant_id=tenant.id, email=vemail).first()
                if not v:
                    v = Visitor(
                        tenant_id=tenant.id,
                        visitor_code=f"VIS-{tenant.code}-{i:04d}",
                        first_name=f"Visitor{i}",
                        last_name="Patel" if i % 2 == 0 else "Mukherjee",
                        email=vemail,
                        phone=f"+9197{tenant.id:02d}{i:04d}",
                        company=visitor_companies[i % len(visitor_companies)],
                        government_id_type="AADHAAR" if i % 2 == 0 else "PAN",
                        government_id_number=f"7890-1234-{tenant.id:02d}{i:02d}",
                        status=VisitorStatus.BLACKLISTED if i == 20 else VisitorStatus.ACTIVE
                    )
                    db.add(v)
                    db.commit()
                    db.refresh(v)
                visitors.append(v)


            # Seed 10 Visit Requests per Tenant
            now = datetime.now(timezone.utc)
            requests = []
            for i in range(1, 11):
                rcode = f"REQ-{tenant.code}-{i:04d}"
                vr = db.query(VisitRequest).filter_by(tenant_id=tenant.id, request_code=rcode).first()
                if not vr:
                    # 5 Approved, 3 Pending, 2 Rejected
                    if i <= 5:
                        status = VisitRequestStatus.APPROVED
                    elif i <= 8:
                        status = VisitRequestStatus.PENDING
                    else:
                        status = VisitRequestStatus.REJECTED

                    vr = VisitRequest(
                        tenant_id=tenant.id,
                        request_code=rcode,
                        visitor_id=visitors[i - 1].id,
                        host_id=host_user.id,
                        purpose="Product Demonstration & Technical Discussion" if i % 2 == 0 else "Vendor Audit",
                        department="Engineering" if i % 2 == 0 else "Human Resources",
                        scheduled_start_time=now - timedelta(hours=i),
                        scheduled_end_time=now + timedelta(hours=8 - i),
                        status=status,
                        created_by=host_user.id,
                        approved_by=host_user.id if status == VisitRequestStatus.APPROVED else None,
                        approved_at=now - timedelta(hours=i) if status == VisitRequestStatus.APPROVED else None
                    )

                    db.add(vr)
                    db.commit()
                    db.refresh(vr)
                requests.append(vr)

            # Seed 5 Visitor Passes for Approved Requests
            approved_requests = [r for r in requests if r.status == VisitRequestStatus.APPROVED]
            passes = []
            for idx, req in enumerate(approved_requests):
                pcode = f"VP-2026-{tenant.code}-{idx+1:04d}"
                vp = db.query(VisitorPass).filter_by(tenant_id=tenant.id, pass_code=pcode).first()
                if not vp:
                    vp_uuid = str(uuid.uuid4())
                    vp = VisitorPass(
                        uuid=vp_uuid,
                        tenant_id=tenant.id,
                        pass_code=pcode,
                        visit_request_id=req.id,
                        visitor_id=req.visitor_id,
                        host_id=req.host_id,
                        valid_from=now - timedelta(hours=2),
                        valid_until=now + timedelta(hours=10),
                        status=PassStatus.ACTIVE if idx < 3 else (PassStatus.USED if idx == 3 else PassStatus.REVOKED),
                        latest_qr_version=1
                    )

                    db.add(vp)
                    db.commit()
                    db.refresh(vp)

                    # Generate Active QR Token
                    token_jwt, claims, _ = QRService.generate_jwt_qr_token(
                        visitor_pass=vp,
                        version=1,
                        expires_at=vp.valid_until
                    )

                    formatted_qr = f"VIZICHECK:PASS:{vp.uuid}:V1:{token_jwt}"
                    qr = QRToken(
                        tenant_id=tenant.id,
                        pass_id=vp.id,
                        version=1,
                        token=formatted_qr,
                        is_active=True,
                        expires_at=vp.valid_until
                    )

                    db.add(qr)
                    db.commit()

                passes.append(vp)

            # Seed 2 CheckIn records
            if len(passes) >= 2:
                for idx in range(2):
                    vp = passes[idx]
                    chk = db.query(CheckIn).filter_by(pass_id=vp.id).first()
                    if not chk:
                        chk = CheckIn(
                            tenant_id=tenant.id,
                            pass_id=vp.id,
                            visit_request_id=vp.visit_request_id,
                            visitor_id=vp.visitor_id,
                            host_id=host_user.id,
                            checkin_time=now - timedelta(minutes=45 * (idx + 1)),
                            status=CheckInStatus.CHECKED_IN if idx == 0 else CheckInStatus.CHECKED_OUT,
                            checkout_time=now - timedelta(minutes=5) if idx == 1 else None,
                            visit_duration_minutes=40.0 if idx == 1 else None,
                            visit_duration_seconds=2400 if idx == 1 else None,
                            gate_device_id=f"DEV-GATE-{tenant.code}-01",
                            scanner_name="Main Gate Scanner 1",
                            scanner_ip="192.168.1.50",
                            scanner_location="Main Lobby Entrance",
                            scanner_version="v1.2.0",
                            gate_name="Main Gate",
                            gate_number="Gate 1",
                            verification_method="QR_SCAN",
                            checked_in_by=tenant_users[3].id
                        )
                        db.add(chk)
                        db.commit()

        print("\n==================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("All tenants, users, visitors, requests, passes, QR tokens, and check-ins generated.")
        print("==================================================")

    finally:
        db.close()


if __name__ == "__main__":
    seed_testing_data()
