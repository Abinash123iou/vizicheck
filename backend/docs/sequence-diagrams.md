# ViziCheck End-to-End Sequence Diagrams

This document contains full sequence diagrams modeling the core operational flows of the **ViziCheck** Smart Visitor Management System.

---

## 1. End-to-End Visitor Lifecycle Flow

```mermaid
sequenceDiagram
    autonumber
    actor Host as Host Employee
    actor Guard as Security Guard
    actor Visitor as Visitor
    participant Auth as Auth & Security
    participant Avail as Host Availability
    participant Vis as Visitor Mgmt
    participant Req as Visit Request
    participant Appr as Approval Workflow
    participant Pass as Visitor Pass & QR
    participant Gate as Gate Check-In/Out
    participant Notif as Notification Pipeline
    participant Audit as Audit Logging

    %% Step 1: Authentication
    Host->>Auth: POST /api/v1/auth/login
    Auth-->>Host: 200 OK (JWT Access Token)

    %% Step 2: Host Availability
    Host->>Avail: POST /api/v1/availability
    Avail-->>Host: 201 Created (Availability Schedule)

    %% Step 3: Visitor Profile Creation
    Host->>Vis: POST /api/v1/visitors
    Vis->>Audit: Log VISITOR_CREATED
    Vis-->>Host: 201 Created (Visitor ID)

    %% Step 4: Visit Request Creation
    Host->>Req: POST /api/v1/visit-requests
    Req->>Avail: Validate Host Slot Availability
    Req->>Notif: Trigger Request Created Hook
    Req->>Audit: Log VISIT_REQUEST_CREATED
    Req-->>Host: 201 Created (Request ID, Pending Status)

    %% Step 5: Approval & Pass Generation
    Host->>Appr: POST /api/v1/visit-requests/{id}/approve
    Appr->>Pass: Generate Visitor Pass & QR JWT Token
    Appr->>Notif: Dispatch Pass Email / SMS to Visitor
    Appr->>Audit: Log REQUEST_APPROVED & PASS_GENERATED
    Appr-->>Host: 200 OK (Status: APPROVED, Pass Active)

    %% Step 6: Gate Check-In (QR Scan)
    Guard->>Auth: POST /api/v1/auth/login (Security Officer)
    Auth-->>Guard: 200 OK (JWT Access Token)
    Visitor->>Guard: Present QR Code at Gate
    Guard->>Gate: POST /api/v1/checkin/scan (QR Token + Gate Device Meta)
    Gate->>Pass: Run 12-Stage Validation Pipeline
    Gate->>Gate: Update Occupancy Dashboard Metrics
    Gate->>Notif: Send Instant Host Check-In Alert
    Gate->>Audit: Log GATE_CHECKIN
    Gate-->>Guard: 201 Created (CheckIn Record, Status: CHECKED_IN)

    %% Step 7: Gate Check-Out
    Visitor->>Guard: Present QR Code at Exit Gate
    Guard->>Gate: POST /api/v1/checkout/scan (QR Token)
    Gate->>Gate: Calculate Attendance Duration
    Gate->>Pass: Mark Pass Status as COMPLETED
    Gate->>Notif: Send Host Check-Out Alert
    Gate->>Audit: Log GATE_CHECKOUT
    Gate-->>Guard: 200 OK (CheckOut Record, Duration Mins)
```

---

## 2. Gate Verification & 12-Stage Security Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Guard as Gate Guard / Kiosk
    participant API as Check-In API Router
    participant Service as CheckIn Service
    participant Val as CheckIn Validator
    participant DB as System Database

    Guard->>API: POST /api/v1/checkin/scan (qr_token, gate_device_meta)
    API->>Service: scan_checkin(db, current_user, request_data)
    Service->>Val: validate_qr_scan_for_checkin(...)
    
    rect rgb(240, 248, 255)
        note right of Val: 12-Stage Validation Pipeline
        Val->>DB: 1. Validate Security Guard Auth & Role
        Val->>DB: 2. Resolve Gate Device Metadata
        Val->>DB: 3. Verify JWT Cryptographic Signature & Expiry
        Val->>DB: 4. Check QR Token Revocation Status
        Val->>DB: 5. Verify Pass Existence & Active State
        Val->>DB: 6. Verify Tenant Boundary Isolation
        Val->>DB: 7. Check Visitor Active Status & Blacklist
        Val->>DB: 8. Verify Visit Request Approved Status
        Val->>DB: 9. Check Pass Validity Time Window
        Val->>DB: 10. Check Duplicate Check-In (Prevent Re-entry)
        Val->>DB: 11. Verify Host Availability & Active State
        Val->>DB: 12. Check Host Overbooking & Building Capacity Limits
    end

    Val-->>Service: Validation Passed (Pass, Request, Visitor Entities)
    Service->>DB: Persist CheckIn, Update Pass & Request Status
    Service-->>API: CheckInResponse DTO
    API-->>Guard: 201 Created (Check-In Success)
```
