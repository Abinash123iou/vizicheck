import sys
import os
import uuid
from datetime import datetime, timedelta, timezone, time as dtime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from database.session import SessionLocal, engine
from database.base import Base

import app.models  # Register all SQLAlchemy models

from app.models.tenant import Tenant, TenantStatus
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import role_permissions
from app.models.user import User
from app.models.visitor import Visitor, VisitorStatus, VerificationStatus, VerificationMethod
from app.models.visit_request import VisitRequest, VisitRequestStatus
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.qr_token import QRToken
from app.models.checkin import CheckIn, CheckInStatus, ScanLog, GateEventHistory, GateVerificationStatus
from app.models.availability import HostAvailability, AvailabilityException, Weekday, RecurrenceType, ExceptionType
from app.models.approval import Approval, ApprovalHistory, ApprovalStatus, ApprovalAction, ApprovalType
from app.models.notification import Notification, NotificationTemplate, NotificationPreference, NotificationStatus, NotificationChannel, NotificationType
from app.models.security import UserSession, SecurityLog
from app.models.audit_log import AuditLog
from app.constants.permissions import Permissions
from app.core.password import hash_password
from app.services.qr_service import QRService


def seed_manual_testing_data():
    """
    Idempotent database seeder for complete ViziCheck Manual API Testing.
    Populates 2 Enterprise Tenants (Capnis Infotech & TCS), 5 Roles, Host Availability, 
    Visitors, Visit Requests, Approvals, Passes, QR Tokens, Check-Ins, Notifications,
    Security Logs, and Audit Entries.
    """
    print("==================================================")
    print("STARTING VIZICHECK MANUAL API TESTING MOCK DATA SEEDER")
    print("==================================================")

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Permissions from Permissions constants
        perm_codes = [getattr(Permissions, attr) for attr in dir(Permissions) if not attr.startswith("__")]
        perm_map = {}
        for code in perm_codes:
            perm = db.query(Permission).filter_by(code=code).first()
            if not perm:
                perm = Permission(
                    code=code,
                    name=code.replace("_", " ").title(),
                    description=f"Permission code for {code}"
                )
                db.add(perm)
                db.flush()
            perm_map[code] = perm
        db.commit()

        # 2. Seed System Roles
        roles_spec = {
            "SUPER_ADMIN": list(perm_map.keys()),
            "TENANT_ADMIN": [
                Permissions.USER_CREATE, Permissions.USER_READ, Permissions.USER_UPDATE, Permissions.USER_DELETE,
                Permissions.USER_RESTORE, Permissions.USER_MANAGE_STATUS, Permissions.USER_RESET_PASSWORD,
                Permissions.PROFILE_VIEW, Permissions.PROFILE_UPDATE,
                Permissions.VISITOR_CREATE, Permissions.VISITOR_READ, Permissions.VISITOR_UPDATE, Permissions.VISITOR_DELETE,
                Permissions.VISITOR_VERIFY, Permissions.VISITOR_BLACKLIST, Permissions.VISITOR_EXPORT, Permissions.VISITOR_RESTORE, Permissions.VISITOR_STATUS,
                Permissions.VISIT_REQUEST_CREATE, Permissions.VISIT_REQUEST_READ, Permissions.VISIT_REQUEST_UPDATE, Permissions.VISIT_REQUEST_DELETE,
                Permissions.VISIT_REQUEST_APPROVE, Permissions.VISIT_REQUEST_REJECT, Permissions.VISIT_REQUEST_CANCEL, Permissions.VISIT_REQUEST_RESTORE, Permissions.VISIT_REQUEST_EXPORT,
                Permissions.PASS_GENERATE, Permissions.PASS_READ, Permissions.PASS_UPDATE, Permissions.PASS_DELETE, Permissions.PASS_REVOKE, Permissions.PASS_RESTORE, Permissions.PASS_EXPORT, Permissions.QR_VIEW, Permissions.QR_REGENERATE,
                Permissions.CHECKIN_CREATE, Permissions.CHECKIN_READ, Permissions.CHECKIN_MANUAL, Permissions.CHECKOUT_CREATE, Permissions.CHECKOUT_MANUAL, Permissions.CHECKIN_UNDO, Permissions.CHECKIN_EXPORT, Permissions.GATE_DASHBOARD_VIEW, Permissions.SCAN_LOGS_VIEW,
                Permissions.AVAILABILITY_CREATE, Permissions.AVAILABILITY_READ, Permissions.AVAILABILITY_UPDATE, Permissions.AVAILABILITY_DELETE,
                Permissions.APPROVAL_CREATE, Permissions.APPROVAL_READ, Permissions.APPROVAL_ACTION, Permissions.APPROVAL_DELEGATE, Permissions.APPROVAL_ESCALATE,
                Permissions.NOTIFICATION_SEND, Permissions.NOTIFICATION_READ, Permissions.NOTIFICATION_MANAGE_TEMPLATES, Permissions.NOTIFICATION_PREFERENCES,
                Permissions.REPORTS_READ, Permissions.REPORTS_EXPORT
            ],
            "SECURITY_OFFICER": [
                Permissions.PROFILE_VIEW, Permissions.PROFILE_UPDATE,
                Permissions.VISITOR_READ, Permissions.VISITOR_VERIFY, Permissions.VISITOR_BLACKLIST,
                Permissions.VISIT_REQUEST_READ, Permissions.PASS_READ, Permissions.PASS_REVOKE, Permissions.QR_VIEW, Permissions.QR_REGENERATE,
                Permissions.CHECKIN_CREATE, Permissions.CHECKIN_READ, Permissions.CHECKIN_MANUAL, Permissions.CHECKOUT_CREATE, Permissions.CHECKOUT_MANUAL, Permissions.CHECKIN_EXPORT, Permissions.GATE_DASHBOARD_VIEW, Permissions.SCAN_LOGS_VIEW,
                Permissions.NOTIFICATION_READ, Permissions.REPORTS_READ
            ],
            "HOST_USER": [
                Permissions.PROFILE_VIEW, Permissions.PROFILE_UPDATE,
                Permissions.VISITOR_CREATE, Permissions.VISITOR_READ,
                Permissions.VISIT_REQUEST_CREATE, Permissions.VISIT_REQUEST_READ, Permissions.VISIT_REQUEST_UPDATE, Permissions.VISIT_REQUEST_APPROVE, Permissions.VISIT_REQUEST_REJECT, Permissions.VISIT_REQUEST_CANCEL,
                Permissions.PASS_GENERATE, Permissions.PASS_READ,
                Permissions.AVAILABILITY_CREATE, Permissions.AVAILABILITY_READ, Permissions.AVAILABILITY_UPDATE, Permissions.AVAILABILITY_DELETE,
                Permissions.APPROVAL_CREATE, Permissions.APPROVAL_READ, Permissions.APPROVAL_ACTION,
                Permissions.NOTIFICATION_READ
            ],
            "RECEPTIONIST": [
                Permissions.PROFILE_VIEW, Permissions.PROFILE_UPDATE,
                Permissions.VISITOR_CREATE, Permissions.VISITOR_READ, Permissions.VISITOR_UPDATE,
                Permissions.VISIT_REQUEST_CREATE, Permissions.VISIT_REQUEST_READ,
                Permissions.PASS_GENERATE, Permissions.PASS_READ,
                Permissions.CHECKIN_CREATE, Permissions.CHECKIN_READ, Permissions.CHECKOUT_CREATE,
                Permissions.NOTIFICATION_READ, Permissions.GATE_DASHBOARD_VIEW
            ],
            "VISITOR": [
                Permissions.PROFILE_VIEW, Permissions.PROFILE_UPDATE,
                Permissions.VISIT_REQUEST_CREATE, Permissions.VISIT_REQUEST_READ, Permissions.VISIT_REQUEST_CANCEL,
                Permissions.PASS_READ, Permissions.NOTIFICATION_READ
            ]
        }

        role_map = {}
        for role_name, perms in roles_spec.items():
            role = db.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=f"System role for {role_name}")
                db.add(role)
                db.flush()

            # Update permissions mapping
            target_perms = [perm_map[p] for p in perms if p in perm_map]
            role.permissions = target_perms
            db.commit()
            db.refresh(role)
            role_map[role_name] = role

        password_hash = hash_password("TestPassword123!")
        super_admin_password_hash = hash_password("Admin@123")

        # 3. Seed Platform Super Admin
        super_admin = db.query(User).filter_by(email="admin@vizicheck.com").first()
        if not super_admin:
            super_admin = User(
                role_id=role_map["SUPER_ADMIN"].id,
                first_name="Super",
                last_name="Admin",
                email="admin@vizicheck.com",
                password_hash=super_admin_password_hash,
                phone="+919876543210",
                is_active=True
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
        else:
            super_admin.password_hash = super_admin_password_hash
            db.commit()

        # 4. Seed Tenant A: Capnis Infotech Pvt Ltd
        tenant_a = db.query(Tenant).filter_by(code="TEN-CAPNIS01").first()
        if not tenant_a:
            tenant_a = Tenant(
                name="Capnis Infotech Pvt Ltd",
                slug="capnis-infotech",
                code="TEN-CAPNIS01",
                contact_person="Rajesh Sharma",
                contact_email="contact@capnis.com",
                contact_phone="+918041234567",
                description="Building 4, Electronic City Phase 1, Bengaluru, Karnataka 560100",
                status=TenantStatus.ACTIVE
            )
            db.add(tenant_a)
            db.commit()
            db.refresh(tenant_a)

        # 5. Seed Tenant B: Tata Consultancy Services
        tenant_b = db.query(Tenant).filter_by(code="TEN-TCS02").first()
        if not tenant_b:
            tenant_b = Tenant(
                name="Tata Consultancy Services",
                slug="tata-consultancy",
                code="TEN-TCS02",
                contact_person="Ananya Verma",
                contact_email="contact@tcs.com",
                contact_phone="+912267778888",
                description="TCS House, Raveline Street, Fort, Mumbai, Maharashtra 400001",
                status=TenantStatus.ACTIVE
            )
            db.add(tenant_b)
            db.commit()
            db.refresh(tenant_b)

        tenants_list = [tenant_a, tenant_b]
        counts = {
            "tenants": len(tenants_list),
            "users": 1,  # super admin
            "hosts": 0,
            "security_officers": 0,
            "visitors": 0,
            "visit_requests": 0,
            "approvals": 0,
            "passes": 0,
            "qr_tokens": 0,
            "checkins": 0,
            "notifications": 0,
            "audit_logs": 0
        }

        created_user_credentials = [("Platform Super Admin", "admin@vizicheck.com", "TestPassword123!", "SUPER_ADMIN", "Global")]

        for tenant in tenants_list:
            print(f"\n--- Seeding Dataset for Tenant: '{tenant.name}' (ID: {tenant.id}, Code: {tenant.code}) ---")

            # Seed Users
            users_spec = [
                ("admin", f"admin.{tenant.slug}@vizicheck.com", "TENANT_ADMIN", "Tenant Admin", "Sharma"),
                ("arjun", f"arjun.kumar@{tenant.slug}.com", "HOST_USER", "Arjun", "Kumar"),
                ("priya", f"priya.sharma@{tenant.slug}.com", "HOST_USER", "Priya", "Sharma"),
                ("guard", f"security.{tenant.slug}@vizicheck.com", "SECURITY_OFFICER", "Vikram", "Singh"),
                ("frontdesk", f"reception.{tenant.slug}@vizicheck.com", "RECEPTIONIST", "Sneha", "Iyer")
            ]

            tenant_users = {}
            for key, email, role_name, fname, lname in users_spec:
                usr = db.query(User).filter_by(email=email).first()
                if not usr:
                    usr = User(
                        tenant_id=tenant.id,
                        role_id=role_map[role_name].id,
                        first_name=fname,
                        last_name=lname,
                        email=email,
                        password_hash=password_hash,
                        phone=f"+9198{tenant.id:02d}{len(tenant_users):04d}",
                        is_active=True
                    )
                    db.add(usr)
                    db.commit()
                    db.refresh(usr)
                tenant_users[key] = usr
                counts["users"] += 1
                if role_name == "HOST_USER":
                    counts["hosts"] += 1
                elif role_name == "SECURITY_OFFICER":
                    counts["security_officers"] += 1
                created_user_credentials.append((f"{fname} {lname}", email, "TestPassword123!", role_name, tenant.name))

            host1 = tenant_users["arjun"]
            host2 = tenant_users["priya"]

            # Seed Host Availability
            for host in [host1, host2]:
                for wday in [Weekday.MONDAY, Weekday.TUESDAY, Weekday.WEDNESDAY, Weekday.THURSDAY, Weekday.FRIDAY]:
                    sched = db.query(HostAvailability).filter_by(tenant_id=tenant.id, user_id=host.id, weekday=wday, is_deleted=False).first()
                    if not sched:
                        sched = HostAvailability(
                            tenant_id=tenant.id,
                            user_id=host.id,
                            weekday=wday,
                            start_time=dtime(9, 0, 0),
                            end_time=dtime(17, 0, 0),
                            break_start=dtime(13, 0, 0),
                            break_end=dtime(14, 0, 0),
                            max_visitors=5,
                            is_available=True,
                            recurrence_type=RecurrenceType.WEEKLY,
                            notes="Standard Enterprise Working Hours"
                        )
                        db.add(sched)
                        db.commit()

            # Seed Availability Exception (Leave for host2 on upcoming date)
            target_exc_date = datetime.now(timezone.utc).date() + timedelta(days=5)
            exc = db.query(AvailabilityException).filter_by(tenant_id=tenant.id, user_id=host2.id).first()
            if not exc:
                exc = AvailabilityException(
                    tenant_id=tenant.id,
                    user_id=host2.id,
                    title="Annual Personal Leave",
                    start_date=target_exc_date,
                    end_date=target_exc_date,
                    exception_type=ExceptionType.PERSONAL_LEAVE,
                    is_full_day=True,
                    notes="Annual Personal Leave"
                )
                db.add(exc)
                db.commit()

            # Seed Visitors (15 per tenant)
            visitors_list = []
            companies = ["Infosys Tech", "Wipro Digital", "Reliance Industries", "TCS Digital", "HCL Technologies"]
            for i in range(1, 16):
                vemail = f"visitor{i}.{tenant.slug}@example.com"
                vcode = f"VIS-{tenant.code}-{i:04d}"
                v = db.query(Visitor).filter(
                    Visitor.tenant_id == tenant.id,
                    (Visitor.email == vemail) | (Visitor.visitor_code == vcode)
                ).first()
                if not v:
                    status_val = VisitorStatus.BLACKLISTED if i == 15 else VisitorStatus.ACTIVE
                    verified_val = VerificationStatus.VERIFIED if i % 2 == 0 else VerificationStatus.PENDING
                    v = Visitor(
                        tenant_id=tenant.id,
                        visitor_code=vcode,
                        first_name=f"Visitor{i}",
                        last_name="Patel" if i % 2 == 0 else "Mukherjee",
                        email=vemail,
                        phone=f"+9197{tenant.id:02d}{i:04d}",
                        company=companies[i % len(companies)],
                        government_id_type="AADHAAR" if i % 2 == 0 else "PAN",
                        government_id_number=f"7890-1234-{tenant.id:02d}{i:02d}",
                        verification_status=verified_val,
                        verification_method=VerificationMethod.GOVT_ID if verified_val == VerificationStatus.VERIFIED else None,
                        status=status_val,
                        blacklist_reason="Safety policy non-compliance" if status_val == VisitorStatus.BLACKLISTED else None
                    )
                    db.add(v)
                    db.commit()
                    db.refresh(v)
                visitors_list.append(v)
                counts["visitors"] += 1

            # Seed Visit Requests (10 per tenant)
            now = datetime.now(timezone.utc)
            requests_list = []
            for i in range(1, 11):
                rcode = f"REQ-{tenant.code}-{i:04d}"
                vr = db.query(VisitRequest).filter_by(tenant_id=tenant.id, request_code=rcode).first()
                if not vr:
                    if i <= 4:
                        status_val = VisitRequestStatus.APPROVED
                    elif i <= 7:
                        status_val = VisitRequestStatus.PENDING
                    elif i <= 9:
                        status_val = VisitRequestStatus.REJECTED
                    else:
                        status_val = VisitRequestStatus.CANCELLED

                    target_host = host1 if i % 2 != 0 else host2
                    vr = VisitRequest(
                        tenant_id=tenant.id,
                        request_code=rcode,
                        visitor_id=visitors_list[i - 1].id,
                        host_id=target_host.id,
                        purpose="Enterprise Tech Review & Vendor Audit" if i % 2 == 0 else "Project Architecture Sync",
                        department="Engineering" if i % 2 == 0 else "Operations",
                        scheduled_start_time=now - timedelta(hours=i),
                        scheduled_end_time=now + timedelta(hours=8 - i),
                        status=status_val,
                        created_by=target_host.id,
                        approved_by=target_host.id if status_val == VisitRequestStatus.APPROVED else None,
                        approved_at=now - timedelta(hours=i) if status_val == VisitRequestStatus.APPROVED else None,
                        rejection_reason="Host unavailable at requested time" if status_val == VisitRequestStatus.REJECTED else None,
                        cancellation_reason="Visitor rescheduled meeting" if status_val == VisitRequestStatus.CANCELLED else None
                    )
                    db.add(vr)
                    db.commit()
                    db.refresh(vr)

                    # Seed Approval Workflow
                    acode = f"APP-2026-{tenant.code}-{i:04d}"
                    app_status_map = {
                        VisitRequestStatus.APPROVED: ApprovalStatus.APPROVED,
                        VisitRequestStatus.PENDING: ApprovalStatus.PENDING,
                        VisitRequestStatus.REJECTED: ApprovalStatus.REJECTED,
                        VisitRequestStatus.CANCELLED: ApprovalStatus.CANCELLED
                    }
                    app_status = app_status_map.get(vr.status, ApprovalStatus.PENDING)

                    approval = Approval(
                        tenant_id=tenant.id,
                        request_id=vr.id,
                        approval_code=acode,
                        approval_type=ApprovalType.SINGLE_LEVEL,
                        current_step=1,
                        total_steps=1,
                        current_approver_id=target_host.id,
                        status=app_status,
                        created_by_id=target_host.id
                    )
                    db.add(approval)
                    db.commit()
                    db.refresh(approval)
                    counts["approvals"] += 1

                    # Approval History Log
                    history = ApprovalHistory(
                        approval_id=approval.id,
                        tenant_id=tenant.id,
                        step_number=1,
                        actor_id=target_host.id,
                        action=ApprovalAction.APPROVE if app_status == ApprovalStatus.APPROVED else (ApprovalAction.REJECT if app_status == ApprovalStatus.REJECTED else ApprovalAction.CREATED),
                        previous_status=ApprovalStatus.PENDING,
                        new_status=app_status,
                        comments="Automated seed approval record"
                    )
                    db.add(history)
                    db.commit()

                requests_list.append(vr)
                counts["visit_requests"] += 1

            # Seed Visitor Passes & QR Tokens for Approved Visit Requests
            approved_reqs = [r for r in requests_list if r.status == VisitRequestStatus.APPROVED]
            passes_list = []
            for idx, req in enumerate(approved_reqs):
                pcode = f"VP-2026-{tenant.code}-{idx+1:04d}"
                vp = db.query(VisitorPass).filter_by(tenant_id=tenant.id, pass_code=pcode).first()
                if not vp:
                    vp_status = PassStatus.ACTIVE if idx < 2 else (PassStatus.USED if idx == 2 else PassStatus.REVOKED)
                    vp = VisitorPass(
                        uuid=str(uuid.uuid4()),
                        tenant_id=tenant.id,
                        pass_code=pcode,
                        visit_request_id=req.id,
                        visitor_id=req.visitor_id,
                        host_id=req.host_id,
                        valid_from=now - timedelta(hours=2),
                        valid_until=now + timedelta(hours=10),
                        status=vp_status,
                        latest_qr_version=1
                    )
                    db.add(vp)
                    db.commit()
                    db.refresh(vp)

                    # Generate cryptographically signed QR Token
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
                        is_active=(vp_status != PassStatus.REVOKED),
                        expires_at=vp.valid_until
                    )
                    db.add(qr)
                    db.commit()
                    counts["qr_tokens"] += 1

                passes_list.append(vp)
                counts["passes"] += 1

            # Seed Check-In / Check-Out Records
            if len(passes_list) >= 2:
                for idx in range(2):
                    vp = passes_list[idx]
                    chk = db.query(CheckIn).filter_by(pass_id=vp.id).first()
                    if not chk:
                        chk_status = CheckInStatus.CHECKED_IN if idx == 0 else CheckInStatus.CHECKED_OUT
                        chk = CheckIn(
                            tenant_id=tenant.id,
                            pass_id=vp.id,
                            visit_request_id=vp.visit_request_id,
                            visitor_id=vp.visitor_id,
                            host_id=vp.host_id,
                            checkin_time=now - timedelta(minutes=60 * (idx + 1)),
                            status=chk_status,
                            checkout_time=now - timedelta(minutes=10) if idx == 1 else None,
                            visit_duration_minutes=50.0 if idx == 1 else None,
                            visit_duration_seconds=3000 if idx == 1 else None,
                            gate_device_id=f"DEV-GATE-{tenant.code}-01",
                            scanner_name="Main Gate Scanner 1",
                            scanner_ip="192.168.1.100",
                            scanner_location="Main Lobby North Gate",
                            scanner_version="v2.1.0",
                            gate_name="North Gate",
                            gate_number="Gate 1",
                            verification_method="QR_SCAN",
                            checked_in_by=tenant_users["guard"].id,
                            checked_out_by=tenant_users["guard"].id if idx == 1 else None
                        )
                        db.add(chk)
                        db.commit()

                        # Scan log
                        slog = ScanLog(
                            tenant_id=tenant.id,
                            pass_id=vp.id,
                            raw_scanned_data=f"VIZICHECK:PASS:{vp.uuid}:V1:TEST_TOKEN",
                            status=GateVerificationStatus.SUCCESS,
                            message="QR Code scan verified successfully",
                            scanner_id=f"DEV-GATE-{tenant.code}-01",
                            ip_address="192.168.1.100"
                        )
                        db.add(slog)
                        db.commit()

                    counts["checkins"] += 1

            # Seed Notification Templates and Notifications
            tmpl = db.query(NotificationTemplate).filter_by(tenant_id=tenant.id, template_code="VISIT_APPROVED_EMBED").first()
            if not tmpl:
                tmpl = NotificationTemplate(
                    tenant_id=tenant.id,
                    name="Visit Request Approved",
                    template_code="VISIT_APPROVED_EMBED",
                    channel=NotificationChannel.EMAIL,
                    subject="Your Visit Request {{request_code}} Has Been Approved",
                    body="Dear {{visitor_name}}, your visit to {{tenant_name}} with host {{host_name}} is approved. Pass code: {{pass_code}}.",
                    is_active=True
                )
                db.add(tmpl)
                db.commit()

            notif = db.query(Notification).filter_by(tenant_id=tenant.id, recipient_email="visitor1." + tenant.slug + "@example.com").first()
            if not notif:
                notif = Notification(
                    tenant_id=tenant.id,
                    recipient_user_id=tenant_users["arjun"].id,
                    recipient_email="visitor1." + tenant.slug + "@example.com",
                    channel=NotificationChannel.EMAIL,
                    notification_type=NotificationType.VISIT_REQUEST_APPROVED,
                    title="Visit Request Approved",
                    message="Your visit request has been approved.",
                    status=NotificationStatus.DELIVERED,
                    sent_at=now - timedelta(minutes=30)
                )
                db.add(notif)
                db.commit()
            counts["notifications"] += 1

            # Seed Security Session & Audit Log
            sess = db.query(UserSession).filter_by(user_id=tenant_users["admin"].id, is_active=True).first()
            if not sess:
                sess = UserSession(
                    tenant_id=tenant.id,
                    user_id=tenant_users["admin"].id,
                    token_jti=str(uuid.uuid4()),
                    ip_address="127.0.0.1",
                    user_agent="PostmanRuntime/7.32.3",
                    device_fingerprint="FINGERPRINT_DESKTOP_001",
                    is_active=True,
                    expires_at=now + timedelta(hours=24)
                )
                db.add(sess)
                db.commit()

            aud = db.query(AuditLog).filter_by(tenant_id=tenant.id, action="TENANT_SEED_INIT").first()
            if not aud:
                aud = AuditLog(
                    tenant_id=tenant.id,
                    user_id=tenant_users["admin"].id,
                    module="SYSTEM",
                    action="TENANT_SEED_INIT",
                    entity_id=tenant.id,
                    ip_address="127.0.0.1"
                )
                db.add(aud)
                db.commit()
            counts["audit_logs"] += 1

        print("\n==================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("==================================================")
        print("\nSUMMARY STATS:")
        print(f"Tenants:           {counts['tenants']}")
        print(f"Users:             {counts['users']}")
        print(f"Hosts:             {counts['hosts']}")
        print(f"Security Officers: {counts['security_officers']}")
        print(f"Visitors:          {counts['visitors']}")
        print(f"Visit Requests:    {counts['visit_requests']}")
        print(f"Approvals:         {counts['approvals']}")
        print(f"Passes:            {counts['passes']}")
        print(f"QR Tokens:         {counts['qr_tokens']}")
        print(f"Check-ins:         {counts['checkins']}")
        print(f"Notifications:     {counts['notifications']}")
        print(f"Audit Logs:        {counts['audit_logs']}")

        print("\nTEST CREATED CREDENTIALS:")
        print(f"{'User Name':<25} | {'Email':<45} | {'Password':<20} | {'Role':<18} | {'Tenant'}")
        print("-" * 130)
        for name, email, pwd, role, tname in created_user_credentials:
            print(f"{name:<25} | {email:<45} | {pwd:<20} | {role:<18} | {tname}")
        print("=" * 130 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    seed_manual_testing_data()
