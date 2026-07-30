# Sprint 1 – Day 9: Visitor Pass & QR Generation Module Documentation

## Module Overview

The **Visitor Pass & QR Generation Module** is the secure credentials engine of ViziCheck. Every approved visit request automatically triggers the creation of a digital/physical Visitor Pass containing a cryptographically signed JWT QR code. The module manages the complete pass lifecycle (`PENDING`, `ACTIVE`, `USED`, `COMPLETED`, `EXPIRED`, `REVOKED`), tracks historical state transitions in `pass_status_history`, enforces QR token versioning to reject old QR screenshots, executes automated background pass expiration, enforces multi-tenant boundaries and Role-Based Access Control (RBAC), and prepares the system for Gate Check-In.

---

## Downstream Architecture & Module Integration Flow

The visitor credentials pipeline connects across system boundaries as follows:

```
┌───────────────────┐
│ Visit Request     │ (Visit Request Status = APPROVED)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Pass Generation   │ (Generate unique pass code: VP-YYYY-TENXXXX-XXXXXX)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ QR Token Signer   │ (Cryptographically sign JWT payload with tenant & pass claims)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Pass Status Log   │ (Record initial transition to ACTIVE in pass_status_history)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Event Notification│ (Dispatch PASS_GENERATED email/SMS with QR code to visitor)
└─────────┬─────────┘
          │
          ├─────────────────────────┐
          ▼                         ▼
┌───────────────────┐     ┌─────────────────────┐
│ Gate Scanner      │     │ Expiration Scheduler│ (Periodic background worker)
│ (Gate Check-In)   │     └──────────┬──────────┘
└─────────┬─────────┘                │
          │                          ▼
          ▼               ┌─────────────────────┐
┌───────────────────┐     │ Status = EXPIRED    │ (valid_until < current_time)
│ Check-In / Out    │     └─────────────────────┘
│ (Status: USED)    │
└───────────────────┘
```

---

## State Machine & Status Transitions

Visitor Passes transition through an explicit set of states:

| Status | Description | Allowed Next States |
| :--- | :--- | :--- |
| `PENDING` | Created pass awaiting activation | `ACTIVE`, `REVOKED`, `EXPIRED` |
| `ACTIVE` | Valid pass ready for gate check-in | `USED`, `REVOKED`, `EXPIRED` |
| `USED` | Visitor actively checked in on site | `COMPLETED`, `REVOKED`, `EXPIRED` |
| `COMPLETED` | Visit finalized after check-out | Terminated |
| `EXPIRED` | Validity window passed without check-in | Terminated |
| `REVOKED` | Pass manually cancelled by admin/host/security | Terminated |

---

## Core Database Schema

### 1. `visitor_passes` Table
- `id` (INTEGER, Primary Key, Autoincrement)
- `uuid` (VARCHAR(36), Unique, Index, Not Null) e.g., `550e8400-e29b-41d4-a716-446655440000`
- `tenant_id` (INTEGER, Foreign Key -> `tenants.id`, RESTRICT, Index)
- `visit_request_id` (INTEGER, Foreign Key -> `visit_requests.id`, RESTRICT, Index)
- `visitor_id` (INTEGER, Foreign Key -> `visitors.id`, RESTRICT, Index)
- `host_id` (INTEGER, Foreign Key -> `users.id`, RESTRICT, Index)
- `pass_code` (VARCHAR(50), Unique, Index, Not Null) e.g., `VP-2026-TEN000138-000001`
- `status` (ENUM `pass_status`, Default `ACTIVE`, Index)
- `latest_qr_version` (INTEGER, Default 1, Not Null)
- `valid_from` (DATETIME, Not Null, Index)
- `valid_until` (DATETIME, Not Null, Index)
- `used_at` (DATETIME, Nullable)
- `completed_at` (DATETIME, Nullable)
- `notes` (TEXT, Nullable)
- `revoked_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `revoked_at` (DATETIME, Nullable)
- `revocation_reason` (VARCHAR(500), Nullable)
- `created_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `created_at` (DATETIME, Default `now()`, Not Null)
- `updated_at` (DATETIME, Default `now()`, On Update `now()`, Nullable)
- `is_deleted` (BOOLEAN, Default `False`, Not Null)
- `deleted_at` (DATETIME, Nullable)
- `deleted_by` (INTEGER, Foreign Key -> `users.id`, Nullable)

### 2. `qr_tokens` Table
- `id` (INTEGER, Primary Key, Autoincrement)
- `tenant_id` (INTEGER, Foreign Key -> `tenants.id`, RESTRICT, Index)
- `pass_id` (INTEGER, Foreign Key -> `visitor_passes.id`, CASCADE, Index)
- `token` (TEXT, Not Null) - Cryptographically signed JWT payload
- `version` (INTEGER, Default 1, Not Null)
- `is_active` (BOOLEAN, Default `True`, Index, Not Null)
- `expires_at` (DATETIME, Not Null, Index)
- `created_at` (DATETIME, Default `now()`, Not Null)
- `updated_at` (DATETIME, Default `now()`, On Update `now()`, Nullable)

### 3. `pass_status_history` Table
- `id` (INTEGER, Primary Key, Autoincrement)
- `pass_id` (INTEGER, Foreign Key -> `visitor_passes.id`, CASCADE, Index)
- `old_status` (ENUM `pass_status`, Nullable)
- `new_status` (ENUM `pass_status`, Not Null)
- `changed_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `changed_at` (DATETIME, Default `now()`, Not Null)
- `remarks` (VARCHAR(500), Nullable)

---

## API Reference (12 REST APIs)

| Verb | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/passes/generate/{visit_request_id}` | `PASS_GENERATE` | Generate Visitor Pass & signed QR token for approved request |
| `GET` | `/api/v1/passes` | `PASS_READ` | List paginated, searched & filtered visitor passes |
| `GET` | `/api/v1/passes/statistics` | `PASS_READ` | Get dashboard metrics, validity averages & regeneration counts |
| `GET` | `/api/v1/passes/export` | `PASS_EXPORT` | Download filtered pass records in CSV format |
| `GET` | `/api/v1/passes/code/{pass_code}` | `PASS_READ` | Find visitor pass details by unique pass code |
| `GET` | `/api/v1/passes/{id}` | `PASS_READ` | Get single visitor pass details by ID |
| `PUT` | `/api/v1/passes/{id}` | `PASS_UPDATE` | Update pass validity window or notes |
| `DELETE` | `/api/v1/passes/{id}` | `PASS_DELETE` | Soft delete visitor pass |
| `GET` | `/api/v1/passes/{id}/qr` | `QR_VIEW` | Retrieve active QR token details & decoded JWT claims |
| `POST` | `/api/v1/passes/{id}/regenerate-qr` | `QR_REGENERATE` | Regenerate QR token, incrementing version and invalidating old QR |
| `PATCH/POST` | `/api/v1/passes/{id}/revoke` | `PASS_REVOKE` | Revoke visitor pass with explicit revocation reason |
| `PATCH` | `/api/v1/passes/{id}/restore` | `PASS_RESTORE` | Restore soft-deleted visitor pass |

---

## Validation & Business Rules

1. **Tenant Isolation & Active State**: Visitor passes can only be generated within an active tenant organization (`TenantStatus.ACTIVE`). Multi-tenant isolation is strictly enforced via database foreign keys, specification filters, and validator checks.
2. **Approved Visit Request Prerequisite**: Passes can only be generated for visit requests with status `APPROVED`. Requesting pass generation for `PENDING`, `REJECTED`, or `CANCELLED` requests raises `ValidationException` (HTTP 400).
3. **Prevent Duplicate Pass Generation**: Prevents duplicate pass generation for the same visit request. If an active, pending, or used pass already exists, `PassValidator.validate_no_duplicate_pass` raises `ConflictException` (HTTP 409 Conflict).
4. **QR Token Versioning & Screenshot Prevention**: Every QR token contains a `version` claim matching `VisitorPass.latest_qr_version`. Upon QR regeneration, `latest_qr_version` is incremented and previous QR tokens are set to `is_active=False`. Scanners reject old QR screenshots where `token.version != pass.latest_qr_version`.
5. **Automated Background Expiration**: The background worker in `pass_expiration_scheduler.py` runs every minute to query active passes where `valid_until < current_time`, automatically updating status to `EXPIRED`, logging `PassStatusHistory`, recording audit trail `PASS_EXPIRED`, and firing `notify_pass_expired`.

---

## Interview Notes & Architectural Key Takeaways

### Q1: How does QR token versioning prevent screenshot reuse?
> **Answer**: QR token security operates through a two-fold versioning mechanism:
> 1. **Token Claims**: Every generated JWT QR token includes a `version` claim (e.g., `version: 2`) alongside `sub` (pass UUID), `tenant_id`, `visitor_id`, `iss`, `aud`, and `exp`.
> 2. **Database State**: The `VisitorPass` entity maintains `latest_qr_version`. When a host or admin clicks *Regenerate QR*, `latest_qr_version` increments (e.g., from 1 to 2) and all previous tokens are deactivated (`is_active=False`).
> 3. **Gate Scanning Validation**: During gate check-in, `QRValidator.validate_token_version_match` checks if `token.version == pass.latest_qr_version`. If a visitor attempts to scan an old QR screenshot with `version: 1`, the scanner rejects the scan immediately.

### Q2: How does the background pass expiration scheduler work?
> **Answer**: The pass expiration scheduler in `background_jobs/pass_expiration_scheduler.py` acts as an automated background worker:
> 1. It queries `VisitorPass` records with status `ACTIVE` and `valid_until < datetime.utcnow()`.
> 2. For each expired pass, it updates `status = EXPIRED`, deactivates linked active QR tokens (`is_active=False`), and inserts a transition entry into `pass_status_history`.
> 3. It writes an audit log entry with action `PASS_EXPIRED` and dispatches an automated notification hook `NotificationService.notify_pass_expired` to inform the visitor and host.

### Q3: What happens when a visitor pass is revoked?
> **Answer**: Pass revocation executes an atomic, multi-step invalidation:
> 1. `PassValidator.validate_pass_not_terminated` ensures the pass is not already `EXPIRED`, `COMPLETED`, or `REVOKED`.
> 2. The pass status updates to `REVOKED`, populating `revoked_by`, `revoked_at`, and `revocation_reason`.
> 3. All active QR tokens linked to the pass are deactivated (`is_active=False`).
> 4. `PassStatusHistory` records the transition (`old_status -> REVOKED`).
> 5. `AuditRepository` logs `PASS_REVOKED` and `NotificationService.notify_pass_revoked` alerts security personnel and the visitor.

### Q4: How is the JWT payload constructed for the QR code?
> **Answer**: Cryptographic QR tokens are created by `QRService.generate_jwt_qr_token()` using `python-jose` signed with the server's `JWT_SECRET` (`HS256`):
> ```json
> {
>   "sub": "550e8400-e29b-41d4-a716-446655440000",
>   "tenant_id": 138,
>   "visitor_id": 195,
>   "visit_request_id": 30,
>   "version": 1,
>   "token_type": "VISITOR_PASS",
>   "iss": "ViziCheck",
>   "aud": "GateScanner",
>   "iat": 1785258771,
>   "exp": 1785273171
> }
> ```
> The signed JWT string is converted into a standard base64 data URI string (`data:image/png;base64,...`) for gate scanner rendering.
