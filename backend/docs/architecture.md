# backend/architecture.md

# ViziCheck Backend Architecture

## Purpose

This document defines the backend architecture, design principles, component interactions, request lifecycle, module communication, and scalability strategy.

---

# Architecture Overview

Architecture Type:

Modular Monolith

Framework:

FastAPI

Database:

MySQL

ORM:

SQLAlchemy

Authentication:

JWT + RBAC

Deployment:

Docker Container

---

# High Level Architecture

Client Applications

* React Admin Portal
* Flutter Mobile App
       ↓
API Gateway Layer
(FastAPI Routes)
       ↓
Business Layer
(Services)
      ↓
Data Access Layer
(Repositories)
      ↓
Database Layer
(MySQL)

---

# Architecture Principles

## Separation of Concerns

Each layer has one responsibility.

API Layer
   ↓
Service Layer
   ↓
Repository Layer
   ↓
Database Layer

---

## Single Responsibility Principle

Every module performs one business function.

Example:

AuthService
Only authentication logic.
ApprovalService
Only approval logic.

---

## Dependency Direction

Allowed:

API
  ↓
Service
  ↓
Repository
  ↓
Database

Not Allowed:

API → Database

Repository → Service

Database → API

---

# Backend Component Architecture

┌─────────────────────────────┐
│      React Admin Portal     │
└──────────────┬──────────────┘
               │
               │ REST API
               │
┌──────────────▼──────────────┐
│      Flutter Mobile App     │
└──────────────┬──────────────┘
               │
               │ REST API
               ▼
┌─────────────────────────────┐
│      FastAPI Backend        │
│         (API Layer)         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Authentication Module   │
│     Visitor Module          │
│     Request Module          │
│     Approval Module         │
│     Pass Module             │
│     QR Module               │
│     Security Module         │
│     Notification Module     │
│     Reporting Module        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Service Layer         │
│   Business Logic Layer      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Repository Layer        │
│     Data Access Layer       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      SQLAlchemy ORM         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       MySQL Database        │
└─────────────────────────────┘

---

# Module Architecture

## Authentication Module

Responsibilities:

* Login
* Logout
* JWT Validation
* Refresh Tokens

Dependencies:

User Module

RBAC Module

---

## User Module

Responsibilities:

* User CRUD
* User Status Management
* Role Assignment

Dependencies:

Authentication

---

## Tenant Module

Responsibilities:

* Tenant Management
* Tenant Status

Dependencies:

User Module

---

## Visitor Module

Responsibilities:

* Visitor Registration
* Visitor Profiles

Dependencies:

Authentication

---

## Request Module

Responsibilities:

* Visit Request Creation
* Request Tracking

Dependencies:

Visitor Module
Tenant Module

---

## Approval Module

Responsibilities:

* Approve Requests
* Reject Requests

Dependencies:

Request Module

---

## Pass Module

Responsibilities:

* Pass Generation
* Pass Status Management

Dependencies:

Approval Module

---

## QR Module

Responsibilities:

* QR Generation
* QR Validation

Dependencies:

Pass Module

---

## Security Module

Responsibilities:

* Check-In
* Check-Out
* Active Visitors

Dependencies:

QR Module

---

## Notification Module

Responsibilities:

* System Notifications
* Event Notifications

Dependencies:

All Modules

---

## Audit Module

Responsibilities:

* Event Logging
* Activity Tracking

Dependencies:

All Modules

---

## Reporting Module

Responsibilities:

* Analytics
* Dashboard Metrics

Dependencies:

All Modules

---

# Request Lifecycle

Example:

Visitor Creates Request
    ↓
API Route
    ↓
Request Service
    ↓
Request Repository
    ↓
Database Save
    ↓
Notification Service
    ↓
Audit Service
    ↓
Response Returned

---

# Visitor Journey Architecture

Visitor Registration
    ↓
Visit Request
    ↓
Approval
    ↓
Pass Generation
    ↓
QR Generation
    ↓
QR Validation
    ↓
Check-In
    ↓
Check-Out
    ↓
Audit Logging
    ↓
Reporting

---

# Authentication Flow

User Login
    ↓
Validate Credentials
    ↓
Generate JWT
    ↓
Return Access Token
    ↓
Access Protected APIs
    ↓
Validate Token
    ↓
Verify Permissions
    ↓
Execute Business Logic

---

# Authorization Flow

Request Received
     ↓
Authenticate User
     ↓
Identify Role
     ↓
Check Permission
     ↓
Grant Access

OR

Deny Access

---

# Notification Architecture

Business Event
     ↓
Notification Service
     ↓
Create Notification
     ↓
Store Database Record
     ↓
Send To User

Examples:

Request Submitted

Request Approved

Pass Generated

Check-In Completed

---

# Audit Logging Architecture

Business Event
     ↓
Audit Service
     ↓
Capture Event
     ↓
Store Audit Log
     ↓
Generate Audit Trail

Events:

Login
Approval
Pass Generation
Check-In
Check-Out

---

# Error Handling Architecture

API Layer
    ↓
Global Exception Handler
    ↓
Standard Error Response

Example:

{
"success": false,
"message": "Request not found"
}

---

# Database Architecture

Database:

MySQL

Core Tables:

roles

users

tenants

visitors

availability_slots

visit_requests

approvals

visitor_passes

qr_tokens

visitor_checkins

notifications

audit_logs

---

# Scalability Strategy

Current:

Modular Monolith

Future:

Microservices Ready

Potential Services:

Authentication Service

Notification Service

Reporting Service

Audit Service

File Service

---

# Security Architecture

Authentication:

JWT

Authorization:

RBAC

Password Storage:

bcrypt

Transport Security:

HTTPS

API Security:

Protected Routes

Input Validation

Rate Limiting

Audit Logging

---

# Deployment Architecture

Client
   ↓
Nginx
   ↓
FastAPI
   ↓
MySQL
   ↓
Persistent Storage

---

# Monitoring Strategy

Monitor:

API Response Time

Failed Logins

QR Validation Errors

Database Performance

Active Visitors

System Errors

---

# Future Integrations

Email Service

SMS Service

Push Notifications

Visitor Kiosk

Face Recognition

Access Control Systems

SSO Integration

---

# AI Development Instructions

When generating backend code:

* Follow Modular Monolith Architecture.
* Use Service Layer for business logic.
* Use Repository Pattern for database access.
* Keep modules loosely coupled.
* Log all critical events.
* Follow JWT + RBAC architecture.
* Maintain scalability for future microservice migration.
