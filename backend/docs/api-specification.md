# backend/api-specification.md

# ViziCheck API Specification

## API Standards

Base URL

/api/v1

Response Format

Success Response:

{
"success": true,
"message": "Operation successful",
"data": {}
}

Error Response:

{
"success": false,
"message": "Validation failed",
"errors": []
}

---

# MODULE 1: AUTHENTICATION

## Login

POST /auth/login

Access:
Public

Request:

{
"email": "[admin@vizicheck.com](mailto:admin@vizicheck.com)",
"password": "Password@123"
}

Response:

{
"access_token": "...",
"refresh_token": "...",
"role": "SUPER_ADMIN"
}

---

## Refresh Token

POST /auth/refresh-token

Access:
Authenticated

Request:

{
"refresh_token": "token"
}

Response:

{
"access_token": "new_token"
}

---

## Logout

POST /auth/logout

Access:
Authenticated

Response:

{
"success": true
}

---

# MODULE 2: USER MANAGEMENT

## Get Users

GET /users

Access:
SUPER_ADMIN

Response:

[
{
"id": 1,
"name": "John"
}
]

---

## Get User By ID

GET /users/{id}

Access:
SUPER_ADMIN

---

## Create User

POST /users

Access:
SUPER_ADMIN

Request:

{
"role_id": 2,
"first_name": "John",
"last_name": "Doe",
"email": "[john@company.com](mailto:john@company.com)",
"phone": "9876543210"
}

---

## Update User

PUT /users/{id}

Access:
SUPER_ADMIN

---

## Delete User

DELETE /users/{id}

Access:
SUPER_ADMIN

Soft Delete

---

# MODULE 3: TENANT MANAGEMENT

## Get Tenants

GET /tenants

Access:
SUPER_ADMIN

---

## Get Tenant

GET /tenants/{id}

Access:
SUPER_ADMIN

---

## Create Tenant

POST /tenants

Access:
SUPER_ADMIN

Request:

{
"name": "ABC Technologies",
"contact_person": "Manager",
"contact_email": "[admin@abc.com](mailto:admin@abc.com)"
}

---

## Update Tenant

PUT /tenants/{id}

Access:
SUPER_ADMIN

---

## Deactivate Tenant

DELETE /tenants/{id}

Access:
SUPER_ADMIN

---

# MODULE 4: VISITOR MANAGEMENT

## Register Visitor

POST /visitors/register

Access:
Public

Request:

{
"first_name": "Rahul",
"last_name": "Kumar",
"email": "[rahul@gmail.com](mailto:rahul@gmail.com)",
"phone": "9999999999"
}

---

## Get Visitor Profile

GET /visitors/profile

Access:
VISITOR

---

## Update Visitor Profile

PUT /visitors/profile

Access:
VISITOR

---

# MODULE 5: AVAILABILITY MANAGEMENT

## Get Availability

GET /availability

Access:
TENANT_ADMIN

---

## Create Availability

POST /availability

Access:
TENANT_ADMIN

Request:

{
"date": "2026-07-10",
"start_time": "10:00",
"end_time": "12:00"
}

---

## Update Availability

PUT /availability/{id}

Access:
TENANT_ADMIN

---

## Delete Availability

DELETE /availability/{id}

Access:
TENANT_ADMIN

---

# MODULE 6: VISIT REQUEST MANAGEMENT

## Create Visit Request

POST /requests

Access:
VISITOR

Request:

{
"tenant_id": 1,
"availability_slot_id": 5,
"purpose": "Interview",
"visit_date": "2026-07-10"
}

---

## Get Requests

GET /requests

Access:
Authenticated

Filters:

status

date

tenant

visitor

---

## Get Request Details

GET /requests/{id}

Access:
Authenticated

---

## Cancel Request

PUT /requests/{id}/cancel

Access:
VISITOR

---

# MODULE 7: APPROVAL MANAGEMENT

## Approve Request

POST /approvals/{requestId}/approve

Access:
TENANT_ADMIN

Request:

{
"comments": "Approved"
}

---

## Reject Request

POST /approvals/{requestId}/reject

Access:
TENANT_ADMIN

Request:

{
"comments": "Schedule full"
}

---

## Approval History

GET /approvals

Access:
TENANT_ADMIN

---

# MODULE 8: PASS MANAGEMENT

## Generate Pass

POST /passes/generate

Access:
System Trigger

---

## Get Passes

GET /passes

Access:
Authenticated

---

## Get Pass Details

GET /passes/{id}

Access:
Authenticated

---

## Revoke Pass

PUT /passes/{id}/revoke

Access:
SUPER_ADMIN

---

# MODULE 9: QR MANAGEMENT

## Generate QR

POST /qr/generate

Access:
System Trigger

---

## Validate QR

POST /qr/validate

Access:
SECURITY_OFFICER

Request:

{
"token": "QR_TOKEN"
}

Response:

{
"valid": true,
"visitor": {}
}

---

# MODULE 10: SECURITY OPERATIONS

## Scan QR

POST /security/scan

Access:
SECURITY_OFFICER

---

## Check-In Visitor

POST /security/checkin

Access:
SECURITY_OFFICER

Request:

{
"pass_id": 1001
}

---

## Check-Out Visitor

POST /security/checkout

Access:
SECURITY_OFFICER

Request:

{
"pass_id": 1001
}

---

## Active Visitors

GET /security/active-visitors

Access:
SECURITY_OFFICER

---

# MODULE 11: NOTIFICATIONS

## Get Notifications

GET /notifications

Access:
Authenticated

---

## Mark As Read

PUT /notifications/{id}/read

Access:
Authenticated

---

# MODULE 12: AUDIT LOGS

## Get Audit Logs

GET /audit-logs

Access:
SUPER_ADMIN

Filters:

module

date

user

action

---

## Get Audit Log Details

GET /audit-logs/{id}

Access:
SUPER_ADMIN

---

# MODULE 13: REPORTING

## Dashboard Metrics

GET /reports/dashboard

Access:
SUPER_ADMIN

Response:

{
"visitors_today": 100,
"pending_requests": 25,
"approved_requests": 50,
"active_visitors": 15
}

---

## Visitor Report

GET /reports/visitors

Access:
SUPER_ADMIN

---

## Approval Report

GET /reports/approvals

Access:
SUPER_ADMIN

---

## Security Report

GET /reports/security

Access:
SUPER_ADMIN

---

## Export Report

GET /reports/export

Access:
SUPER_ADMIN

Formats:

PDF

Excel

---

# HTTP Status Codes

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error

---

# Pagination Standard

?page=1

&limit=20

Response:

{
"page": 1,
"limit": 20,
"total": 100,
"items": []
}

---

# Sorting Standard

?sort_by=created_at

&order=desc

---

# Search Standard

?search=rahul

---

# API Versioning

Current Version:

v1

Base URL:

/api/v1

Future:

/api/v2

---

# Estimated API Count

Authentication:
5 APIs

Users:
5 APIs

Tenants:
5 APIs

Visitors:
4 APIs

Availability:
4 APIs

Requests:
5 APIs

Approvals:
3 APIs

Passes:
4 APIs

QR:
3 APIs

Security:
4 APIs

Notifications:
2 APIs

Audit:
2 APIs

Reports:
5 APIs

Total:
51+ REST APIs
