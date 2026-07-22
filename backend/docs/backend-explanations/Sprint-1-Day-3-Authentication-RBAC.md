# Backend Explanation – Sprint 1 Day 3: Authentication & RBAC Foundation

## Overview
This document provides a comprehensive technical overview of the Authentication and Role-Based Access Control (RBAC) foundation implemented during Sprint 1 Day 3 for **ViziCheck**. It serves as an architectural blueprint, design decision log, security reference, and interview preparation guide.

---

## 1. Authentication Architecture

ViziCheck implements a clean, layered multi-tenant authentication system designed around SOLID principles and Clean Architecture:

```
Client (Web / Mobile)
   │
   ▼
API Router (`backend/app/api/routes/auth.py`)
   │
   ▼
Pydantic Validation (`backend/app/schemas/`)
   │
   ▼
Authentication Service (`backend/app/services/auth_service.py`)
   │
   ├──► Security Module (`backend/app/core/security.py`, `jwt.py`, `password.py`)
   │
   ├──► User Repository (`backend/app/repositories/user_repository.py`)
   │
   └──► Auth Repository (`backend/app/repositories/auth_repository.py`)
```

### Layer Separation Rules
1. **API Routers (Controllers)**: Thin controllers. Responsible strictly for endpoint declaration, Pydantic schema validation, extracting client metadata (IP address), calling services, and wrapping results in standard response envelopes.
2. **Services**: Encapsulate all business rules and workflows (password validation, status verification, token issuance, audit logging).
3. **Repositories**: Communicate directly with the database via SQLAlchemy ORM. They handle query building, eager loading of relations (`role`, `permissions`, `tenant`), and returning domain entities. No HTTP exceptions or token operations exist in repositories.
4. **Core Security**: High-performance cryptographic operations (bcrypt password hashing and HMAC-SHA256 JWT signature management).

---

## 2. JWT Flow & Payload Specifications

### Token Lifecycle
1. **Access Tokens**: Short-lived tokens (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`) passed in `Authorization: Bearer <token>` headers to authenticate stateless REST API requests.
2. **Refresh Tokens**: Long-lived tokens (`REFRESH_TOKEN_EXPIRE_MINUTES = 10080` / 7 days) used at `POST /api/v1/auth/refresh` to obtain new token pairs without requiring re-entry of user credentials.

### JWT Payload Schema
All JWT tokens issued by ViziCheck contain the following standard claims:

```json
{
  "sub": "1",
  "email": "admin@vizicheck.com",
  "role": "SUPER_ADMIN",
  "tenant_id": null,
  "permissions": [
    "USER_CREATE",
    "USER_VIEW",
    "TENANT_CREATE",
    "VISITOR_VIEW",
    "..."
  ],
  "token_type": "access",
  "iat": 1774209600,
  "exp": 1774213200
}
```

> [!CAUTION]
> **Data Security Constraint**: JWT payloads are base64url-encoded and readable by any client. Passwords, password hashes, phone numbers, or personal identifying information (PII) are strictly prohibited from token claims.

---

## 3. Module Breakdown & Responsibilities

### 1. `security.py`, `password.py`, `jwt.py`, `auth.py` (`backend/app/core/`)
- **Purpose**: Low-level cryptographic and security infrastructure.
- **Responsibilities**:
  - `password.py`: `hash_password` and `verify_password` utilizing `bcrypt` via `passlib` with 72-byte string safe handling and `bcrypt` 4.x compatibility patches.
  - `jwt.py`: `create_access_token`, `create_refresh_token`, and `decode_token` with signature verification, expiration check, and custom exception mapping (`ExpiredTokenException`, `InvalidTokenException`).
  - `auth.py`: OAuth2 password bearer scheme instantiation and header extraction.
  - `security.py`: Unified security interface facade.

### 2. Schemas (`login.py`, `token.py`, `auth.py` in `backend/app/schemas/`)
- **Purpose**: Data Transfer Objects (DTOs) and API request/response validation.
- **Key Models**:
  - `LoginRequest`: Validates incoming email and password.
  - `LoginResponseData`: Access token, refresh token, token type, user profile.
  - `TokenResponseData`: Token pair returned on refresh.
  - `UserProfileResponse`: Complete representation of user, assigned role, tenant name, permissions, and timestamps.
  - `ResponseEnvelope[T]`: Unified API response envelope `{ "success": bool, "message": str, "data": T, "errors": list }`.

### 3. `user_repository.py` & `auth_repository.py` (`backend/app/repositories/`)
- **Purpose**: Database persistence layer.
- **Responsibilities**:
  - `UserRepository`: Queries active non-soft-deleted users by email or ID, eagerly loading `role`, `role.permissions`, and `tenant`. Updates `last_login` timestamp.
  - `AuthRepository`: Inserts structured audit records into `audit_logs` for `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, and `TOKEN_REFRESH` events.

### 4. `auth_service.py` (`backend/app/services/`)
- **Purpose**: Orchestrates all authentication and RBAC workflows.
- **Key Methods**:
  - `login(...)`: Coordinates email lookup, password verification, active user check, active tenant check, token generation, last login timestamp update, and audit log generation.
  - `refresh_token(...)`: Decodes refresh token, validates claims, verifies user & tenant state, generates new tokens, and logs token refresh events.
  - `logout(...)`: Logs logout event in audit table.
  - `verify_user_status(...)`: Raises `UserInactiveException` if `is_active` is False or user is soft-deleted.
  - `verify_tenant_status(...)`: Raises `TenantInactiveException` if associated tenant is suspended or inactive.

### 5. Authentication API (`backend/app/api/routes/auth.py`)
- **Purpose**: HTTP route handlers exposing REST endpoints under `/api/v1/auth`.
- **Endpoints**:
  - `POST /login`: Receives `LoginRequest`, invokes `AuthService.login`, returns standard response envelope.
  - `POST /refresh`: Receives `RefreshTokenRequest`, invokes `AuthService.refresh_token`.
  - `POST /logout`: Enforces authenticated user, invokes `AuthService.logout`.
  - `GET /me`: Enforces authenticated user, returns current user's profile and granted permission codes.

### 6. RBAC & Dependencies (`dependencies.py`, `permissions.py`)
- **Purpose**: Authorization and dependency injection middleware.
- **Dependencies**:
  - `get_current_user`: Decodes JWT header, validates signature/token_type, fetches user from database.
  - `get_current_active_user`: Enforces user active and tenant active checks.
  - `get_current_super_admin`: Restricts access to `SUPER_ADMIN` role.
  - `get_current_tenant_admin`: Restricts access to `TENANT_ADMIN` or `SUPER_ADMIN`.
  - `get_current_security_officer`: Restricts access to `SECURITY_OFFICER`, `TENANT_ADMIN`, or `SUPER_ADMIN`.
  - `PermissionChecker`: Custom callable dependency verifying specific permission code (e.g. `USER_CREATE`, `VISITOR_VIEW`). `SUPER_ADMIN` automatically bypasses permission checks.

### 7. Middleware (`backend/app/middleware/auth.py`)
- **Purpose**: Global request processing.
- **Behavior**: Inspects incoming `Authorization: Bearer` headers, decodes token claims, and attaches `request.state.user` and `request.state.tenant_id` context to the request.

---

## 4. Response Standardization

All responses (both successful responses and exception errors) return the unified standard JSON envelope:

### Success Response Example
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "first_name": "Super",
      "last_name": "Admin",
      "email": "admin@vizicheck.com",
      "phone": null,
      "is_active": true,
      "role_id": 1,
      "role_name": "SUPER_ADMIN",
      "tenant_id": null,
      "tenant_name": null,
      "permissions": ["USER_CREATE", "USER_VIEW", "..."],
      "last_login": "2026-07-22T14:14:48",
      "created_at": "2026-07-22T14:14:48"
    }
  },
  "errors": null
}
```

### Error Response Example (HTTP 401 Unauthenticated)
```json
{
  "success": false,
  "message": "Invalid email or password",
  "data": null,
  "errors": [
    "Invalid email or password"
  ]
}
```

---

## 5. Security Considerations & Best Practices

1. **Password Hashing**: Uses `bcrypt` with automated salt generation. Passwords are never stored in plaintext.
2. **Environment Secret Management**: `JWT_SECRET` is loaded strictly from environment variables (`.env`).
3. **Stateless Authorization**: JWT signatures prevent token tampering. Tokens are verified on every protected request.
4. **Tenant Isolation**: `tenant_id` is embedded in JWT claims and request state, ensuring cross-tenant data access is blocked.
5. **Audit Trail**: Every login attempt (successful or failed), token refresh, and logout is recorded in `audit_logs` with IP address and timestamp.
6. **Graceful Error Envelope**: Stack traces are never exposed to clients; domain exceptions return structured, client-friendly error envelopes.

---

## 6. Scalability Considerations

- **Stateless Verification**: JWT verification requires zero database queries if token claims contain user role and permission arrays, enabling high throughput microservices.
- **Database Eager Loading**: Database queries use `joinedload` to fetch User, Role, Permissions, and Tenant in a single optimized SQL query, eliminating N+1 query problems.
- **Connection Pooling**: SQLAlchemy engine uses `pool_pre_ping=True` with pool size 10 and max overflow 20 for concurrent connection management.

---

## 7. Interview Explanation

When asked to explain the Authentication and RBAC architecture in an interview:

> *"In ViziCheck, I built a Clean Architecture-compliant authentication system using FastAPI, SQLAlchemy, PyJWT/python-jose, and Bcrypt. We enforce a strict separation of concerns where thin controllers validate requests and format standard response envelopes (`{ success, message, data, errors }`), services handle business validation like user/tenant active status check and audit logging, and repositories deal exclusively with ORM data access using eager loading to prevent N+1 queries.*
>
> *Authentication relies on JWT access and refresh token pairs. Claims include the user ID, email, role, tenant ID, and granted permission codes. Authorization is powered by FastAPI dependency injection with custom `PermissionChecker` and `RoleChecker` callables that evaluate user claims dynamically, allowing Super Admins full access while enforcing fine-grained RBAC for Tenant Admins and Security Officers."*
