# backend/audit-logging.md

# Audit Logging Specification

## Purpose

Track every important activity.

---

## Logged Events

Login

Logout

Password Reset

User Creation

Tenant Creation

Request Creation

Approval

Rejection

Pass Generation

QR Validation

Check-In

Check-Out

Role Changes

User Updates

---

## Audit Structure

Timestamp

User ID

Module

Action

Entity ID

Old Value

New Value

IP Address

---

## Retention Policy

5 Years

---

## Immutable Logs

Audit records cannot be edited or deleted.
