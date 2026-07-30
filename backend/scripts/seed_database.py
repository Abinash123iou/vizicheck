import sys
import os
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from config import settings
from database.session import SessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.core.password import hash_password



# Define system roles
ROLES = [
    {"name": "SUPER_ADMIN", "description": "Highest privilege role. System and Platform administrator."},
    {"name": "TENANT_ADMIN", "description": "Tenant organization administrator. Can manage visits and availability."},
    {"name": "SECURITY_OFFICER", "description": "Security personnel at facility gate. Validates passes and handles check-in/out."},
    {"name": "VISITOR", "description": "External visitor. Can create and track own visit requests."},
]

# Define system permissions
PERMISSIONS = [
    # User Management
    {"code": "USER_CREATE", "name": "Create User", "description": "Create system users"},
    {"code": "USER_VIEW", "name": "View User", "description": "View system users"},
    {"code": "USER_UPDATE", "name": "Update User", "description": "Update system users"},
    {"code": "USER_DELETE", "name": "Delete User", "description": "Soft delete system users"},
    # Role Management
    {"code": "ROLE_VIEW", "name": "View Roles", "description": "View system roles and permission mapping"},
    {"code": "ROLE_UPDATE", "name": "Update Roles", "description": "Modify role to permission mappings"},
    # Tenant Management
    {"code": "TENANT_CREATE", "name": "Create Tenant", "description": "Create tenant organizations"},
    {"code": "TENANT_VIEW", "name": "View Tenant", "description": "View tenant details"},
    {"code": "TENANT_UPDATE", "name": "Update Tenant", "description": "Modify tenant details"},
    {"code": "TENANT_DELETE", "name": "Delete Tenant", "description": "Soft delete tenant organizations"},
    # Visitor Management
    {"code": "VISITOR_VIEW", "name": "View Visitor", "description": "View visitor profile details"},
    {"code": "VISITOR_UPDATE", "name": "Update Visitor", "description": "Modify visitor profile details"},
    # Availability
    {"code": "AVAILABILITY_CREATE", "name": "Create Availability", "description": "Define tenant availability slots"},
    {"code": "AVAILABILITY_VIEW", "name": "View Availability", "description": "View availability schedules"},
    {"code": "AVAILABILITY_UPDATE", "name": "Update Availability", "description": "Modify availability slots"},
    {"code": "AVAILABILITY_DELETE", "name": "Delete Availability", "description": "Remove availability slots"},
    # Visit Requests
    {"code": "REQUEST_CREATE", "name": "Create Visit Request", "description": "Submit a visit request"},
    {"code": "REQUEST_VIEW", "name": "View Visit Requests", "description": "View visit requests"},
    {"code": "REQUEST_UPDATE", "name": "Update Visit Request", "description": "Modify pending visit requests"},
    {"code": "REQUEST_CANCEL", "name": "Cancel Visit Request", "description": "Cancel submitted visit requests"},
    # Approval
    {"code": "APPROVAL_APPROVE", "name": "Approve Request", "description": "Approve visit requests"},
    {"code": "APPROVAL_REJECT", "name": "Reject Request", "description": "Reject visit requests"},
    # Pass Management
    {"code": "PASS_GENERATE", "name": "Generate Pass", "description": "Generate visitor passes after approval"},
    {"code": "PASS_VIEW", "name": "View Pass", "description": "View visitor passes"},
    {"code": "PASS_REVOKE", "name": "Revoke Pass", "description": "Revoke active visitor passes"},
    # QR Verification
    {"code": "QR_VALIDATE", "name": "Validate QR Code", "description": "Scan and validate visitor QR pass"},
    # Gate Security & Check-In
    {"code": "CHECKIN_CREATE", "name": "Check-in Visitor", "description": "Record visitor entry via QR scan"},
    {"code": "CHECKIN_READ", "name": "View Check-in Records", "description": "View check-in/out event history"},
    {"code": "CHECKIN_MANUAL", "name": "Manual Check-in", "description": "Perform manual check-in override"},
    {"code": "CHECKOUT_CREATE", "name": "Check-out Visitor", "description": "Record visitor exit via QR scan"},
    {"code": "CHECKOUT_MANUAL", "name": "Manual Check-out", "description": "Perform manual check-out override"},
    {"code": "CHECKIN_UNDO", "name": "Undo Check-in", "description": "Revert visitor check-in state"},
    {"code": "CHECKIN_EXPORT", "name": "Export Check-in Records", "description": "Export check-in logs to CSV"},
    {"code": "GATE_DASHBOARD_VIEW", "name": "View Gate Dashboard", "description": "Access live gate occupancy dashboard"},
    {"code": "SCAN_LOGS_VIEW", "name": "View Scan Analytics", "description": "View QR scan failure & success logs"},
    # Reports
    {"code": "REPORT_VIEW", "name": "View Reports", "description": "View analytics and dashboard metrics"},
    {"code": "REPORT_EXPORT", "name": "Export Reports", "description": "Export reports to PDF or Excel"},
    # Notifications
    {"code": "NOTIFICATION_VIEW", "name": "View Notifications", "description": "View system notifications"},
    # Audit Logs
    {"code": "AUDIT_VIEW", "name": "View Audit Logs", "description": "View system audit logs"},
]

# Define permission matrices for each role
ROLE_PERMISSIONS = {
    "SUPER_ADMIN": [p["code"] for p in PERMISSIONS],  # All permissions
    "TENANT_ADMIN": [
        "REQUEST_VIEW",
        "APPROVAL_APPROVE",
        "APPROVAL_REJECT",
        "PASS_VIEW",
        "AVAILABILITY_CREATE",
        "AVAILABILITY_VIEW",
        "AVAILABILITY_UPDATE",
        "AVAILABILITY_DELETE",
        "CHECKIN_CREATE",
        "CHECKIN_READ",
        "CHECKIN_MANUAL",
        "CHECKOUT_CREATE",
        "CHECKOUT_MANUAL",
        "CHECKIN_UNDO",
        "CHECKIN_EXPORT",
        "GATE_DASHBOARD_VIEW",
        "SCAN_LOGS_VIEW",
        "REPORT_VIEW",
        "NOTIFICATION_VIEW",
    ],
    "SECURITY_OFFICER": [
        "REQUEST_VIEW",
        "PASS_VIEW",
        "QR_VALIDATE",
        "CHECKIN_CREATE",
        "CHECKIN_READ",
        "CHECKIN_MANUAL",
        "CHECKOUT_CREATE",
        "CHECKOUT_MANUAL",
        "CHECKIN_EXPORT",
        "GATE_DASHBOARD_VIEW",
        "SCAN_LOGS_VIEW",
        "REPORT_VIEW",
        "NOTIFICATION_VIEW",
    ],
    "VISITOR": [
        "REQUEST_CREATE",
        "REQUEST_VIEW",
        "REQUEST_CANCEL",
        "PASS_VIEW",
        "VISITOR_UPDATE",
        "NOTIFICATION_VIEW",
    ],
}


def seed():
    db: Session = SessionLocal()
    try:
        print("Starting database seeding...")
        
        # 1. Seed Roles
        db_roles = {}
        roles_created = 0
        for role_data in ROLES:
            role = db.query(Role).filter_by(name=role_data["name"]).first()
            if not role:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
                db.add(role)
                db.flush()
                roles_created += 1
            db_roles[role_data["name"]] = role
        print(f"Roles seeded: {roles_created} new roles created.")

        # 2. Seed Permissions
        db_permissions = {}
        permissions_created = 0
        for perm_data in PERMISSIONS:
            perm = db.query(Permission).filter_by(code=perm_data["code"]).first()
            if not perm:
                perm = Permission(
                    code=perm_data["code"],
                    name=perm_data["name"],
                    description=perm_data["description"],
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
                db.add(perm)
                db.flush()
                permissions_created += 1
            else:
                # Update name or description if they changed in our seeding script definition
                perm.name = perm_data["name"]
                perm.description = perm_data["description"]
            db_permissions[perm_data["code"]] = perm
        print(f"Permissions seeded: {permissions_created} new permissions created.")

        # 3. Associate Permissions with Roles (Idempotent update)
        mappings_updated = 0
        for role_name, perm_codes in ROLE_PERMISSIONS.items():
            role = db_roles[role_name]
            current_perm_ids = {p.id for p in role.permissions}
            target_perms = [db_permissions[code] for code in perm_codes if code in db_permissions]
            target_perm_ids = {p.id for p in target_perms}

            # If the set of permissions mapped has changed, update it
            if current_perm_ids != target_perm_ids:
                role.permissions = target_perms
                db.flush()
                mappings_updated += 1
        print(f"Role-Permission mappings updated/assigned for {mappings_updated} roles.")

        # 4. Create default Super Admin Account (Idempotent)
        admin_email = settings.DEFAULT_SUPER_ADMIN_EMAIL
        admin_password = settings.DEFAULT_SUPER_ADMIN_PASSWORD
        super_admin_role = db_roles["SUPER_ADMIN"]

        admin_user = db.query(User).filter_by(email=admin_email).first()
        admin_created = False
        if not admin_user:
            admin_user = User(
                role_id=super_admin_role.id,
                first_name="Super",
                last_name="Admin",
                email=admin_email,
                password_hash=hash_password(admin_password),
                is_active=True,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            db.add(admin_user)
            admin_created = True
            print(f"Super Admin account created: {admin_email}")
        else:
            # Optionally update password hash if it has changed to match env settings
            # We will re-hash and update if needed, but for simplicity let's update password
            admin_user.password_hash = hash_password(admin_password)
            admin_user.is_active = True
            print(f"Super Admin account updated (active and password reset): {admin_email}")

        db.commit()
        
        # Output Concise Execution Summary as requested
        print("\n" + "="*50)
        print("DATABASE SEED COMPLETED SUCCESSFULLY")
        print("="*50)
        print(f"Roles: {len(db_roles)} total system roles verified.")
        print(f"Permissions: {len(db_permissions)} total permissions verified.")
        print(f"Role-Permission mappings verified for all roles.")
        print(f"Super Admin user verified: {admin_email}")
        print("="*50 + "\n")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
