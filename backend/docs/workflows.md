# backend/workflows.md

# Core System Workflows

## Visitor Request Workflow

Draft
↓
Submitted
↓
Pending Approval
↓
Approved / Rejected

If Approved:

Approved
↓
Pass Generated
↓
QR Generated
↓
Check-In
↓
Check-Out
↓
Completed

---

## Approval Workflow

Pending
↓
Tenant Review
↓
Approve OR Reject

Approve
↓
Pass Generation

Reject
↓
Notification

---

## Security Workflow

QR Scan
↓
Validate Token

Valid
↓
Check-In

Invalid
↓
Access Denied

---

## Notification Workflow

Business Event
↓
Notification Service
↓
Database Notification
↓
User Receives Notification

---

## Audit Workflow

User Action
↓
Audit Service
↓
Audit Table
↓
Reporting Dashboard
