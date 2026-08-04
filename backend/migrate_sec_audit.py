from sqlalchemy import text
from database.session import engine
from database.base import Base
import app.models  # ensure all SQLAlchemy models are registered

def migrate_database():
    print("Initializing missing database tables...")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Check failed_login_attempts on users
        res = conn.execute(text("SHOW COLUMNS FROM users LIKE 'failed_login_attempts'")).fetchone()
        if not res:
            print("Adding failed_login_attempts column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INT NOT NULL DEFAULT 0"))
            conn.commit()

        # Check locked_until on users
        res = conn.execute(text("SHOW COLUMNS FROM users LIKE 'locked_until'")).fetchone()
        if not res:
            print("Adding locked_until column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN locked_until DATETIME NULL"))
            conn.commit()

        # Check tenant_id on audit_logs
        res = conn.execute(text("SHOW COLUMNS FROM audit_logs LIKE 'tenant_id'")).fetchone()
        if not res:
            print("Adding tenant_id column to audit_logs table...")
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN tenant_id INT NULL"))
            try:
                conn.execute(text("ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL"))
            except Exception as e:
                print(f"Notice: FK constraint creation skipped or already exists: {e}")
            conn.commit()

    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
