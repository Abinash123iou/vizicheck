# architecture/er-diagram.md

# ViziCheck Entity Relationship Diagram

## Core Relationships

```mermaid
erDiagram

ROLES ||--o{ USERS : has

USERS ||--o{ AUDIT_LOGS : creates

USERS ||--o| VISITORS : has

TENANTS ||--o{ USERS : manages

VISITORS ||--o{ VISIT_REQUESTS : creates

TENANTS ||--o{ AVAILABILITY_SLOTS : owns

AVAILABILITY_SLOTS ||--o{ VISIT_REQUESTS : selected_for

VISIT_REQUESTS ||--|| APPROVALS : has

APPROVALS ||--|| VISITOR_PASSES : generates

VISITOR_PASSES ||--|| QR_TOKENS : contains

VISITOR_PASSES ||--o{ VISITOR_CHECKINS : records

USERS ||--o{ NOTIFICATIONS : receives

USERS ||--o{ AUDIT_LOGS : creates
```

---

## Primary Entities

Roles

Users

Tenants

Visitors

Availability Slots

Visit Requests

Approvals

Visitor Passes

QR Tokens

Visitor Checkins

Notifications

Audit Logs

---

## Database Design Rules

Primary Key:

id

Foreign Key:

entity_id

Soft Delete:

supported

Audit Columns:

created_at

updated_at

created_by

updated_by
