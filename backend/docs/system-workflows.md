# architecture/system-workflows.md

# ViziCheck System Workflows

## Visitor Registration Workflow

```mermaid
flowchart TD

Visitor Registers
     ↓
Create Account
     ↓
Email Verification
     ↓
Profile Created
```

---

## Visit Request Workflow

```mermaid
flowchart TD

Visitor
      ↓
Select Tenant
      ↓
Select Availability Slot
      ↓
Submit Request
      ↓
Pending Approval
```

---

## Approval Workflow

```mermaid
flowchart TD

Pending Request
      ↓
Tenant Admin Reviews
      ↓
Approve OR Reject

Approve --> Pass Generation

Reject --> Notification
```

---

## Pass Generation Workflow

```mermaid
flowchart TD

Approved Request
    ↓
Generate Pass
    ↓
Generate QR
    ↓
Send Notification
```

---

## Security Check-In Workflow

```mermaid
flowchart TD

Visitor Arrives
      ↓
Security Scans QR
      ↓
Validate QR
      ↓
Check-In Visitor
      ↓
Update Audit Log
```

---

## Check-Out Workflow

```mermaid
flowchart TD

Visitor Exit
     ↓
Security Check-Out
     ↓
Visit Completed
     ↓
Audit Log Created
```
