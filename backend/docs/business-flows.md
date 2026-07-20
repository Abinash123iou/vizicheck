# backend/business-flows.md

# ViziCheck Business Flows

## Purpose

Defines real-world business scenarios and expected system behavior.

---

# Flow 1: Interview Visitor

Visitor registers account
         ↓
Visitor selects company tenant
         ↓
Visitor selects available slot
         ↓
Visitor submits request
         ↓
Tenant Admin reviews request
         ↓
Request approved
         ↓
Pass generated
         ↓
QR generated
         ↓
Security scans QR
         ↓
Visitor check-in
         ↓
Visitor attends interview
         ↓
Visitor check-out
         ↓
Audit log created

---

# Flow 2: Client Meeting Visitor

Client receives invitation
         ↓
Registers visitor account
         ↓
Creates meeting request
         ↓
Tenant approves
         ↓
QR pass generated
         ↓
Security validates QR
         ↓
Check-in completed
         ↓
Meeting completed
         ↓
Check-out completed

---

# Flow 3: Vendor Visit

Vendor submits maintenance/service visit
        ↓
Tenant reviews purpose
        ↓
Approval granted
        ↓
Pass generated
        ↓
Security verifies QR
        ↓
Entry allowed
        ↓
Work completed
        ↓
Exit recorded

---

# Flow 4: Delivery Personnel

Delivery person registers
        ↓
Delivery request created
        ↓
Tenant approves
        ↓
Temporary pass generated
        ↓
Security verifies
        ↓
Delivery completed
        ↓
Exit recorded

---

# Flow 5: Rejected Visitor

Visitor submits request
        ↓
Tenant rejects request
        ↓
Notification sent
        ↓
No pass generated
        ↓
Request closed

---

# Flow 6: Expired Pass

Visitor misses visit slot
      ↓
Pass validity expires
      ↓
QR becomes invalid
      ↓
Security scan fails
      ↓
Entry denied

---

# Flow 7: Invalid QR

Security scans QR
     ↓
System validates token
     ↓
QR invalid/revoked
     ↓
Access denied
     ↓
Audit log created

---

# Flow 8: Emergency Security Block

Suspicious visitor identified
      ↓
Admin revokes pass
      ↓
QR revoked
      ↓
Security notified
      ↓
Visitor access blocked
