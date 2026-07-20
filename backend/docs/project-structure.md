# backend/project-structure.md

# ViziCheck Backend Project Structure

## Purpose

This document defines the standard FastAPI project structure for ViziCheck.

Goals:

* Maintainable Codebase
* Modular Architecture
* Clear Separation of Concerns
* AI-Friendly Development
* Scalable Structure

---

# Architecture Style

Pattern:

Modular Monolith

Layers:

API Layer
   ↓
Service Layer
   ↓
Repository Layer
   ↓
Database Layer

---

# Root Structure

app/
├── api/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
├── middleware/
├── utils/
├── database/
├── tests/
├── main.py
└── config.py

---

# Detailed Structure

app/
│
├── api/
│   ├── auth.py
│   ├── users.py
│   ├── tenants.py
│   ├── visitors.py
│   ├── availability.py
│   ├── requests.py
│   ├── approvals.py
│   ├── passes.py
│   ├── qr.py
│   ├── security.py
│   ├── notifications.py
│   ├── reports.py
│   └── audit.py
│
├── core/
│   ├── security.py
│   ├── permissions.py
│   ├── exceptions.py
│   ├── dependencies.py
│   └── constants.py
│
├── models/
│   ├── role.py
│   ├── user.py
│   ├── tenant.py
│   ├── visitor.py
│   ├── availability.py
│   ├── visit_request.py
│   ├── approval.py
│   ├── pass.py
│   ├── qr_token.py
│   ├── checkin.py
│   ├── notification.py
│   └── audit_log.py
│
├── schemas/
│   ├── auth.py
│   ├── user.py
│   ├── tenant.py
│   ├── visitor.py
│   ├── availability.py
│   ├── request.py
│   ├── approval.py
│   ├── pass.py
│   ├── qr.py
│   ├── security.py
│   ├── notification.py
│   └── report.py
│
├── repositories/
│   ├── auth_repository.py
│   ├── user_repository.py
│   ├── tenant_repository.py
│   ├── visitor_repository.py
│   ├── request_repository.py
│   ├── approval_repository.py
│   ├── pass_repository.py
│   ├── qr_repository.py
│   ├── security_repository.py
│   ├── notification_repository.py
│   └── audit_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   ├── tenant_service.py
│   ├── visitor_service.py
│   ├── availability_service.py
│   ├── request_service.py
│   ├── approval_service.py
│   ├── pass_service.py
│   ├── qr_service.py
│   ├── security_service.py
│   ├── notification_service.py
│   ├── report_service.py
│   └── audit_service.py
│
├── middleware/
│   ├── auth_middleware.py
│   ├── audit_middleware.py
│   └── logging_middleware.py
│
├── database/
│   ├── session.py
│   ├── base.py
│   └── migrations/
│
├── utils/
│   ├── qr_generator.py
│   ├── validators.py
│   ├── date_utils.py
│   ├── response.py
│   └── logger.py
│
├── tests/
│   ├── auth/
│   ├── tenant/
│   ├── visitor/
│   ├── request/
│   ├── approval/
│   ├── pass/
│   └── security/
│
├── config.py
└── main.py

---

# Layer Responsibilities

## API Layer

Responsibilities:

* Route Definitions
* Request Validation
* Response Formatting
* Dependency Injection

No Business Logic Allowed.

---

## Service Layer

Responsibilities:

* Business Logic
* Workflow Execution
* Validation Rules
* Module Coordination

Main Business Layer.

---

## Repository Layer

Responsibilities:

* Database Operations
* CRUD Operations
* Query Handling

No Business Logic.

---

## Model Layer

Responsibilities:

* Database Entity Definitions
* Relationships
* Constraints

Uses SQLAlchemy ORM.

---

## Schema Layer

Responsibilities:

* Request Models
* Response Models
* Validation Models

Uses Pydantic.

---

# Naming Standards

Files:

snake_case

Examples:

user_service.py
visitor_repository.py

---

Classes:

PascalCase

Examples:

UserService
VisitorRepository

---

Functions:

snake_case

Examples:

create_visitor()
approve_request()
generate_qr_pass()

---

# Dependency Flow

API
 ↓
Service
 ↓
Repository
 ↓
Database

Never:

API → Repository

Never:

Repository → Service

---

# Configuration Management

Environment Variables:

DATABASE_URL

JWT_SECRET

JWT_ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES

APP_ENV

APP_NAME

---

# Development Rules

* One Service Per Module
* One Repository Per Module
* No Business Logic In Routes
* No Raw SQL In Services
* Use Dependency Injection
* Use Type Hints Everywhere
* Maintain Clean Separation

---

# Scalability Guidelines

Future Services:

Email Service

SMS Service

Push Notification Service

File Storage Service

Analytics Service

Can be added without changing existing architecture.

---

# AI Development Rules

When generating code:

* Follow folder structure exactly.
* Place business logic only in services.
* Use repositories for database access.
* Use schemas for validation.
* Use SQLAlchemy ORM.
* Follow FastAPI best practices.
* Generate modular, production-ready code.
