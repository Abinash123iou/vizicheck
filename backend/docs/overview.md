# backend/overview.md

# ViziCheck Backend Overview

## Project Information

Project Name:
ViziCheck

Full Name:
Smart Visitor Management System

Version:
1.0

Project Type:
Enterprise Visitor Management Platform

Architecture:
Modular Monolithic Architecture

Backend Framework:
FastAPI

Database:
MySQL 8

Authentication:
JWT Authentication

Authorization:
Role-Based Access Control (RBAC)

API Style:
REST API

---

# Project Summary

ViziCheck is a production-oriented Smart Visitor Management System designed to digitize and automate the complete visitor lifecycle across corporate offices, business parks, educational institutions, and secure facilities.

The platform eliminates paper-based visitor management processes by providing digital visitor registration, approval workflows, QR-based visitor passes, real-time check-in/check-out tracking, notifications, audit logging, and reporting.

---

# Business Problem

Traditional visitor management systems rely on:

* Paper Registers
* Manual Approvals
* Security Phone Calls
* Physical Visitor Passes
* Manual Record Keeping

Problems:

* Long Visitor Wait Times
* Human Errors
* Poor Tracking
* Security Risks
* Missing Audit Trails
* Difficult Reporting

---

# Proposed Solution

ViziCheck provides:

* Visitor Self Registration
* Digital Visit Requests
* Tenant Approval Workflow
* QR-Based Visitor Passes
* Security Verification
* Check-In Management
* Check-Out Management
* Audit Logging
* Reporting & Analytics

---

# User Roles

## Super Admin

Responsibilities:

* Manage Platform
* Manage Users
* Manage Tenants
* View Reports
* Monitor Operations

---

## Tenant

Responsibilities:

* Review Visitor Requests
* Approve Visitors
* Reject Visitors
* Manage Availability

---

## Visitor

Responsibilities:

* Register
* Submit Requests
* View Request Status
* Access QR Passes

---

## Security Officer

Responsibilities:

* Verify QR Passes
* Check-In Visitors
* Check-Out Visitors
* Monitor Active Visitors

---

# Core Modules

1. Authentication

2. User Management

3. Tenant Management

4. Visitor Management

5. Availability Management

6. Visit Request Management

7. Approval Workflow

8. Pass Management

9. QR Verification

10. Security Operations

11. Notifications

12. Reporting & Analytics

13. Audit Logging

---

# Technology Stack

## Backend

* FastAPI
* Python 3.12

## Database

* MySQL 8
* SQLAlchemy
* Alembic

## Authentication

* JWT
* Bcrypt

## API Documentation

* Swagger UI
* OpenAPI

## Development Tools

* Git
* GitHub
* Docker
* Postman

---

# Project Metrics

User Roles:
4

Core Modules:
13

Database Tables:
12

REST APIs:
55

Web Screens:
20+

Mobile Screens:
14+

Development Sprints:
6

Project Duration:
12 Weeks

---

# Key Features

* Secure Authentication
* Role-Based Access Control
* Visitor Registration
* Visit Request Submission
* Approval Workflow
* QR Pass Generation
* QR Verification
* Check-In Tracking
* Check-Out Tracking
* Notification System
* Audit Logging
* Reporting Dashboard

---

# Security Requirements

* JWT Authentication
* Password Hashing
* Protected APIs
* Role-Based Authorization
* Audit Logging
* QR Verification
* Secure Database Access

---

# Non Functional Requirements

Performance:
Support concurrent users efficiently.

Scalability:
Support future expansion.

Reliability:
Maintain data consistency.

Security:
Protect visitor and tenant data.

Maintainability:
Modular codebase with clean architecture.

Availability:
24x7 operational readiness.

---

# Backend Goals

The backend should:

* Follow Clean Architecture
* Use Modular Design
* Provide REST APIs
* Maintain Audit Trails
* Support Role-Based Access Control
* Generate QR Passes
* Manage Visitor Lifecycle
* Provide Reporting Data

---

# Success Criteria

A successful backend implementation should allow:

Visitor Registration
       ↓
Visit Request
       ↓
Tenant Approval
       ↓
QR Pass Generation
       ↓
Security Verification
       ↓
Check-In
       ↓
Check-Out
       ↓
Audit Logging
       ↓
Reporting

without manual intervention.
