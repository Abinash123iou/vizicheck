# backend/database-schema.md

# ViziCheck Database Schema

## Purpose

Defines database entities, relationships, constraints, indexes, and business data structure.

Database Engine:
MySQL 8

ORM:
SQLAlchemy

Migration Tool:
Alembic

---

# Database Overview

Total Tables: 12

Core Flow:

User
  ↓
Tenant
  ↓
Visitor
  ↓
Visit Request
  ↓
Approval
  ↓
Visitor Pass
  ↓
QR Token
  ↓
Check-In / Check-Out
  ↓
Audit Log
  ↓
Reports

---

# Entity Relationship Summary

Role
│
└── User
├── Tenant
├── Approval
├── Notification
└── Audit Log

Visitor
│
└── Visit Request
├── Approval
└── Visitor Pass
└── QR Token
└── Check-In

---

# Table 1: roles

Purpose:
System roles and permissions.

Columns:

id BIGINT PK

name VARCHAR(50) UNIQUE

description VARCHAR(255)

created_at DATETIME

updated_at DATETIME

Records:

SUPER_ADMIN

TENANT

SECURITY

VISITOR

---

# Table 2: users

Purpose:
Internal platform users.

Columns:

id BIGINT PK

role_id BIGINT FK

tenant_id BIGINT FK

first_name VARCHAR(100)

last_name VARCHAR(100)

email VARCHAR(255) UNIQUE

phone VARCHAR(20)

password_hash VARCHAR(255)

is_active BOOLEAN

last_login DATETIME

created_at DATETIME

updated_at DATETIME

Relationships:

Many Users → One Role

Many Users → One Tenant (optional)

---

# Table 3: tenants

Purpose:
Organizations operating within facility.

Columns:

id BIGINT PK

name VARCHAR(255)

description TEXT

contact_person VARCHAR(255)

contact_email VARCHAR(255)

contact_phone VARCHAR(20)

status ENUM

created_at DATETIME

updated_at DATETIME

Status:

ACTIVE

INACTIVE

---

# Table 4: visitors

Purpose:
Visitor profiles.

Columns:

id BIGINT PK

user_id BIGINT FK

first_name VARCHAR(100)

last_name VARCHAR(100)

email VARCHAR(255)

phone VARCHAR(20)

company_name VARCHAR(255)

id_proof_type VARCHAR(50)

id_proof_number VARCHAR(100)

created_at DATETIME

updated_at DATETIME

Relationships:

One Visitor → One User (optional)

Indexes:

email

phone

---

# Table 5: availability_slots

Purpose:
Tenant availability schedule.

Columns:

id BIGINT PK

tenant_id BIGINT FK

available_date DATE

start_time TIME

end_time TIME

status ENUM

created_at DATETIME

updated_at DATETIME

Status:

AVAILABLE

BLOCKED

---

# Table 6: visit_requests

Purpose:
Visitor visit requests.

Columns:

id BIGINT PK

visitor_id BIGINT FK

tenant_id BIGINT FK

availability_slot_id BIGINT FK

purpose VARCHAR(255)

visit_date DATE

visit_time TIME

status ENUM

remarks TEXT

created_at DATETIME

updated_at DATETIME

Status:

PENDING

APPROVED

REJECTED

CANCELLED

COMPLETED

EXPIRED

Indexes:

visitor_id

tenant_id

status

visit_date

---

# Table 7: approvals

Purpose:
Approval workflow records.

Columns:

id BIGINT PK

request_id BIGINT FK

approved_by BIGINT FK

decision ENUM

comments TEXT

decision_time DATETIME

created_at DATETIME

Status:

APPROVED

REJECTED

Relationships:

Approval → Request

Approval → User

---

# Table 8: visitor_passes

Purpose:
Generated visitor passes.

Columns:

id BIGINT PK

request_id BIGINT FK

pass_number VARCHAR(100)

status ENUM

valid_from DATETIME

valid_to DATETIME

created_at DATETIME

updated_at DATETIME

Status:

ACTIVE

EXPIRED

REVOKED

USED

Indexes:

pass_number

status

---

# Table 9: qr_tokens

Purpose:
QR code management.

Columns:

id BIGINT PK

pass_id BIGINT FK

token VARCHAR(255)

status ENUM

expires_at DATETIME

created_at DATETIME

Status:

ACTIVE

EXPIRED

REVOKED

Indexes:

token

---

# Table 10: visitor_checkins

Purpose:
Visitor entry and exit tracking.

Columns:

id BIGINT PK

pass_id BIGINT FK

checkin_time DATETIME

checkout_time DATETIME

checked_in_by BIGINT FK

checked_out_by BIGINT FK

status ENUM

created_at DATETIME

Status:

CHECKED_IN

CHECKED_OUT

Indexes:

pass_id

status

---

# Table 11: notifications

Purpose:
System notifications.

Columns:

id BIGINT PK

user_id BIGINT FK

title VARCHAR(255)

message TEXT

is_read BOOLEAN

notification_type VARCHAR(100)

created_at DATETIME

Indexes:

user_id

is_read

---

# Table 12: audit_logs

Purpose:
System audit trail.

Columns:

id BIGINT PK

user_id BIGINT FK

action VARCHAR(255)

module VARCHAR(100)

entity_id BIGINT

old_value JSON

new_value JSON

ip_address VARCHAR(100)

created_at DATETIME

Indexes:

user_id

module

created_at

---

# Relationship Definitions

Role

1 → Many Users

---

Tenant

1 → Many Users (optional)

1 → Many Availability Slots

1 → Many Visit Requests

---

Visitor

1 → 1 User (optional)

1 → Many Visit Requests

---

Visit Request

1 → 1 Approval

1 → 1 Visitor Pass

---

Visitor Pass

1 → 1 QR Token

1 → Many Check-In Records

---

User

1 → Many Approvals

1 → Many Notifications

1 → Many Audit Logs

---

# Soft Delete Strategy

Tables Using Soft Delete:

users

tenants

availability_slots

visit_requests

visitor_passes

Implementation:

is_deleted BOOLEAN

deleted_at DATETIME

---

# Audit Requirements

Log Events:

Login

Logout

Create Request

Update Request

Approve Request

Reject Request

Generate Pass

QR Scan

Check-In

Check-Out

User Management

Tenant Management

---

# Database Indexing Strategy

High Frequency Indexes:

users.email

visitors.email

visit_requests.status

visit_requests.visit_date

visitor_passes.pass_number

qr_tokens.token

audit_logs.created_at

notifications.user_id

---

# Data Retention Policy

Audit Logs:
5 Years

Visit Records:
5 Years

Notifications:
1 Year

Check-In Records:
5 Years

Reports:
Permanent

---

# Naming Conventions

Tables:
snake_case

Columns:
snake_case

Primary Keys:
id

Foreign Keys: <entity>_id

Timestamps:

created_at

updated_at

deleted_at

---

# Future Expansion

Reserved for:

Multi-Facility Support

Multi-Tenant SaaS

Email Service

SMS Service

Push Notifications

Document Uploads

Face Recognition Integration

Visitor Kiosk Integration
