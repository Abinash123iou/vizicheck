import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.session as db_session
from main import app
from app.core.dependencies import get_db
from database.base import Base
from app.models import (
    Role, Permission, Tenant, TenantStatus, User, AuditLog, UserSession, SecurityLog
)
from app.core.password import hash_password
from config import settings

from sqlalchemy import event

# Create SQLite in-memory test engine with StaticPool to share connection across threads/sessions
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(test_engine, "connect")
def add_sqlite_concat(dbapi_connection, connection_record):
    dbapi_connection.create_function("concat", -1, lambda *args: "".join(str(a) for a in args if a is not None))

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Globally override db_session.SessionLocal and db_session.engine
db_session.engine = test_engine
db_session.SessionLocal = TestSessionLocal

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Setup in-memory SQLite database tables and seed required initial roles, permissions & super admin user.
    """
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    try:
        # Seed Permissions
        perm_codes = ["USER_CREATE", "USER_READ", "USER_UPDATE", "USER_DELETE", "TENANT_READ", "SECURITY_READ"]
        permissions_objs = []
        for code in perm_codes:
            perm = db.query(Permission).filter_by(code=code).first()
            if not perm:
                perm = Permission(name=code, code=code, description=f"Permission {code}")
                db.add(perm)
                db.flush()
            permissions_objs.append(perm)

        # Seed Roles
        roles_data = [
            ("SUPER_ADMIN", "System Super Administrator"),
            ("TENANT_ADMIN", "Tenant Administrator"),
            ("SECURITY_OFFICER", "Security Officer"),
            ("HOST", "Host Employee"),
            ("VISITOR", "Visitor User")
        ]
        roles_dict = {}
        for role_name, desc in roles_data:
            role = db.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=desc)
                if role_name == "SUPER_ADMIN":
                    role.permissions = permissions_objs
                db.add(role)
                db.flush()
            roles_dict[role_name] = role

        # Seed Default Super Admin User
        admin_email = settings.DEFAULT_SUPER_ADMIN_EMAIL
        admin = db.query(User).filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                first_name="Super",
                last_name="Admin",
                password_hash=hash_password(settings.DEFAULT_SUPER_ADMIN_PASSWORD),
                is_active=True,
                role_id=roles_dict["SUPER_ADMIN"].id
            )
            db.add(admin)

        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
