# backend/coding-standards.md

# ViziCheck Backend Coding Standards

## Purpose

This document defines coding conventions, architecture rules, naming standards, API standards, and development guidelines.

All backend code must follow these standards.

---

# Technology Standards

Framework:
FastAPI

Language:
Python 3.12+

ORM:
SQLAlchemy 2.0

Database:
MySQL 8

Validation:
Pydantic v2

Authentication:
JWT

Password Hashing:
bcrypt

---

# Architecture Rules

Architecture Pattern:

Modular Monolith

Flow:

API Layer
   ↓
Service Layer
   ↓
Repository Layer
   ↓
Database Layer

---

# Separation Of Concerns

## API Layer

Responsibilities:

* Route Definitions
* Request Validation
* Response Handling

Never:

* Write Business Logic
* Write Database Queries

---

## Service Layer

Responsibilities:

* Business Logic
* Validation Rules
* Workflow Execution

Never:

* Direct HTTP Handling

---

## Repository Layer

Responsibilities:

* CRUD Operations
* Query Execution

Never:

* Business Logic

---

## Model Layer

Responsibilities:

* Database Tables
* Relationships
* Constraints

---

# Naming Conventions

## Files

Use:

snake_case

Examples:

auth_service.py

visitor_repository.py

report_service.py

---

## Classes

Use:

PascalCase

Examples:

AuthService

VisitorRepository

TenantModel

---

## Functions

Use:

snake_case

Examples:

create_visitor()

approve_request()

generate_pass()

---

## Variables

Use:

snake_case

Examples:

visitor_id

request_status

created_at

---

## Constants

Use:

UPPER_CASE

Examples:

MAX_LOGIN_ATTEMPTS

JWT_EXPIRY_MINUTES

DEFAULT_PAGE_SIZE

---

# API Naming Standards

Good:

GET /users

GET /users/{id}

POST /users

PUT /users/{id}

DELETE /users/{id}

Bad:

GET /getUsers

POST /createUser

DELETE /removeUser

---

# Database Naming Standards

Tables:

snake_case

Examples:

visit_requests

visitor_passes

audit_logs

---

Columns:

snake_case

Examples:

created_at

updated_at

tenant_id

visitor_id

---

Primary Key:

id

---

Foreign Key:

<entity>_id

Examples:

user_id

tenant_id

request_id

---

# Response Standards

Success Response

{
"success": true,
"message": "Operation successful",
"data": {}
}

---

Error Response

{
"success": false,
"message": "Validation failed",
"errors": []
}

---

# Validation Rules

Validate:

* Email Format
* Phone Number
* Required Fields
* Date Formats
* Enum Values

Validation must occur:

1. Schema Layer
2. Service Layer

---

# Exception Handling

Use Custom Exceptions

Examples:

NotFoundException

ValidationException

AuthorizationException

BusinessRuleException

---

Never Return:

Raw Database Errors

Stack Traces

Internal Exceptions

---

# Logging Standards

Use Structured Logging

Required Log Levels:

INFO

WARNING

ERROR

CRITICAL

---

Log Examples

User Login

Request Approval

QR Validation

Check-In

Check-Out

System Errors

---

# Security Standards

Passwords:

bcrypt

Never Store Plain Text Passwords

---

JWT:

Access Token

Refresh Token

Token Expiry

---

Authorization:

RBAC

Permission Validation

---

Input Validation:

Mandatory

For Every Endpoint

---

# SQLAlchemy Standards

Use:

ORM Queries

Repository Pattern

Type Hints

Relationships

---

Avoid:

Raw SQL

Business Logic In Models

---

# Service Layer Standards

Each Module Must Have:

One Service

Example:

AuthService

VisitorService

ApprovalService

---

Responsibilities:

Business Logic Only

---

# Repository Standards

Each Module Must Have:

One Repository

Example:

UserRepository

RequestRepository

PassRepository

---

Responsibilities:

Database Access Only

---

# Dependency Injection

Use FastAPI Dependencies

Example:

Database Session

Current User

Permission Validator

---

# Pagination Standards

Default:

page=1

limit=20

Maximum:

limit=100

---

# Sorting Standards

Supported:

sort_by

order

Example:

?sort_by=created_at&order=desc

---

# Search Standards

Supported:

search

Example:

?search=rahul

---

# Audit Logging Standards

Always Log:

Login

Logout

Request Creation

Approval

Rejection

Pass Generation

Check-In

Check-Out

User Updates

Tenant Updates

---

# Testing Standards

Minimum Coverage:

80%

Types:

Unit Tests

Integration Tests

API Tests

---

Folder Structure

tests/

auth/

users/

requests/

approvals/

security/

---

# Code Review Checklist

Before Merge:

✓ Type Hints Present

✓ Validation Implemented

✓ Error Handling Implemented

✓ Logging Added

✓ Unit Tests Added

✓ Naming Standards Followed

✓ Security Rules Followed

✓ No Hardcoded Values

---

# Environment Variables

Never Hardcode:

Database URL

JWT Secret

API Keys

Email Credentials

---

Use:

.env

Environment Configuration

---

# Documentation Standards

Every API Must Have:

Description

Request Schema

Response Schema

Status Codes

Authorization Rules

Examples

---

# AI Development Instructions

When generating backend code:

* Follow project structure exactly.
* Use FastAPI best practices.
* Use SQLAlchemy ORM.
* Use Repository Pattern.
* Use Service Layer.
* Use JWT Authentication.
* Use RBAC Authorization.
* Add Type Hints.
* Add Logging.
* Add Validation.
* Generate production-ready code only.
