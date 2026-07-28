# Sprint 1 – Day 8: Visit Request Management System Documentation

## Module Overview

The **Visit Request Management System** is the core access control workflow engine of ViziCheck. A visitor profile alone does not grant physical or digital entrance to an organization—the Visit Request module manages the complete invitation and approval lifecycle, enforcing tenant isolation, Role-Based Access Control (RBAC), validation, audit logging, pass generation hooks, notification hooks, and dashboard statistics.

---

## Downstream Architecture & Module Integration Flow

The visitor access pipeline connects across system boundaries as follows:

```
┌─────────────────┐
│ Visitor Module  │ (Visitor Profile Registered & Verified)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Visit Request   │ (Host submits invitation with purpose, date & time window)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Request Review  │ (Tenant Admin / Host Review)
└────┬───────┬────┘
     │       │
     ▼       ▼
[Approved] [Rejected] ──► (Notify Visitor of Rejection & Reason)
     │
     ▼
┌──────────────────┐
│ Visitor Pass     │ (Automatic Visitor Pass record generation)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ QR Generator     │ (Unique, cryptographically signed QR Code token payload)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Send Notification│ (Email/SMS with QR Pass dispatched to visitor & security)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check-In Module  │ (Gate Security scans QR Pass -> Status: CHECKED_IN)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check-Out Module │ (Exit scan -> Status: CHECKED_OUT -> COMPLETED)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Audit & Reports  │ (Compliance exports & dashboard metrics)
└──────────────────┘
```

---

## State Machine & Status Transitions

Visit Requests transition through an explicit set of states:

| Status | Description | Allowed Next States |
| :--- | :--- | :--- |
| `PENDING` | Newly created request awaiting review | `APPROVED`, `REJECTED`, `CANCELLED` |
| `APPROVED` | Approved by host/admin; QR Pass generated | `CHECKED_IN`, `CANCELLED`, `EXPIRED` |
| `REJECTED` | Declined by host/admin with rejection reason | Terminated |
| `CANCELLED` | Revoked prior to arrival with cancellation reason | Terminated |
| `CHECKED_IN` | Visitor arrived on site and scanned in | `CHECKED_OUT` |
| `CHECKED_OUT` | Visitor departed site | `COMPLETED` |
| `COMPLETED` | Visit lifecycle finalized | Terminated |
| `EXPIRED` | Visit window passed without check-in | Terminated |

---

## Core Database Schema

### `visit_requests` Table
- `id` (INTEGER, Primary Key, Autoincrement)
- `tenant_id` (INTEGER, Foreign Key -> `tenants.id`, CASCADE, Index)
- `request_code` (VARCHAR(50), Unique per tenant, Index) e.g., `VR-TEN-000001-000001`
- `visitor_id` (INTEGER, Foreign Key -> `visitors.id`, CASCADE, Index)
- `host_id` (INTEGER, Foreign Key -> `users.id`, RESTRICT, Index)
- `purpose` (VARCHAR(255), Not Null)
- `department` (VARCHAR(100), Nullable, Index)
- `scheduled_start_time` (DATETIME, Not Null, Index)
- `scheduled_end_time` (DATETIME, Not Null, Index)
- `actual_checkin` (DATETIME, Nullable)
- `actual_checkout` (DATETIME, Nullable)
- `additional_visitors_count` (INTEGER, Default 0)
- `notes` (TEXT, Nullable)
- `status` (ENUM `visit_request_status`, Default `PENDING`, Index)
- `approved_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `approved_at` (DATETIME, Nullable)
- `approval_notes` (TEXT, Nullable)
- `rejected_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `rejected_at` (DATETIME, Nullable)
- `rejection_reason` (TEXT, Nullable)
- `cancelled_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `cancelled_at` (DATETIME, Nullable)
- `cancellation_reason` (TEXT, Nullable)
- `created_by` (INTEGER, Foreign Key -> `users.id`, Nullable)
- `created_at` (DATETIME, Default `now()`, Index)
- `updated_at` (DATETIME, Nullable)
- `is_deleted` (BOOLEAN, Default `False`)

---

## API Reference (14 REST APIs)

| Verb | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/visit-requests` | `VISIT_REQUEST_CREATE` | Submit a new Visit Request |
| `GET` | `/api/v1/visit-requests` | `VISIT_REQUEST_READ` | List paginated, searched & filtered requests |
| `GET` | `/api/v1/visit-requests/statistics` | `VISIT_REQUEST_READ` | Get dashboard analytics metrics & peak hours |
| `GET` | `/api/v1/visit-requests/export` | `VISIT_REQUEST_EXPORT` | Download filtered requests in CSV format |
| `GET` | `/api/v1/visit-requests/pending` | `VISIT_REQUEST_READ` | Get pending requests awaiting host/admin review |
| `GET` | `/api/v1/visit-requests/my-requests` | Authenticated User | Get requests created by or hosted by current user |
| `GET` | `/api/v1/visit-requests/calendar` | `VISIT_REQUEST_READ` | Get calendar events feed grouped by date |
| `GET` | `/api/v1/visit-requests/{id}` | `VISIT_REQUEST_READ` | Get single visit request details by ID |
| `PUT` | `/api/v1/visit-requests/{id}` | `VISIT_REQUEST_UPDATE` | Update pending visit request details |
| `DELETE` | `/api/v1/visit-requests/{id}` | `VISIT_REQUEST_DELETE` | Soft delete visit request |
| `PATCH/POST` | `/api/v1/visit-requests/{id}/approve` | `VISIT_REQUEST_APPROVE` | Approve request (triggers pass & notification hooks) |
| `PATCH/POST` | `/api/v1/visit-requests/{id}/reject` | `VISIT_REQUEST_REJECT` | Reject request with mandatory rejection reason |
| `PATCH/POST` | `/api/v1/visit-requests/{id}/cancel` | `VISIT_REQUEST_CANCEL` | Cancel request with mandatory cancellation reason |
| `PATCH` | `/api/v1/visit-requests/{id}/restore` | `VISIT_REQUEST_RESTORE` | Restore soft-deleted visit request |

---

## Validation & Business Rules

1. **Tenant Isolation & Active State**: Requests can only be created within an active tenant organization (`TenantStatus.ACTIVE`). Super Admins can override tenant context.
2. **Visitor Eligibility**: The visitor must exist in the tenant organization, must not be soft-deleted, and **must not be blacklisted**.
3. **Host Eligibility**: The host employee must exist, belong to the tenant organization, be active (`is_active=True`), and not be deleted.
4. **Schedule Sanity**: `scheduled_end_time` must be after `scheduled_start_time`. Start time cannot be in the past (unless an explicit authorized override is set).
5. **Overlapping Booking Prevention**: Prevents scheduling overlapping active/pending visits for the same visitor during identical time windows (`scheduled_start_time < new_end AND scheduled_end_time > new_start`).

---

## Interview Notes & Architectural Key Takeaways

### Q1: How does ViziCheck enforce tenant isolation in the Visit Request module?
> **Answer**: Multi-tenancy is enforced at three distinct layers:
> 1. **Database Schema**: All `visit_requests` table rows contain a mandatory, indexed `tenant_id` foreign key.
> 2. **Repository Specifications**: The `RequestFilters` specification automatically appends `filter(VisitRequest.tenant_id == current_user.tenant_id)` for non-Super Admin users.
> 3. **Validation Layer**: `RequestValidator.validate_tenant_boundary` verifies that hosts, visitors, and request entities belong exclusively to the authenticated user's tenant organization before executing any read or write operation.

### Q2: What happens when a Visit Request is approved?
> **Answer**: Approval initiates a multi-stage event cascade:
> 1. The status transitions from `PENDING` to `APPROVED`, populating `approved_by`, `approved_at`, and `approval_notes`.
> 2. An immutable audit record with action `VISIT_REQUEST_APPROVED` is saved to the audit log.
> 3. `PassService.generate_pass_for_approved_request` triggers QR visitor pass generation.
> 4. `NotificationService.notify_request_approved` dispatches notifications containing pass details to the visitor and host.

### Q3: How are duplicate bookings handled?
> **Answer**: The system performs window overlap detection in `RequestRepository.check_overlapping_request()`. It checks if any existing request for the same visitor in the same tenant has status `PENDING`, `APPROVED`, or `CHECKED_IN` and time boundaries overlapping the requested window `(start_time < new_end AND end_time > new_start)`. If an overlap is found, a `ValidationException` is raised.
