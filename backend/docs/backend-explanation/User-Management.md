# Sprint 1 – Day 4: User Management Module Documentation

## 1. Executive Summary & Overview
The **User Management Module** provides a secure, production-grade API for managing user identities, profile attributes, status transitions, role permissions, and tenant isolation in ViziCheck.

It adheres strictly to **Clean Architecture** principles, separating responsibilities across modular layers:
- **API Controllers (`app/api/routes/users.py`, `profile.py`)**: Thin controllers handling HTTP requests and routing.
- **Service Layer (`app/services/user_service.py`, `profile_service.py`)**: Orchestrates business logic, validations, repository access, mapping, and audit logging.
- **Validation Layer (`app/validators/user_validator.py`)**: Encapsulates email normalization, password strength policy, role assignment rules, tenant boundary checks, and self-delete checks.
- **Mapper Layer (`app/mappers/user_mapper.py`)**: Handles conversion between SQLAlchemy ORM models and response DTOs.
- **Specification Layer (`app/repositories/specifications/user_filters.py`)**: Dynamically builds query filters and sorting.
- **Repository Layer (`app/repositories/user_repository.py`, `audit_repository.py`)**: Database access layer.
- **Constants Layer (`app/constants/`)**: Centralized definitions for audit actions, roles, and permissions.

---

## 2. Architecture & Request Lifecycle

```
Client Request
      │
      ▼
FastAPI Router (users.py / profile.py)
      │
      ▼
Dependencies (get_current_tenant_admin / get_current_active_user) ── [JWT & RBAC Check]
      │
      ▼
Service Layer (UserService / ProfileService)
      ├──> UserValidator (Email, Password, Role, Tenant, Self-Delete)
      ├──> UserRepository / UserFilters (Database CRUD & Specifications)
      ├──> AuditRepository (Record Administrative Action)
      └──> UserMapper (ORM -> Response DTO)
      │
      ▼
Response Envelope JSON Payload
```

---

## 3. Core Component Specifications

### 3.1 Validation Layer (`UserValidator`)
- **Password Policy**: Minimum 8 characters, requiring at least one uppercase letter, one lowercase letter, one numeric digit, and one special character (`!@#$%^&*()_+-=[]{}|;:,.<>/?`).
- **Email Normalization**: Strips leading/trailing whitespace and converts emails to lowercase before checking uniqueness or persisting (`jane.doe@example.com`).
- **Role Assignment Controls**: Non-Super Admin callers are strictly prevented from assigning or elevating users to the `SUPER_ADMIN` role.
- **Tenant Isolation**: Tenant Admins are restricted to managing users strictly within their assigned `tenant_id`.
- **Self-Deletion Guard**: Prevents users from soft-deleting their own account via administrative user endpoints.

### 3.2 Specification & Search Layer (`UserFilters`)
The specification layer dynamically builds query clauses for searching across `first_name`, `last_name`, and `email` using case-insensitive wildcard matching (`ilike`), filtering by `role_id`, `tenant_id`, `is_active`, and `is_deleted` flags, and applying dynamic sorting (`created_at`, `email`, `first_name`, `last_name`) and page offsets.

### 3.3 Enhanced Pagination DTO (`EnhancedPaginationResponse`)
```json
{
  "page": 1,
  "page_size": 10,
  "total_records": 45,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false,
  "items": [ ... ]
}
```

---

## 4. API Endpoints Reference

| Method | Endpoint | Description | Authorization |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/users` | Create user | Super Admin, Tenant Admin |
| `GET` | `/api/v1/users` | List / Search / Paginate users | Super Admin, Tenant Admin |
| `GET` | `/api/v1/users/{id}` | Get user details | Super Admin, Tenant Admin |
| `PUT` | `/api/v1/users/{id}` | Update user details | Super Admin, Tenant Admin |
| `DELETE` | `/api/v1/users/{id}` | Soft delete user | Super Admin, Tenant Admin |
| `PATCH` | `/api/v1/users/{id}/activate` | Activate user account | Super Admin, Tenant Admin |
| `PATCH` | `/api/v1/users/{id}/deactivate` | Deactivate user account | Super Admin, Tenant Admin |
| `PATCH` | `/api/v1/users/{id}/restore` | Restore soft-deleted user | Super Admin, Tenant Admin |
| `PATCH` | `/api/v1/users/change-password` | Change own password | Any Active User |
| `PATCH` | `/api/v1/users/{id}/reset-password` | Admin reset user password | Super Admin, Tenant Admin |
| `GET` | `/api/v1/profile` | Get logged-in user profile | Any Active User |
| `PUT` | `/api/v1/profile` | Update logged-in user profile | Any Active User |

---

## 5. Audit Logging Specifications

All user management administrative actions persist audit events to `audit_logs`:
- `USER_CREATED`: Logged upon successful user account creation.
- `USER_UPDATED`: Logged with `old_value` and `new_value` snapshots on updates.
- `USER_DELETED`: Logged upon soft-deletion.
- `USER_RESTORED`: Logged upon restoration of a soft-deleted user.
- `USER_ACTIVATED`: Logged when user status is changed to active.
- `USER_DEACTIVATED`: Logged when user status is disabled.
- `PASSWORD_CHANGED`: Logged when user changes their password.
- `PASSWORD_RESET`: Logged when admin resets user password.
- `PROFILE_UPDATED`: Logged when user updates self profile.

---

## 6. Security Considerations & Best Practices

1. **Password Hashing**: Passwords are never stored in plaintext and are hashed using bcrypt via `hash_password()`.
2. **DTO Exposure Protection**: Password hashes and internal security credentials are never exposed in any schema or response DTO.
3. **Tenant Boundary Protection**: Database queries strictly filter by `tenant_id` for tenant-scoped users, preventing cross-tenant data leaks.
4. **Role Escalation Protection**: Non-Super Admin users cannot assign or elevate accounts to `SUPER_ADMIN`.
5. **Soft Delete Preservation**: Soft delete preserves audit trails and foreign key integrity.

---

## 7. Interview Explanation Guide

**Q: How is user management structured in ViziCheck?**
> "We follow Clean Architecture by separating concerns into dedicated Validation, Specification, Mapper, Repository, and Service layers. Controllers in `users.py` and `profile.py` remain thin. `UserService` handles administrative user operations while `ProfileService` handles self-service profile management. Validation rules (email normalization, password strength, tenant boundaries, role escalation guards) live in `UserValidator`. Data formatting is decoupled using `UserMapper`, and search/pagination queries use `UserFilters` specifications. All administrative actions emit audit log events to ensure full compliance."
