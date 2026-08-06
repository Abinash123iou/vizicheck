# Module Dependency Diagram

The following Mermaid diagram illustrates the architectural dependencies and inter-module communications across all integrated Sprint 1 backend modules in **ViziCheck**.

```mermaid
graph TD
    subgraph Core Framework
        AUTH[Authentication & RBAC]
        SECURITY[Security Policy & Sessions]
        AUDIT[Audit Logging Engine]
        TENANT[Tenant Management]
        USER[User Management]
    end

    subgraph Visitor & Host Operations
        VISITOR[Visitor Management]
        AVAIL[Host Availability]
        REQ[Visit Request Management]
        APPROVAL[Approval Workflow]
    end

    subgraph Pass & Gate Execution
        PASS[Visitor Pass Management]
        QR[QR Code Management]
        CHECKIN[Check-In / Check-Out Engine]
        NOTIF[Notification Pipeline]
    end

    AUTH --> USER
    AUTH --> TENANT
    SECURITY --> AUTH
    USER --> TENANT

    REQ --> VISITOR
    REQ --> USER
    REQ --> AVAIL
    REQ --> TENANT

    APPROVAL --> REQ
    APPROVAL --> USER

    PASS --> REQ
    PASS --> VISITOR
    PASS --> QR

    CHECKIN --> PASS
    CHECKIN --> QR
    CHECKIN --> REQ
    CHECKIN --> NOTIF

    NOTIF --> USER
    NOTIF --> VISITOR

    AUDIT -. Intercepts Write Operations .-> AUTH
    AUDIT -. Intercepts Write Operations .-> USER
    AUDIT -. Intercepts Write Operations .-> TENANT
    AUDIT -. Intercepts Write Operations .-> VISITOR
    AUDIT -. Intercepts Write Operations .-> REQ
    AUDIT -. Intercepts Write Operations .-> APPROVAL
    AUDIT -. Intercepts Write Operations .-> PASS
    AUDIT -. Intercepts Write Operations .-> CHECKIN
```

## Module Interactions Summary

1. **Auth & Security**: Manages JWT lifecycle, RBAC permission verification, account lockout policies, and session tracking.
2. **Tenants & Users**: Enforces multi-tenant data isolation across all database queries.
3. **Visit Request & Availability**: Validates host working hours and slot limits before creating visit requests.
4. **Approval & Pass Generation**: Auto-triggers visitor pass and cryptographically signed QR token upon request approval.
5. **Gate Security & Check-In**: Runs 12-stage validation pipeline on QR scan, updates occupancy metrics, and dispatches instant host notifications.
6. **Audit & Logging**: Asynchronously logs state modifications across all system operations.
