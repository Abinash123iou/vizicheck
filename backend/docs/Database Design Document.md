## Database Design Documents v1.0

## Part 1: Database Foundation

## 1. Database Overview

Database: MySQL
Development Server: XAMPP
Backend ORM: SQLAlchemy
Backend Framework: FastAPI

The database will support:
* Authentication and role access
* Tenant and visitor profiles
* Calendar-based availability
* Visit requests
* Approval workflow
* QR pass generation
* Check-in/check-out tracking
* Audit logs
* Notifications

## 2. Final Table Inventory

1. roles
2. users
3. tenants
4. visitors
5. availability_slots
6. visit_requests
7. approvals
8. visitor_passes
9. qr_tokens
10. visitor_checkins
11. audit_logs
12. notifications

## 3. Relationship Overview  
![](images/4f7878cb9e9014376e04fe031987202d51799d74d910cddf2f3a0c459a8359e8.jpg)

## 4. Common Columns Standard

Most business tables include:
* created_at (DATETIME)
* updated_at (DATETIME, Nullable)
* is_deleted (BOOLEAN, Default false)
* deleted_at (DATETIME, Nullable)

For V1, we will use BIGINT AUTO_INCREMENT primary keys:
Example:
`id BIGINT AUTO_INCREMENT PRIMARY KEY`

---

## Part 2: Identity Tables

### Table 1: roles
Purpose: Stores role definitions for RBAC.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>name</td><td>VARCHAR(50)</td><td>Unique, Not Null</td></tr>
  <tr><td>description</td><td>VARCHAR(255)</td><td>Nullable</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

Default roles:
* SUPER_ADMIN
* TENANT
* SECURITY
* VISITOR

### Table 2: users  
Purpose: Common authentication table for all user types.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>role_id</td><td>BIGINT</td><td>Foreign Key → roles.id</td></tr>
  <tr><td>tenant_id</td><td>BIGINT</td><td>Foreign Key → tenants.id, Nullable</td></tr>
  <tr><td>first_name</td><td>VARCHAR(100)</td><td>Not Null</td></tr>
  <tr><td>last_name</td><td>VARCHAR(100)</td><td>Not Null</td></tr>
  <tr><td>email</td><td>VARCHAR(255)</td><td>Unique, Not Null</td></tr>
  <tr><td>phone</td><td>VARCHAR(20)</td><td>Nullable</td></tr>
  <tr><td>password_hash</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>is_active</td><td>BOOLEAN</td><td>Default true</td></tr>
  <tr><td>last_login</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>is_deleted</td><td>BOOLEAN</td><td>Default false</td></tr>
  <tr><td>deleted_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

Indexes:
* idx_users_email (email)
* idx_users_role_id (role_id)
* idx_users_tenant_id (tenant_id)

---

## Part 3: Profile Tables

### Table 3: tenants
Purpose: Stores tenant/organization details operating within the facility.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>name</td><td>VARCHAR(255)</td><td>Not Null, Unique</td></tr>
  <tr><td>description</td><td>TEXT</td><td>Nullable</td></tr>
  <tr><td>contact_person</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>contact_email</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>contact_phone</td><td>VARCHAR(20)</td><td>Nullable</td></tr>
  <tr><td>status</td><td>ENUM('ACTIVE', 'INACTIVE')</td><td>Not Null, Default 'ACTIVE'</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>is_deleted</td><td>BOOLEAN</td><td>Default false</td></tr>
  <tr><td>deleted_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

### Table 4: visitors
Purpose: Stores visitor profile details.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>user_id</td><td>BIGINT</td><td>Foreign Key → users.id, Nullable</td></tr>
  <tr><td>first_name</td><td>VARCHAR(100)</td><td>Not Null</td></tr>
  <tr><td>last_name</td><td>VARCHAR(100)</td><td>Not Null</td></tr>
  <tr><td>email</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>phone</td><td>VARCHAR(20)</td><td>Not Null</td></tr>
  <tr><td>company_name</td><td>VARCHAR(255)</td><td>Nullable</td></tr>
  <tr><td>id_proof_type</td><td>VARCHAR(50)</td><td>Nullable</td></tr>
  <tr><td>id_proof_number</td><td>VARCHAR(100)</td><td>Nullable</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

Indexes:
* idx_visitors_user_id (user_id)
* idx_visitors_email (email)
* idx_visitors_phone (phone)

---

## Part 4: Workflow Tables

### Table 5: availability_slots
Purpose: Stores calendar-based tenant availability.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>tenant_id</td><td>BIGINT</td><td>Foreign Key → tenants.id</td></tr>
  <tr><td>available_date</td><td>DATE</td><td>Not Null</td></tr>
  <tr><td>start_time</td><td>TIME</td><td>Not Null</td></tr>
  <tr><td>end_time</td><td>TIME</td><td>Not Null</td></tr>
  <tr><td>status</td><td>ENUM('AVAILABLE', 'BLOCKED')</td><td>Not Null, Default 'AVAILABLE'</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>is_deleted</td><td>BOOLEAN</td><td>Default false</td></tr>
  <tr><td>deleted_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

Constraints:
* end_time must be greater than start_time
* tenant_id must exist in tenants table

Indexes:
* idx_availability_tenant_id (tenant_id)
* idx_availability_date (available_date)

### Table 6: visit_requests
Purpose: Stores visitor requests to meet a tenant. This is the central transaction table of ViziCheck.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>visitor_id</td><td>BIGINT</td><td>Foreign Key → visitors.id</td></tr>
  <tr><td>tenant_id</td><td>BIGINT</td><td>Foreign Key → tenants.id</td></tr>
  <tr><td>availability_slot_id</td><td>BIGINT</td><td>Foreign Key → availability_slots.id</td></tr>
  <tr><td>purpose</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>visit_date</td><td>DATE</td><td>Not Null</td></tr>
  <tr><td>visit_time</td><td>TIME</td><td>Not Null</td></tr>
  <tr><td>status</td><td>ENUM('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'COMPLETED', 'EXPIRED')</td><td>Default 'PENDING'</td></tr>
  <tr><td>remarks</td><td>TEXT</td><td>Nullable</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>is_deleted</td><td>BOOLEAN</td><td>Default false</td></tr>
  <tr><td>deleted_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

Constraints:
* visitor_id must exist
* tenant_id must exist
* visit_date cannot be in the past during request creation

Indexes:
* idx_requests_visitor_id (visitor_id)
* idx_requests_tenant_id (tenant_id)
* idx_requests_status (status)
* idx_requests_visit_date (visit_date)

### Table 7: approvals
Purpose: Stores approval decisions for visit requests.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>request_id</td><td>BIGINT</td><td>Foreign Key → visit_requests.id</td></tr>
  <tr><td>approved_by</td><td>BIGINT</td><td>Foreign Key → users.id</td></tr>
  <tr><td>decision</td><td>ENUM('APPROVED', 'REJECTED')</td><td>Not Null</td></tr>
  <tr><td>comments</td><td>TEXT</td><td>Nullable</td></tr>
  <tr><td>decision_time</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
</table>

Indexes:
* idx_approvals_request_id (request_id)
* idx_approvals_approved_by (approved_by)

---

## Part 5: Operational Tables

### Table 8: visitor_passes
Purpose: Stores approved visitor passes. A pass is created only after request approvals are completed.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>request_id</td><td>BIGINT</td><td>Foreign Key → visit_requests.id</td></tr>
  <tr><td>pass_number</td><td>VARCHAR(100)</td><td>Unique, Not Null</td></tr>
  <tr><td>status</td><td>ENUM('ACTIVE', 'EXPIRED', 'REVOKED', 'USED')</td><td>Not Null, Default 'ACTIVE'</td></tr>
  <tr><td>valid_from</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>valid_to</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>updated_at</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>is_deleted</td><td>BOOLEAN</td><td>Default false</td></tr>
  <tr><td>deleted_at</td><td>DATETIME</td><td>Nullable</td></tr>
</table>

Indexes:
* idx_passes_request_id (request_id)
* idx_passes_number (pass_number)
* idx_passes_status (status)

### Table 9: qr_tokens
Purpose: Stores QR verification tokens associated with passes.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>pass_id</td><td>BIGINT</td><td>Foreign Key → visitor_passes.id</td></tr>
  <tr><td>token</td><td>VARCHAR(255)</td><td>Unique, Not Null</td></tr>
  <tr><td>status</td><td>ENUM('ACTIVE', 'EXPIRED', 'REVOKED')</td><td>Not Null, Default 'ACTIVE'</td></tr>
  <tr><td>expires_at</td><td>DATETIME</td><td>Not Null</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
</table>

Indexes:
* idx_qr_pass_id (pass_id)
* idx_qr_token (token)

### Table 10: visitor_checkins
Purpose: Stores visitor entry and exit records. Tracks visitor presence inside the facility.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>pass_id</td><td>BIGINT</td><td>Foreign Key → visitor_passes.id</td></tr>
  <tr><td>checkin_time</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>checkout_time</td><td>DATETIME</td><td>Nullable</td></tr>
  <tr><td>checked_in_by</td><td>BIGINT</td><td>Foreign Key → users.id</td></tr>
  <tr><td>checked_out_by</td><td>BIGINT</td><td>Foreign Key → users.id, Nullable</td></tr>
  <tr><td>status</td><td>ENUM('CHECKED_IN', 'CHECKED_OUT')</td><td>Not Null</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
</table>

Indexes:
* idx_checkins_pass_id (pass_id)
* idx_checkins_status (status)

---

## Part 6: System Tables

### Table 11: audit_logs
Purpose: Stores all critical system activities for traceability, security, and auditing.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>user_id</td><td>BIGINT</td><td>Foreign Key → users.id</td></tr>
  <tr><td>action</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>module</td><td>VARCHAR(100)</td><td>Not Null</td></tr>
  <tr><td>entity_id</td><td>BIGINT</td><td>Nullable</td></tr>
  <tr><td>old_value</td><td>JSON</td><td>Nullable</td></tr>
  <tr><td>new_value</td><td>JSON</td><td>Nullable</td></tr>
  <tr><td>ip_address</td><td>VARCHAR(100)</td><td>Nullable</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
</table>

Indexes:
* idx_audit_user_id (user_id)
* idx_audit_module (module)
* idx_audit_created_at (created_at)

### Table 12: notifications
Purpose: Stores all system-generated notifications.

<table>
  <tr><td>Column</td><td>Type</td><td>Constraint</td></tr>
  <tr><td>id</td><td>BIGINT</td><td>Primary Key, Auto Increment</td></tr>
  <tr><td>user_id</td><td>BIGINT</td><td>Foreign Key → users.id</td></tr>
  <tr><td>title</td><td>VARCHAR(255)</td><td>Not Null</td></tr>
  <tr><td>message</td><td>TEXT</td><td>Not Null</td></tr>
  <tr><td>is_read</td><td>BOOLEAN</td><td>Default false</td></tr>
  <tr><td>notification_type</td><td>VARCHAR(100)</td><td>Not Null</td></tr>
  <tr><td>created_at</td><td>DATETIME</td><td>Not Null</td></tr>
</table>

Indexes:
* idx_notifications_user_id (user_id)
* idx_notifications_is_read (is_read)

---

## Part 7: Business Rule Mapping & Foreign Key Cardinality

### Recommended Foreign Key Cardinality
* Role: 1 → Many Users
* Tenant: 1 → Many Users (optional)
* Visitor: 1 → 1 User (optional)
* Tenant: 1 → Many Availability Slots
* Visitor: 1 → Many Visit Requests
* Tenant: 1 → Many Visit Requests
* Visit Request: 1 → 1 Approval
* Visit Request: 1 → 1 Visitor Pass
* Visitor Pass: 1 → 1 QR Token
* Visitor Pass: 1 → Many Check-In Records (future-proof)
* User: 1 → Many Audit Logs
* User: 1 → Many Notifications
