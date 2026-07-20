# backend/auth-rbac.md

# ViziCheck Authentication & RBAC Specification

## Purpose

This document defines:

* Authentication Architecture
* JWT Token Strategy
* Role-Based Access Control (RBAC)
* Permission Matrix
* Authorization Rules
* Security Policies

---

# Authentication Overview

Authentication verifies user identity before granting access to protected resources.

Authentication Method:

JWT Authentication

Token Type:

Bearer Token

Authorization Header:

Authorization: Bearer <token>

---

# Supported User Roles

## SUPER_ADMIN

Highest privilege role.

Responsibilities:

* Platform Administration
* User Management
* Tenant Management
* Reporting
* Audit Monitoring

---

## TENANT_ADMIN

Represents an organization inside the facility.

Responsibilities:

* Approve Visitor Requests
* Reject Visitor Requests
* Manage Availability
* View Reports

---

## SECURITY_OFFICER

Handles visitor verification and gate operations.

Responsibilities:

* QR Validation
* Check-In
* Check-Out
* Active Visitor Monitoring

---

## VISITOR

External user visiting the facility.

Responsibilities:

* Register Account
* Create Visit Requests
* Track Requests
* View Passes

---

# JWT Architecture

## Access Token

Purpose:

API Authentication

Expiry:

15 Minutes

Payload:

{
user_id,
role,
email,
token_type
}

---

## Refresh Token

Purpose:

Generate new access token

Expiry:

7 Days

Stored:

Database

Revocable:

Yes

---

# Login Flow

User Login
    ↓
Validate Credentials
    ↓
Generate Access Token
    ↓
Generate Refresh Token
    ↓
Store Refresh Token
    ↓
Return Tokens

---

# Refresh Token Flow

Access Token Expired
      ↓
Validate Refresh Token
      ↓
Generate New Access Token
      ↓
Return New Access Token

---

# Logout Flow

User Logout
     ↓
Invalidate Refresh Token
     ↓
Clear Session
     ↓
Audit Log Entry

---

# Password Policy

Minimum Length:
8 Characters

Required:

* Uppercase Letter
* Lowercase Letter
* Number
* Special Character

Examples:

Valid:
Password@123

Invalid:
password

---

# Password Storage

Algorithm:

bcrypt

Never Store:

Plain Text Passwords

Required:

Salted Hashing

---

# Role Hierarchy

SUPER_ADMIN
    ↓
TENANT_ADMIN
    ↓
SECURITY_OFFICER
    ↓
VISITOR

---

# Permission Codes

## User Management

USER_CREATE
USER_VIEW
USER_UPDATE
USER_DELETE

---

## Tenant Management

TENANT_CREATE
TENANT_VIEW
TENANT_UPDATE
TENANT_DELETE

---

## Visitor Management

VISITOR_VIEW
VISITOR_UPDATE

---

## Availability

AVAILABILITY_CREATE
AVAILABILITY_VIEW
AVAILABILITY_UPDATE
AVAILABILITY_DELETE

---

## Visit Requests

REQUEST_CREATE
REQUEST_VIEW
REQUEST_UPDATE
REQUEST_CANCEL

---

## Approval

APPROVAL_APPROVE
APPROVAL_REJECT

---

## Pass

PASS_GENERATE
PASS_VIEW
PASS_REVOKE

---

## QR

QR_VALIDATE

---

## Security

CHECKIN_CREATE
CHECKOUT_CREATE

---

## Reports

REPORT_VIEW
REPORT_EXPORT

---

## Audit

AUDIT_VIEW

---

# Permission Matrix

SUPER_ADMIN

Permissions:
All Permissions

---

TENANT_ADMIN

Permissions:
REQUEST_VIEW
APPROVAL_APPROVE
APPROVAL_REJECT
PASS_VIEW
AVAILABILITY_CREATE
AVAILABILITY_VIEW
AVAILABILITY_UPDATE
AVAILABILITY_DELETE
REPORT_VIEW
NOTIFICATION_VIEW

---

SECURITY_OFFICER

Permissions:
REQUEST_VIEW
PASS_VIEW
QR_VALIDATE
CHECKIN_CREATE
CHECKOUT_CREATE
REPORT_VIEW
NOTIFICATION_VIEW

---

VISITOR

Permissions:

REQUEST_CREATE
REQUEST_VIEW
REQUEST_CANCEL
PASS_VIEW
PROFILE_UPDATE
NOTIFICATION_VIEW

---

# API Authorization Rules

## Public APIs

/auth/login

/auth/forgot-password

/auth/reset-password

/visitors/register

---

## Authenticated APIs

Require JWT Token

Examples:

/requests

/passes

/notifications

/profile

---

## Admin Only APIs

/users

/tenants

/audit-logs

---

## Tenant Only APIs

/approvals

/availability

---

## Security Only APIs

/security/checkin

/security/checkout

/security/scan

---

# FastAPI Authorization Strategy

Use Dependency Injection.

Example:

get_current_user()
    ↓
verify_role()
    ↓
verify_permission()
    ↓
Execute Endpoint

---

# Route Protection Levels

Level 1

Public

No Authentication

---

Level 2

Authenticated

Valid JWT Required

---

Level 3

Role Protected

Specific Role Required

---

Level 4

Permission Protected

Specific Permission Required

---

# Account Security Rules

Maximum Login Attempts:

5

After Failure:

Account Locked

Lock Duration:

15 Minutes

---

# Token Revocation Rules

Refresh Token Revoked When:

* Logout
* Password Change
* Account Disabled

---

# Audit Requirements

Log Events:

Login

Logout

Password Reset

User Creation

Role Changes

Permission Changes

Failed Login Attempts

Token Revocation

---

# Security Headers

Enable:

HTTPS

CORS

Secure Cookies

Content Security Policy

Rate Limiting

---

# Future Enhancements

Multi-Factor Authentication (MFA)

Single Sign-On (SSO)

Google Login

Microsoft Login

Biometric Authentication

Device-Based Authentication

Session Monitoring

---

# AI Development Instructions

When generating authentication code:

* Use JWT Authentication
* Use bcrypt Password Hashing
* Use RBAC Authorization
* Implement Refresh Tokens
* Use Dependency Injection
* Protect Sensitive Routes
* Log Security Events
* Follow FastAPI Security Best Practices
