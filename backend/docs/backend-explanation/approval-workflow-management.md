# Sprint 1 – Day 12: Approval Workflow Management System (Module Code: APP)

## Overview

The **Approval Workflow Management System** (`Module Code: APP`) in ViziCheck serves as the core decision engine between **Visit Request Creation** and **Visitor Pass Generation**.

It supports single-level (Host direct) and multi-level (Host -> Department Head -> Security Admin) approval workflows, approval audit history tracking, delegation to substitute approvers, escalation to management, expiration timeouts, and multi-tenant isolation.

---

## Technical Architecture & Workflow Integration

```
               ┌──────────────────────────────────────────────┐
               │         Visitor / Employee Submits           │
               │               Visit Request                  │
               └──────────────────────┬───────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │    Approval Workflow Engine Initialized      │
               │            (Status: PENDING)                 │
               └──────────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
          ┌───────────────────┐               ┌───────────────────┐
          │ Approve (Action)  │               │  Reject (Action)  │
          └─────────┬─────────┘               └─────────┬─────────┘
                    │                                   │
      ┌─────────────┴─────────────┐                     │
      │                           │                     │
      ▼                           ▼                     ▼
[Single / Final Step]     [Multi-Level Next Step]  Visit Request -> REJECTED
Visit Request -> APPROVED  Advance Current Step    Approval -> REJECTED
Visitor Pass Generated    Assign Next Approver
QR Token Generated
```

---

## Implemented API Endpoints (6 Endpoints)

| # | HTTP Method | Route Path | Description | Required Permissions |
|---|-------------|------------|-------------|----------------------|
| 1 | `POST` | `/api/v1/approvals` | Initialize approval workflow for a visit request | `APPROVAL_CREATE` |
| 2 | `GET` | `/api/v1/approvals/pending` | List pending approvals for current user / tenant with filters & pagination | `APPROVAL_READ` |
| 3 | `PATCH` | `/api/v1/approvals/{id}/action` | Action approval step (`APPROVE`, `REJECT`, `DELEGATE`, `ESCALATE`) | `APPROVAL_ACTION` |
| 4 | `GET` | `/api/v1/approvals/{id}/history` | Retrieve approval audit history timeline | `APPROVAL_READ` |
| 5 | `GET` | `/api/v1/approvals/stats` | Retrieve approval dashboard metrics | `APPROVAL_READ` |
| 6 | `GET` | `/api/v1/approvals/{id}` | Retrieve approval workflow details by ID | `APPROVAL_READ` |

---

## Database Schemas

### 1. `approvals` Table
Stores active and historical approval workflows per visit request.

| Column | Type | Constraints / Details |
|--------|------|-----------------------|
| `id` | BigInteger | Primary Key, Auto-increment |
| `tenant_id` | BigInteger | Foreign Key (`tenants.id`), Indexed |
| `request_id` | BigInteger | Foreign Key (`visit_requests.id`), Indexed |
| `approval_code` | String(50) | Unique Approval Code (e.g. `APP-2026-CAP-000001`) |
| `approval_type` | Enum | `SINGLE_LEVEL`, `MULTI_LEVEL` |
| `current_step` | Integer | Active step index (Default: 1) |
| `total_steps` | Integer | Total workflow steps (Default: 1) |
| `current_approver_id` | BigInteger | Foreign Key (`users.id`), Active Approver |
| `status` | Enum | `PENDING`, `APPROVED`, `REJECTED`, `DELEGATED`, `ESCALATED`, `EXPIRED`, `CANCELLED` |
| `expires_at` | DateTime | Optional workflow expiration timestamp |
| `notes` | Text | Additional notes |
| `created_at` | DateTime | Timestamp |
| `updated_at` | DateTime | Timestamp |
| `is_deleted` | Boolean | Soft delete flag |

### 2. `approval_histories` Table
Audit timeline logging every state change, actor, and comment.

| Column | Type | Constraints / Details |
|--------|------|-----------------------|
| `id` | BigInteger | Primary Key, Auto-increment |
| `approval_id` | BigInteger | Foreign Key (`approvals.id`), Indexed |
| `tenant_id` | BigInteger | Foreign Key (`tenants.id`), Indexed |
| `step_number` | Integer | Step index when action occurred |
| `actor_id` | BigInteger | Foreign Key (`users.id`), User who performed action |
| `action` | Enum | `CREATED`, `APPROVE`, `REJECT`, `DELEGATE`, `ESCALATE`, `REMIND`, `EXPIRE`, `CANCEL` |
| `previous_status` | Enum | Status before action |
| `new_status` | Enum | Status after action |
| `comments` | Text | Comments / justification |
| `delegated_to_id` | BigInteger | Foreign Key (`users.id`), Nullable delegate user |
| `created_at` | DateTime | Action timestamp |

---

## Core Features & Business Logic

1. **Automatic Pass Generation on Final Approval**:
   - When the final approval step is approved, the system automatically transitions `VisitRequest` status to `APPROVED` and invokes `PassService.generate_pass` to create the `VisitorPass` and active `QRToken`.
2. **Rejection Handling**:
   - Rejection instantly terminates the workflow, updates `VisitRequest` status to `REJECTED`, and logs audit trails.
3. **Delegation & Escalation**:
   - Approvers can delegate their active approval step to another tenant user (e.g. host traveling on leave).
   - Approvers or system rules can escalate an approval to an admin or manager (`target_user_id`).
4. **Audit Trail**:
   - Generates audit logs for `APPROVAL_CREATED`, `APPROVED`, `REJECTED`, `DELEGATED`, `ESCALATED`, `EXPIRED`, `CANCELLED`.

---

## Verification Results

- **Pytest Suite**: Executed `python -m pytest tests/approval/test_approval.py -v`.
  - 8/8 unit tests passing **100%**.
- **Data Seeder**: Executed `python scripts/seed_testing_data.py`.
  - All mock approvals generated.
