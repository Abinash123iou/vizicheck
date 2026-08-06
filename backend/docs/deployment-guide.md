# ViziCheck Production Deployment & Operational Guide

This document outlines the environment configuration, database setup, deployment steps, and security guidelines for deploying the **ViziCheck** Smart Visitor Management backend service to production.

---

## 1. Prerequisites & System Requirements

- **Python**: `3.12+`
- **Database**: PostgreSQL `14+` (or SQLite `3.35+` for development/staging)
- **Process Manager**: Gunicorn with Uvicorn worker class (`uvicorn.workers.UvicornWorker`)
- **Reverse Proxy**: NGINX or AWS Application Load Balancer (ALB) with SSL/TLS termination
- **Containerization**: Docker & Docker Compose (Optional but recommended)

---

## 2. Environment Configuration

Create a production `.env` file based on `.env.example`:

```env
# General System Config
PROJECT_NAME=ViziCheck
VERSION=1.0.0
API_V1_STR=/api/v1
ENVIRONMENT=production
DEBUG=False

# Database Connection
DATABASE_URL=postgresql://vizicheck_user:SecurePassword123!@localhost:5432/vizicheck_db

# Security & JWT Configuration
SECRET_KEY=prod_super_secret_jwt_key_change_me_in_production_environment_998877
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Default Super Admin Credentials (Seeded on first migration)
DEFAULT_SUPER_ADMIN_EMAIL=superadmin@vizicheck.io
DEFAULT_SUPER_ADMIN_PASSWORD=SuperAdminPassword123!

# Security Policies
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30

# CORS Allowed Origins
BACKEND_CORS_ORIGINS=["https://app.vizicheck.io","https://admin.vizicheck.io"]
```

---

## 3. Database Migration & Setup

Execute Alembic migrations to apply all database tables, foreign key constraints, indexes, and initial seeds:

```bash
# Activate Virtual Environment
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Run Alembic Migrations
alembic upgrade head
```

---

## 4. Running the Production Server

### Using Gunicorn with Uvicorn Workers

```bash
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon
```

### Docker Deployment

```bash
# Build Docker image
docker build -t vizicheck-backend:v1.0.0 .

# Run Docker container
docker run -d \
    --name vizicheck-backend \
    -p 8000:8000 \
    --env-file .env \
    vizicheck-backend:v1.0.0
```

---

## 5. Verification & Health Monitoring

- **Health Check Endpoint**: `GET /health`
  - Expected Response: `HTTP 200 OK`
  - Content: `{"success": true, "data": {"status": "healthy", "database": "healthy"}}`
- **Interactive Swagger Docs**: `GET /docs` (Disable in production if restricted)
- **ReDoc Documentation**: `GET /redoc`

---

## 6. Background Schedulers & Cron Jobs

ViziCheck includes background jobs for system maintenance:
- **Overdue Check-In Cleanup**: Runs periodically to flag overstay visitors and notify hosts.
  ```bash
  python background_jobs/checkin_cleanup_scheduler.py
  ```
