```txt
React Web Application
Flutter Mobile Application
Future Admin/Integration Tools
```

## ViziCheck API Specification v1.0

## 1. API Overview

ViziCheck will expose REST APIs through the FastAPI backend.

The APIs will be consumed by:

## 2. API Base URL

## Local Development

http://localhost:8000/api/v1

## Production

https://api.vizicheck.com/api/v1

Production URL can be changed later based on hosting.

## 3. API Standards

## Request Format

```json
{
    "field_name": "value"
}
```

## Success Response Format

```json
{
    "success": true,
    "message": "Operation successful",
    "data": {}
}
```

## Error Response Format

```json
{
    "success": false,
    "message": "Validation failed",
    "errors": []
}
```

## 4. Authentication Standard

All protected endpoints must include:

Authorization: Bearer <access\_token>

## 5. Common HTTP Status Codes

<table><tr><td>Code</td><td>Meaning</td></tr><tr><td>200</td><td>Success</td></tr><tr><td>201</td><td>Created</td></tr><tr><td>400</td><td>Bad Request</td></tr><tr><td>401</td><td>Unauthorized</td></tr><tr><td>403</td><td>Forbidden</td></tr><tr><td>404</td><td>Not Found</td></tr><tr><td>409</td><td>Conflict</td></tr><tr><td>422</td><td>Validation Error</td></tr><tr><td>500</td><td>Internal Server Error</td></tr></table>

## 6. API Module List

AUTH Authentication APIs

TEN Tenant APIs

VIS Visitor APIs

AVL Availability APIs

REQ Visit Request APIs

APP Approval APIs

PASS Pass APIs

QR QR Verification APIs

SEC Security Operations APIs

AUDIT Audit APIs

NOTIF Notification APIs

REP Report APIs

ADMIN Settings/Admin APIs

```json
7. Authentication APIs
API-AUTH-001 — Login
POST /auth/login
Access
Public
Request Body
{
    "email": "admin@vizicheck.com",
    "password": "Password@123"
}
Success Response
{
    "success": true,
    "message": "Login successful",
    "data": {
    "access_token": "jwt_token",
    "token_type": "bearer",
    "user": {
    "user_id": "uuid",
    "full_name": "Admin User",
    "email": "admin@vizicheck.com",
    "role": "SUPER_ADMIN"
    }
    }
}
```

```snap
API-AUTH-002 — Logout
POST /auth/logout
Access
Authenticated Users
Success Response
{
  "success": true,
  "message": "Logout successful",
  "data": null
}
```

```txt
API-AUTH-003 — Get Current User
GET /auth/me
Access
Authenticated Users
Success Response
{
  "success": true,
  "message": "Current user fetched successfully",
  "data": {
    "user_id": "uuid",
    "full_name": "Admin User",
    "email": "admin@vizicheck.com",
    "role": "SUPER_ADMIN",
    "account_status": "active"
    }
}
API-AUTH-004 — Forgot Password
POST /auth/forgot-password
Access
Public
Request Body
{
  "email": "user@example.com"
}
API-AUTH-005 — Reset Password
POST /auth/reset-password
Access
Public
Request Body
{
  "token": "reset_token",
  "new_password": "NewPassword@123"
}
```

```txt
8. Tenant APIs
API-TEN-001 — Create Tenant
POST /tenants
Access
Super Admin
Request Body
{
    "full_name": "Ramesh Kumar",
    "email": "ramesh@company.com",
    "phone": "9876543210",
    "department": "IT",
    "designation": "Manager",
    "office_location": "Block A - Floor 2"
}
Success Response
{
    "success": true,
    "message": "Tenant created successfully",
    "data": {
    "tenant_id": "uuid",
    "user_id": "uuid",
    "full_name": "Ramesh Kumar",
    "email": "ramesh@company.com",
    "department": "IT"
    }
}
API-TEN-002 — Get All Tenants
GET /tenants
Access
Super Admin, Security Officer
Query Params
page
limit
search
status
```

## API-TEN-003 — Get Tenant by ID

GET /tenants/{tenant\_id}

Access

Super Admin, Tenant, Security Officer

## API-TEN-004 — Update Tenant

PUT /tenants/{tenant\_id}

Access

Super Admin, Tenant Own Profile

## API-TEN-005 — Delete Tenant

DELETE /tenants/{tenant\_id}

Access

Super Admin

Note

This should perform soft delete, not hard delete.

## 9. Visitor APIs

## API-VIS-001 — Register Visitor

POST /visitors/register

Access

Public / Visitor

Request Body

```json
{
    "full_name": "Suresh Babu",
    "email": "suresh@example.com",
    "phone": "9876543210",
    "password": "Password@123",
    "organization_name": "ABC Suppliers",
    "visitor_type": "vendor"
}
```

## API-VIS-002 — Get All Visitors

GET /visitors

## Access

Super Admin, Security Officer

Query Params

page
limit
search
visitor\_type

## API-VIS-003 — Get Visitor by ID

GET /visitors/{visitor\_id}

## Access

Super Admin, Visitor Own Profile, Security Officer

## API-VIS-004 — Update Visitor

PUT /visitors/{visitor\_id}

## Access

Super Admin, Visitor Own Profile

## API-VIS-005 — Get Visitor History

GET /visitors/{visitor\_id}/history

## Access

Super Admin, Visitor Own Profile

## 10. Availability APIs

API-AVL-001 — Create Availability

POST /tenants/{tenant\_id}/availability

Access

Tenant Own Profile, Super Admin

```ignorefile
date
from_date
to_date
status
```

```txt
Super Admin, Tenant Own Profile, Visitor
```

```txt
Request Body
{
    "available_date": "2026-06-20",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "status": "available",
    "notes": "Available for visitor meetings"
}
```

## API-AVL-002 — Get Tenant Availability

GET /tenants/{tenant\_id}/availability

## Access

## Query Params

## API-AVL-003 — Update Availability

PUT /availability/{availability\_id}

## Access

Tenant Own Profile, Super Admin

## API-AVL-004 — Delete Availability

DELETE /availability/{availability\_id}

## Access

Tenant Own Profile, Super Admin

```txt
API-REQ-001 — Create Visit Request
POST /requests
Access
Visitor
Request Body
{
"tenant_id": "uuid",
"visit_date": "2026-07-15",
"start_time": "10:00:00",
"end_time": "11:00:00",
"purpose": "Project Discussion"
}
Validation
Tenant must exist
Visit date must be valid
Tenant availability must be checked
End time > Start time
```

## 11. Visit Request APIs

These APIs manage the complete visitor request lifecycle.

## API-REQ-002 — Get All Requests

## API-REQ-003 — Get Request By ID

GET /requests/{request\_id}

\## API-REQ-004 — Update Request

\`\`http
PUT /requests/{request\_id}

## API-REQ-005 — Cancel Request

POST /requests/{request\_id}/cancel
Access
Visitor
Status Change
Pending
↓
Cancelled

## API-REQ-006 — Request Timeline

GET /requests/{request\_id}/timeline

Access

Tenant

Super Admin

Visitor

\### Returns

\`\`text

Created

Tenant Approved

Admin Approved

Pass Generated

Checked-In

Checked-Out

## 12. Approval APIs

These APIs support the approval workflow defined in the SRS.

## API-APP-001 — Get Pending Approvals

GET /approvals/pending

Access

Tenant
Super Admin

\## API-APP-002 — Approve Request

'''http
POST /approvals/{request\_id}/approve

Access

Tenant
Super Admin

\### Validation

\`\`text
Tenant availability must be valid.

If tenant absent
approval must fail.
(Primary business rule from internship specification.)

```txt
Request Body
{
    "notes": "Approved for meeting"
}

API-APP-003 — Reject Request
POST /approvals/{request_id}/reject
Request Body
{
    "reason": "Tenant unavailable"
}

API-APP-004 — Approval History
GET /approvals/history
Access
Super Admin
Query Params
date_range
approver
status
```

## 13. Pass APIs

These APIs manage visitor pass generation and lifecycle.

```txt
API-PASS-001 — Generate Pass
POST /passes/generate
Access
Super Admin
Request Body
{
    "request_id": "uuid"
}
```

```txt
Validation
Tenant Approval Completed
Admin Approval Completed
Tenant Available
Output
{
"pass_id": "uuid",
"pass_number": "VP-2026-0001",
"status": "active"
}
```

## API-PASS-002 — Get Pass By ID

```txt
Request Body
{
"reason": "Security concern"
}
```

```txt
API-PASS-005 — Pass History
GET /passes/history
Access
Super Admin
Filters
status
date_range
tenant
visitor
```

## 14. QR Verification APIs

```hcl
API-QR-001 — Generate QR Token
POST /qr/generate
Access
System / Super Admin
Request Body
{
    "pass_id": "uuid"
}
Response
{
    "success": true,
    "message": "QR token generated successfully",
    "data": {
    "qr_token_id": "uuid",
    "pass_id": "uuid",
    "token_value": "secure-token",
    "expires_at": "2026-07-15T11:00:00"
    }
}
```

```txt
API-QR-002 — Get QR by Pass ID
GET /qr/pass/{pass_id}
Access
Super Admin, Visitor Own Pass, Security Officer

API-QR-003 — Validate QR
POST /qr/validate
Access
Security Officer
Request Body
{
    "token_value": "secure-token"
}
Validation
Token must exist
Token must not be expired
Pass must be active
Pass must not be revoked
Response
{
    "success": true,
    "message": "QR validation successful",
    "data": {
    "pass_id": "uuid",
    "visitor_name": "Suresh Babu",
    "tenant_name": "Ramesh Kumar",
    "visit_date": "2026-07-15",
    "valid": true
    }
}
```

```txt
15. Security Operations APIs
API-SEC-001 — Check-In Visitor
POST /security/checkin
Access
Security Officer
Request Body
{
"pass_id": "uuid",
"remarks": "Verified at main gate"
}
Validation
Pass must be active
Visitor must not already be checked in
API-SEC-002 — Check-Out Visitor
POST /security/checkout
Access
Security Officer
Request Body
{
"pass_id": "uuid",
"remarks": "Visitor exited"
}
Validation
Visitor must already be checked in
API-SEC-003 — Get Active Visitors
GET /security/active-visitors
Access
Security Officer, Super Admin
```

## API-SEC-004 — Get Security Logs

GET /security/logs

Access

Security Officer, Super Admin

## 16. Audit APIs

## API-AUDIT-001 — Get Audit Logs

GET /audit-logs

Access

Super Admin

Query Params

page limit

module\_name

action\_type

user\_id

from\_date

to\_date

## API-AUDIT-002 — Get Audit Log by ID

GET /audit-logs/{audit\_log\_id}

Access

Super Admin

## 17. Notification APIs

API-NOTIF-001 — Get My Notifications

GET /notifications

Access

Authenticated Users

## API-NOTIF-002 — Mark Notification as Read

PATCH /notifications/{notification\_id}/read

## Access

Notification Owner

## API-NOTIF-003 — Mark All Notifications as Read

PATCH /notifications/read-all

Access

Authenticated Users

## 18. Report APIs

## API-REP-001 — Dashboard Summary

GET /reports/dashboard

## Access

Super Admin, Tenant, Security Officer

## Response Includes

Total Visitors
Today's Visits

Pending Approvals

Active Visitors

Checked-In Count

Checked-Out Count

## API-REP-002 — Visitor Statistics

GET /reports/visitor-statistics

## Access

Super Admin

Query Params

from\_date

to\_date

group\_by

## API-REP-003 — Approval Statistics

GET /reports/approval-statistics
Access
Super Admin

## API-REP-004 — Export Report

GET /reports/export
Access
Super Admin

Query Params

report\_type
format
from\_date
to\_date

## 19. Admin APIs

API-ADMIN-001 — Get All Users

GET /admin/users
Access
Super Admin

## API-ADMIN-002 — Update User Role

PUT /admin/users/{user\_id}/role

Access

Super Admin

Request Body

{
    "role": "TENANT"
}

## API-ADMIN-003 — Update User Status

Access

Super Admin

Request Body

## API-ADMIN-004 — Get System Settings

GET /admin/settings

Access

Super Admin

## API-ADMIN-005 — Update System Settings

PUT /admin/settings

Access

Super Admin

## Final API Count

AUTH 5  
TEN 5  
VIS 5  
AVL 4  
REQ 6  
APP 4  
PASS 5  
QR 3  
SEC 4  
AUDIT 2  
NOTIF 3  
REP 4  
ADMIN 5
