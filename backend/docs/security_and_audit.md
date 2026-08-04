# Security & Audit Management Module (SEC + AUDIT)

## Overview

The **Security Management** and **Audit Management** modules provide enterprise-grade protection, access control, session management, activity tracking, account security, and audit compliance for ViziCheck.

---

# 1. Security Management (SEC)

## Features

- **IP Address Tracking & Device Fingerprinting**: Captures IP addresses, User-Agent header, and custom device fingerprints on every login and sensitive security event.
- **Login Activity Monitoring & Event Logging**: Records `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `TOKEN_REFRESH`, `SESSION_REVOKED`, `ACCOUNT_LOCKED`, and `SUSPICIOUS_ACTIVITY` events with severity rating (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Account Lockout Policy**: Automatically locks a user account for **15 minutes** after **5 consecutive failed login attempts**.
- **Password Policy Enforcement**: Validates that passwords contain at least 8 characters, 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character.
- **Session Management & Token Revocation**: Generates unique session JTIs on login and supports real-time session listing and session revocation.
- **Suspicious Activity Detection**: Identifies logins originating from unrecognized device fingerprints or suspicious patterns.
- **Security Dashboard**: Provides aggregated metrics for total active sessions, 24-hour failed login count, locked accounts count, and suspicious activity alerts.

## API Endpoints

| Method | Endpoint | Description | Privileges Required |
| --- | --- | --- | --- |
| `GET` | `/api/v1/security/sessions` | List active sessions | Authenticated User |
| `DELETE` | `/api/v1/security/sessions/{id}` | Revoke active session | Owner / Tenant Admin / Super Admin |
| `GET` | `/api/v1/security/activity` | Search security activity logs | Security Officer / Tenant Admin / Super Admin |
| `GET` | `/api/v1/security/dashboard` | Get security metrics dashboard | Security Officer / Tenant Admin / Super Admin |

---

# 2. Audit Management (AUDIT)

## Features

- **Centralized Audit Engine**: Logs every critical operation across all system modules (`USER_MANAGEMENT`, `TENANT_MANAGEMENT`, `VISIT_REQUEST`, `VISITOR_PASS`, `CHECK_IN`, etc.).
- **Entity Change Tracking**: Captures state changes with `old_value` and `new_value` JSON payloads.
- **Multi-Tenant Audit Isolation**: Tenant Admins can strictly view and export audit trails belonging to their organization, while Super Admins possess full platform visibility.
- **Audit Trail Export**: Allows exporting audit logs to `CSV` or `JSON` formats with custom date range and filter criteria.

## API Endpoints

| Method | Endpoint | Description | Privileges Required |
| --- | --- | --- | --- |
| `GET` | `/api/v1/audit` | List audit logs with pagination and search | Tenant Admin / Super Admin |
| `GET` | `/api/v1/audit/export` | Export audit logs as CSV or JSON file | Tenant Admin / Super Admin |

---

## Architectural Flow

```
User Action
     │
     ▼
Service Layer (AuthService / RequestService / etc.)
     │
     ├──────────────────────────────┐
     ▼                              ▼
Security Engine (SecurityService) Audit Engine (AuditService)
     │                              │
     ▼                              ▼
user_sessions & security_logs    audit_logs
     │                              │
     └──────────────┬───────────────┘
                    ▼
           Security Dashboard & Audit Reports
```
