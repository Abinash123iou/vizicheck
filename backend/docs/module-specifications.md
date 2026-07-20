# backend/module-specifications.md

# ViziCheck Backend Module Specifications

## Purpose

This document defines all backend modules, responsibilities, business rules, entities, dependencies, and implementation requirements.

The backend is divided into 13 modules.

Each module follows:

API Layer
   ↓
Service Layer
   ↓
Repository Layer
   ↓
Database Layer

---

# Module 1: Authentication

## Purpose

Provide secure user authentication and session management.

## Responsibilities

* Login
* Logout
* Password Reset
* Token Generation
* Token Validation

## APIs

POST /auth/login

POST /auth/logout

POST /auth/forgot-password

POST /auth/reset-password

POST /auth/refresh-token

## Dependencies

User Management

RBAC

## Business Rules

* Email must be unique.
* Password must be hashed.
* JWT required for protected endpoints.
* Invalid credentials return 401.

---

# Module 2: User Management

## Purpose

Manage all platform users.

## User Types

* Super Admin
* Tenant User
* Security Officer

## Responsibilities

* Create User
* Update User
* Disable User
* Assign Role
* View User Profile

## APIs

GET /users

GET /users/{id}

POST /users

PUT /users/{id}

DELETE /users/{id}

## Dependencies

Authentication

RBAC

## Business Rules

* Only Admin can create users.
* Email must be unique.
* User deletion is soft delete.

---

# Module 3: Tenant Management

## Purpose

Manage organizations operating inside the facility.

## Responsibilities

* Create Tenant
* Update Tenant
* Activate Tenant
* Deactivate Tenant
* View Tenant Details

## APIs

GET /tenants

GET /tenants/{id}

POST /tenants

PUT /tenants/{id}

DELETE /tenants/{id}

## Dependencies

User Management

## Business Rules

* Tenant name must be unique.
* Deactivated tenants cannot approve visitors.

---

# Module 4: Visitor Management

## Purpose

Manage visitor profiles.

## Responsibilities

* Register Visitor
* Update Visitor Profile
* View Visitor Information

## APIs

POST /visitors/register

GET /visitors/{id}

PUT /visitors/{id}

GET /visitors/profile

## Dependencies

Authentication

## Business Rules

* Visitor phone number required.
* Visitor email required.
* Duplicate visitor accounts not allowed.

---

# Module 5: Availability Management

## Purpose

Manage tenant availability schedules.

## Responsibilities

* Create Availability
* Update Availability
* Delete Availability
* View Availability

## APIs

GET /availability

POST /availability

PUT /availability/{id}

DELETE /availability/{id}

## Business Rules

* Availability cannot overlap.
* Past dates cannot be edited.

---

# Module 6: Visit Request Management

## Purpose

Manage visitor requests.

## Responsibilities

* Create Request
* Cancel Request
* View Requests
* Track Status

## APIs

POST /requests

GET /requests

GET /requests/{id}

PUT /requests/{id}

DELETE /requests/{id}

## Request Status

Pending

Approved

Rejected

Cancelled

Completed

Expired

## Business Rules

* Request requires tenant selection.
* Visit date must be future date.
* Request cannot be modified after approval.

---

# Module 7: Approval Management

## Purpose

Handle request approval workflow.

## Responsibilities

* Approve Request
* Reject Request
* Approval History

## APIs

GET /approvals

POST /approvals/{requestId}/approve

POST /approvals/{requestId}/reject

## Dependencies

Visit Request Module

## Business Rules

* Only tenant users can approve.
* Rejected requests cannot generate passes.

---

# Module 8: Pass Management

## Purpose

Manage visitor passes.

## Responsibilities

* Generate Pass
* View Pass
* Download Pass
* Revoke Pass

## APIs

GET /passes

GET /passes/{id}

POST /passes/generate

PUT /passes/{id}/revoke

## Pass Status

Active

Expired

Revoked

Used

## Dependencies

Approval Module

QR Module

## Business Rules

* Pass generated only after approval.
* One active pass per request.

---

# Module 9: QR Management

## Purpose

Generate and validate QR codes.

## Responsibilities

* Generate QR
* Validate QR
* Revoke QR

## APIs

POST /qr/generate

POST /qr/validate

PUT /qr/revoke

## Business Rules

* QR linked to active pass.
* Expired pass invalidates QR.
* Revoked QR cannot be reused.

---

# Module 10: Security Operations

## Purpose

Manage visitor entry and exit.

## Responsibilities

* QR Verification
* Check-In
* Check-Out
* Active Visitor Tracking

## APIs

POST /security/checkin

POST /security/checkout

GET /security/active-visitors

POST /security/scan

## Dependencies

Pass Module

QR Module

## Business Rules

* Visitor must have active pass.
* Visitor cannot check-in twice.
* Check-out requires successful check-in.

---

# Module 11: Notification Management

## Purpose

Manage system notifications.

## Notification Types

* Request Submitted
* Request Approved
* Request Rejected
* Pass Generated
* Check-In Confirmation
* Check-Out Confirmation

## APIs

GET /notifications

PUT /notifications/read

## Business Rules

* Notifications generated automatically.
* Notifications linked to users.

---

# Module 12: Audit Logging

## Purpose

Track all critical system activities.

## Events

Login

Logout

Create Request

Approve Request

Reject Request

Generate Pass

Check-In

Check-Out

User Updates

## APIs

GET /audit-logs

GET /audit-logs/{id}

## Business Rules

* Audit records immutable.
* Audit logs cannot be edited.

---

# Module 13: Reporting & Analytics

## Purpose

Provide operational insights.

## Reports

Visitor Report

Approval Report

Tenant Report

Security Report

Daily Summary

Monthly Summary

## APIs

GET /reports/dashboard

GET /reports/visitors

GET /reports/approvals

GET /reports/security

GET /reports/export

## Business Rules

* Reports filtered by date.
* Export supports PDF and Excel.

---

# Module Dependencies

Authentication
     ↓
User Management
     ↓
Tenant Management
     ↓
Visitor Management
     ↓
Visit Request Management
     ↓
Approval Management
     ↓
Pass Management
     ↓
QR Management
     ↓
Security Operations
     ↓
Audit Logging
     ↓
Reporting

Notifications operate across all modules.

---

# Development Priority

Sprint 1

* Authentication
* User Management
* Tenant Management

Sprint 2

* Visitor Management
* Availability Management
* Request Management

Sprint 3

* Approval Management
* Pass Management

Sprint 4

* QR Management
* Security Operations

Sprint 5

* Notifications
* Audit Logging

Sprint 6

* Reporting & Analytics
