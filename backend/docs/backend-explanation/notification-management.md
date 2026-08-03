# Notification Management Module Documentation

**Module Code:** `NOTIF`  
**Sprint / Day:** Sprint 1 — Day 14  
**Architecture Layer:** Clean Architecture (Domain Models, Validators, Services, Repositories, Mappers, Controllers)  
**Supported Delivery Channels:** Email, SMS, In-App Notifications  

---

## 1. Overview

The **Notification Management Module** provides a centralized, multi-tenant communication pipeline for the ViziCheck Enterprise Visitor Management System. It delivers system lifecycle events across Email, SMS, and In-App channels, maintaining delivery tracking, retry mechanisms, template variable interpolation, user opt-in/opt-out preferences, audit logging, and strict multi-tenant isolation.

---

## 2. Integration Architecture

```
                    ┌────────────────────────────┐
                    │     Business Modules       │
                    │----------------------------│
                    │ Visit Requests             │
                    │ Approval Workflow          │
                    │ Visitor Pass               │
                    │ Check-In / Check-Out       │
                    │ Availability               │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │ Notification Service Layer │
                    │----------------------------│
                    │ Event Dispatcher           │
                    │ Template Engine            │
                    │ Preference Manager         │
                    │ Delivery Status Tracker    │
                    └─────────────┬──────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
           Email Provider    SMS Provider   In-App Notification
                 │                │                │
                 └────────────────┴────────────────┘
                                  │
                                  ▼
                        notification_history
```

---

## 3. Database Schema

### Table 1: `notifications`
Stores historical log and status lifecycle of every notification sent.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-increment primary key |
| `uuid` | String(36) | Unique notification UUID |
| `tenant_id` | Integer (FK) | Multi-tenant isolation foreign key |
| `recipient_user_id` | Integer (FK, Nullable) | Target system user ID |
| `recipient_email` | String(255), Nullable | Destination email address |
| `recipient_phone` | String(50), Nullable | Destination phone number |
| `notification_type` | String(100) | Event category enum |
| `channel` | String(50) | `EMAIL`, `SMS`, `IN_APP` |
| `title` | String(255) | Title / subject line |
| `message` | Text | Body text content |
| `status` | String(50) | `PENDING`, `QUEUED`, `SENDING`, `DELIVERED`, `READ`, `FAILED`, `CANCELLED` |
| `priority` | String(50) | `LOW`, `MEDIUM`, `HIGH`, `URGENT` |
| `template_id` | Integer (FK, Nullable) | Template referenced |
| `reference_module` | String(100), Nullable | Originating module name |
| `reference_id` | Integer, Nullable | Originating record ID |
| `sent_at` | DateTime, Nullable | Timestamp sent |
| `delivered_at` | DateTime, Nullable | Timestamp delivered/read |
| `retry_count` | Integer | Retry attempt counter |

### Table 2: `notification_templates`
Stores reusable templates with placeholder variable interpolation (`{variable_name}`).

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Primary key |
| `tenant_id` | Integer (FK, Nullable) | Tenant scope (NULL = system global default) |
| `template_code` | String(100) | Unique template code string |
| `name` | String(255) | Human readable template name |
| `channel` | String(50) | Delivery channel |
| `subject` | String(255), Nullable | Subject line template |
| `body` | Text | Body template text with placeholders |
| `variables` | JSON, Nullable | List of allowed variable names |
| `is_active` | Boolean | Opt-in active status |

### Table 3: `notification_preferences`
Stores per-user channel delivery opt-in/opt-out preferences.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Primary key |
| `tenant_id` | Integer (FK) | Tenant ID |
| `user_id` | Integer (FK) | User ID |
| `email_enabled` | Boolean | Opt-in flag for Email channel |
| `sms_enabled` | Boolean | Opt-in flag for SMS channel |
| `inapp_enabled` | Boolean | Opt-in flag for In-App channel |

---

## 4. API Endpoints

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/notifications/send` | Dispatch a single notification | `NOTIFICATION_SEND` |
| `GET` | `/api/v1/notifications` | List notifications history (paginated & filtered) | `NOTIFICATION_READ` |
| `PATCH` | `/api/v1/notifications/{id}/read` | Mark in-app notification as READ | Active User |
| `GET` | `/api/v1/notifications/statistics` | Retrieve dashboard analytics & success rates | `NOTIFICATION_READ` |
| `GET` | `/api/v1/notifications/preferences` | Get user channel delivery preferences | Active User |
| `PUT` | `/api/v1/notifications/preferences` | Update user channel delivery preferences | Active User |
| `POST` | `/api/v1/notifications/templates` | Create a notification template | `NOTIFICATION_MANAGE_TEMPLATES` |
| `GET` | `/api/v1/notifications/templates` | List notification templates | `NOTIFICATION_READ` |

---

## 5. Notification Status Lifecycle

```
PENDING ──► QUEUED ──► SENDING ──► DELIVERED ──► READ
                           │
                           ▼
                        FAILED ──► RETYING ──► CANCELLED
```

---

## 6. Audit Logging & Security

- **Audit Actions:** `NOTIFICATION_SENT`, `NOTIFICATION_READ`, `TEMPLATE_CREATED`, `PREFERENCES_UPDATED`.
- **Tenant Isolation:** Enforced at Repository and Service levels via `tenant_id` database queries.
- **RBAC Rules:** Enforced via `has_permission(Permissions.NOTIFICATION_SEND)` and related permission constants.
