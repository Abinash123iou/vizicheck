## ViziCheck SRS v1.0

## Section 1 – Introduction

## 1.1 Purpose

The purpose of this Software Requirements Specification (SRS) document is to define the functional and non-functional requirements of the ViziCheck platform.

ViziCheck is a Smart Visitor Access and Verification Platform designed to digitize visitor registration, approval workflows, access verification, and visitor lifecycle management within organizations.

This document serves as the primary engineering reference for product owners, developers, testers, architects, and stakeholders involved in the design, development, testing, deployment, and maintenance of the platform.

The SRS establishes a common understanding of system behaviour, business rules, interfaces, constraints, and acceptance criteria to ensure consistent implementation across all project components.

## 1.2 Scope

ViziCheck provides a centralized platform for managing visitor access through structured workflows and secure verification mechanisms.

The system supports:

• User Authentication and Authorization

\- Tenant Management

\- Visitor Registration and Management

\- Visit Request Processing

\- Approval Workflows

• Digital Pass Generation

• QR Code Verification

• Security Check-In and Check-Out Operations

\- Audit Logging

\- Notifications

• Reporting and Administration

The platform will be delivered through:

\- Web Application

\- Mobile Application

\- REST API Services

The initial release (V1.0) focuses on secure visitor lifecycle management and operational efficiency while maintaining scalability for future enhancements.

1.3 Definitions, Acronyms, and Abbreviations

<table><tr><td>Term</td><td>Description</td></tr><tr><td>SRS</td><td>Software Requirements Specification</td></tr><tr><td>PRD</td><td>Product Requirements Document</td></tr><tr><td>RD</td><td>Requirement Discovery Document</td></tr><tr><td>API</td><td>Application Programming Interface</td></tr><tr><td>JWT</td><td>JSON Web Token</td></tr><tr><td>RBAC</td><td>Role-Based Access Control</td></tr><tr><td>QR</td><td>Quick Response Code</td></tr><tr><td>UI</td><td>User Interface</td></tr><tr><td>UX</td><td>User Experience</td></tr><tr><td>CRUD</td><td>Create, Read, Update, Delete</td></tr><tr><td>Admin</td><td>Super Administrator</td></tr><tr><td>Tenant</td><td>Employee or host receiving visitors</td></tr><tr><td>Visitor</td><td>External person requesting access</td></tr><tr><td>Security Officer</td><td>Personnel responsible for access verification</td></tr></table>

## 1.4 References

The following documents serve as references for this SRS:

Product Documentation

\- Requirement Discovery Document (RD) v1.0

• Product Requirements Document (PRD) v1.0

## Technical References

\- FastAPI Documentation

\- MySQL Documentation

\- React Documentation

\- Flutter Documentation

\- JWT Authentication Standards

Internal Artifacts

• Architecture Document (Future)

• Database Design Document (Future)

• API Specification (Future)

## 1.5 Intended Audience

This document is intended for:

## Product Team

Responsible for validating business requirements and product scope.

## Backend Developers

Responsible for implementing APIs, business logic, authentication, database interactions, and integrations.

## Frontend Developers

Responsible for implementing web interfaces and user workflows.

## Mobile Developers

Responsible for implementing mobile experiences and QR-based visitor interactions.

## QA Engineers

Responsible for testing and validation against defined requirements.

## Project Stakeholders

Responsible for reviewing project progress and ensuring alignment with organizational goals.

## 1.6 Document Overview

This SRS is organized into the following sections:

<table><tr><td>Section</td><td>Description</td></tr><tr><td>Section 1</td><td>Introduction</td></tr><tr><td>Section 2</td><td>Overall Description</td></tr><tr><td>Section 3</td><td>Functional Requirements</td></tr><tr><td>Section 4</td><td>External Interface Requirements</td></tr><tr><td>Section 5</td><td>Non-Functional Requirements</td></tr><tr><td>Section 6</td><td>Data Requirements</td></tr><tr><td>Section 7</td><td>Acceptance Criteria</td></tr></table>

Each section progressively moves from business understanding to detailed engineering specifications.

## Section 2 – Overall Description

## 2.1 Product Perspective

ViziCheck is a standalone Visitor Access and Verification Platform developed to modernize and streamline visitor management processes within organizations.

The platform replaces manual visitor registers, fragmented approval processes, and unsecured visitor verification methods with a centralized digital solution.

ViziCheck operates as a modular monolithic application consisting of:

![](images/205e1d33ff74b3a7513e435a1a784dac90cfc9cf6065c021c22e8210234ae119.jpg)

The platform is designed to support future growth while maintaining simplicity for initial deployment.

2.2 Product Functions
The primary functions of ViziCh
Identity Management
    - User Authentication
    - Authorization
    - Session Management
Tenant Management
    - Tenant Profiles
    - Availability Scheduling
    - Host Management
Visitor Management
    - Visitor Registration
    - Visitor Profiles
    - Visitor History
Visit Request Processing
    - Request Creation
    - Request Tracking
    - Request Cancellation
Approval Workflow
    - Tenant Approval
    - Administrative Approval
    - Request Rejection
Pass Management
    - Visitor Pass Generation
    - Pass Validation
    - Pass Revocation
QR Verification
    - QR Generation
    - QR Validation
    - Verification Tracking
Security Operations
    - Visitor Check-In
    - Visitor Check-Out
    - Presence Tracking
Audit & Reporting
    - Activity Logging
    - Approval Tracking
    - Operational Reporting

## 2.3 User Classes and Characteristics

## Super Admin

Responsibilities:

• System Governance

\- User Management

\- Reporting

\- Configuration Management

Technical Proficiency:

• Intermediate to Advanced

## Tenant

Responsibilities:

\- Manage Availability

\- Review Requests

\- Approve or Reject Visitors

Technical Proficiency:

\- Basic to Intermediate

## Visitor

Responsibilities:

\- Register

\- Request Visits

\- Present QR Pass

Technical Proficiency:

\- Basic

## Security Officer

Responsibilities:

\- Verify Visitors

\- Scan QR Codes

• Perform Check-In and Check-Out

Technical Proficiency:

\- Basic to Intermediate

## 2.4 Operating Environment

## Web Environment

\- Google Chrome

\- Microsoft Edge

\- Mozilla Firefox

## Mobile Environment

\- Android

\- iOS

## Backend Environment

\- FastAPI

\- Python 3.x

Database Environment

\- MySQL

## Development Environment

\- XAMPP

\- VS Code

\- GitHub

## 2.5 Design and Implementation Constraints

The following constraints apply to ViziCheck Version 1.0:

## Technology Constraints

\- Backend must use FastAPI.

\- Database must use MySQL.

• Mobile application must use Flutter.

• Authentication must use JWT.

## Business Constraints

\- Tenant availability validation is mandatory.

\- Approval workflow must be completed before pass generation.

• Audit logging is mandatory for critical actions.

## Security Constraints

• Role-Based Access Control must be enforced.

• Unauthorized access must be prevented.

\- Sensitive data must be protected.

## 2.6 Assumptions and Dependencies

## Assumptions

\- Users possess valid credentials.

\- Organizations maintain tenant records.

\- Internet connectivity is available during operation.

• Security personnel have access to QR scanning devices.

## Dependencies

\- MySQL Database

\- Email Notification Service

• QR Generation Library

\- JWT Authentication Components

## Section 3 – Functional Requirements

## 3.1 Authentication & Identity Management

## FR-AUTH-001

Requirement Name

User Login

Description

The system shall allow registered users to authenticate using their credentials.

## Actors

\- Super Admin

\- Tenant

\- Visitor

• Security Officer

## Preconditions

\- User account exists.

\- User account is active.

## Inputs

<table><tr><td>Field</td><td>Type</td></tr><tr><td>Email</td><td>String</td></tr><tr><td>Password</td><td>String</td></tr></table>

## Processing

1. Validate credentials.

2. Verify account status.

3. Generate JWT token.

4. Create session record.

## Outputs

\- Authentication Success

\- JWT Token Issued

## Exceptions

\- Invalid Credentials

\- Inactive Account

## Business Rules

\- BR-015

\- BR-016

## FR-AUTH-002

## Requirement Name

User Logout

## Description

The system shall allow authenticated users to terminate active sessions.

## Actors

\- All Roles

## Preconditions

\- Valid session exists.

## Processing

1. Invalidate token.

2. Close active session.

## Outputs

\- Logout Success

## FR-AUTH-003

## Requirement Name

Role-Based Access Control

## Description

The system shall enforce permissions based on assigned user roles.

## Actors

\- System

## Processing

1. Identify user role.

2. Validate requested action.

3. Grant or deny access.

## Outputs

\- Authorized

\- Unauthorized

## Business Rules

\- BR-016

## FR-AUTH-004

## Requirement Name

Password Reset

## Description

The system shall allow users to reset forgotten passwords.

## Actors

\- All Roles

## Inputs

\- Registered Email

## Outputs

\- Reset Link Sent

## 3.2 Tenant Management

FR-TEN-001

Requirement Name

Create Tenant

Description

The system shall allow administrators to create tenant profiles.

Actors

\- Super Admin

## Inputs

<table><tr><td>Field</td><td>Type</td></tr><tr><td>Tenant Name</td><td>String</td></tr><tr><td>Department</td><td>String</td></tr><tr><td>Email</td><td>String</td></tr><tr><td>Phone Number</td><td>String</td></tr></table>

## Processing

1. Validate inputs.

2. Create tenant profile.

3. Create associated user account.

## Outputs

\- Tenant Created

## FR-TEN-002

Requirement Name

Update Tenant Profile

Description

The system shall allow tenants to maintain profile information.

Actors

\- Tenant

\- Super Admin

## Outputs

\- Profile Updated

## FR-TEN-003

Requirement Name

Manage Availability Schedule

## Description

The system shall allow tenants to define available and unavailable periods.

Actors

\- Tenant

## Inputs

<table><tr><td>Field</td><td>Type</td></tr><tr><td>Date</td><td>Date</td></tr><tr><td>Start Time</td><td>Time</td></tr><tr><td>End Time</td><td>Time</td></tr><tr><td>Status</td><td>Enum</td></tr></table>

## Status Values

Available

Busy

Absent

## Processing

1. Validate schedule.

2. Store availability.

## Outputs

• Availability Updated

## Business Rules

\- BR-001

\- BR-002

\- BR-003

## FR-TEN-004

## Requirement Name

View Assigned Visitor Requests

Description

The system shall allow tenants to review requests associated with them.

Actors

\- Tenant

Outputs

\- Request List

## 3.3 Visitor Management

FR-VIS-001

Requirement Name

Register Visitor

Description

The system shall allow visitors to create accounts.

Actors

\- Visitor

Inputs

<table><tr><td>Field</td><td>Type</td></tr><tr><td>Full Name</td><td>String</td></tr><tr><td>Email</td><td>String</td></tr><tr><td>Phone Number</td><td>String</td></tr><tr><td>Password</td><td>String</td></tr></table>

## Processing

1. Validate inputs.

2. Create visitor account.

3. Create visitor profile.

Outputs

\- Registration Successful

## FR-VIS-002

## Requirement Name

Update Visitor Profile

## Description

The system shall allow visitors to maintain personal information.

## Actors

\- Visitor

## Outputs

• Profile Updated

## FR-VIS-003

## Requirement Name

View Visitor History

## Description

The system shall provide visitors with historical visit records.

Actors

\- Visitor

## Outputs

\- Visit History

## FR-VIS-004

Requirement Name

Search Visitor Records

Description

The system shall allow authorized users to search visitor information.

Actors

\- Super Admin

\- Tenant

## Search Criteria

Visitor Name

Email

Phone Number

Visit Date

## Outputs

\- Matching Visitor Records

## FR-VIS-005

## Requirement Name

View Visitor Details

Description

The system shall allow authorized users to access visitor information.

## Actors

\- Super Admin

\- Tenant

• Security Officer

## Outputs

\- Visitor Profile Information

## Traceability

## Authentication Module

FR-AUTH-001

## FR-AUTH-002

## FR-AUTH-003

FR-AUTH-004

## Tenant Module

FR-TEN-001

FR-TEN-002

FR-TEN-003

FR-TEN-004

<table><tr><td>Visitor Module</td></tr><tr><td>FR-VIS-001</td></tr><tr><td>FR-VIS-002</td></tr><tr><td>FR-VIS-003</td></tr><tr><td>FR-VIS-004</td></tr><tr><td>FR-VIS-005</td></tr></table>

## 3.4 Visit Request Management

FR-REQ-001

## Requirement Name

Create Visit Request

Description

The system shall allow visitors to create visit requests for a specific tenant.

Actors

\- Visitor

Preconditions

\- Visitor authenticated.

\- Tenant exists.

Inputs

<table><tr><td>Field</td><td>Type</td></tr><tr><td>Tenant ID</td><td>UUID</td></tr><tr><td>Visit Date</td><td>Date</td></tr><tr><td>Start Time</td><td>Time</td></tr><tr><td>End Time</td><td>Time</td></tr><tr><td>Purpose</td><td>Text</td></tr></table>

## Processing

1. Validate visitor account.

2. Validate tenant existence.

3. Validate requested date and time.

4. Validate tenant availability.

5. Create visit request.

## Outputs

\- Visit Request Created

## Exceptions

\- Tenant Not Found

\- Invalid Date

\- Tenant Unavailable

## Business Rules

\- BR-001

\- BR-002

\- BR-003

## FR-REQ-002

## Requirement Name

Update Visit Request

## Description

The system shall allow modification of requests before approval.

## Actors

\- Visitor

## Preconditions

\- Request status is Submitted or Pending.

## Outputs

\- Request Updated

## FR-REQ-003

Requirement Name

Cancel Visit Request

Description

The system shall allow visitors to cancel pending requests.

## Actors

\- Visitor

## Outputs

\- Request Cancelled

## FR-REQ-004

## Requirement Name

Track Request Status

## Description

The system shall allow users to monitor request progress.

## Actors

\- Visitor

\- Tenant

\- Super Admin

## Status Values

Draft

Submitted

Pending Tenant Approval

Pending Admin Approval

Approved

Rejected

Cancelled

Completed

## Outputs

\- Current Status

## FR-REQ-005

## Requirement Name

View Request History

## Description

The system shall maintain historical visit request records.

Actors

\- Visitor

\- Tenant

\- Super Admin

## Outputs

\- Request History

## 3.5 Approval Workflow

FR-APP-001

Requirement Name

Review Visit Request

Description

The system shall allow tenants to review pending requests.

Actors

\- Tenant

## Outputs

\- Request Details

## FR-APP-002

Requirement Name

Approve Visit Request

Description

The system shall allow tenants to approve requests.

Actors

\- Tenant

## Preconditions

\- Tenant available.

\- Request valid.

## Processing

1. Validate availability.

2. Record approval.

3. Update request status.

## Outputs

\- Tenant Approval Recorded

## Business Rules

\- BR-001

\- BR-002

\- BR-003

## FR-APP-003

Requirement Name

Reject Visit Request

Description

The system shall allow tenants to reject requests.

## Actors

\- Tenant

## Inputs

<table><tr><td>Field</td><td>Type</td></tr><tr><td>Rejection Reason</td><td>Text</td></tr></table>

## Outputs

\- Request Rejected

## FR-APP-004

## Requirement Name

Administrative Approval

## Description

The system shall allow administrators to perform final authorization.

Actors

\- Super Admin

## Preconditions

\- Tenant approval completed.

Outputs

\- Request Approved

## Business Rules

\- BR-004

## FR-APP-005

## Requirement Name

View Approval History

Description

The system shall maintain approval records.

Actors

\- Super Admin

\- Tenant

## Outputs

\- Approval Timeline

## 3.6 Pass Management

FR-PASS-001

## Requirement Name

Generate Visitor Pass

## Description

The system shall generate a visitor pass after approval completion.

## Actors

\- System

\- Super Admin

## Preconditions

\- Tenant approved.

\- Admin approved.

## Processing

1. Generate Pass ID.

2. Create QR token.

3. Create pass record.

4. Set pass status Active.

## Outputs

\- Visitor Pass Generated

## Business Rules

\- BR-004

\- BR-005

\- BR-006

## FR-PASS-002

## Requirement Name

View Visitor Pass

## Description

The system shall allow authorized users to access pass details.

## Actors

\- Visitor

\- Tenant

\- Super Admin

\- Security Officer

## Outputs

\- Pass Information

## FR-PASS-003

## Requirement Name

Revoke Visitor Pass

## Description

The system shall allow administrators to invalidate a pass.

Actors

\- Super Admin

## Outputs

• Pass Revoked

## Business Rules

\- BR-008

## FR-PASS-004

## Requirement Name

Validate Pass Expiry

## Description

The system shall verify pass validity before access.

Actors

\- System

## Outputs

\- Valid

\- Expired

## Business Rules

\- BR-007

## FR-PASS-005

## Requirement Name

Maintain Pass Lifecycle

## Description

The system shall track pass status transitions.

Status Values
Generated
Active
Checked-In
Checked-Out
Expired
Revoked
Archived
Outputs
• Current Pass Status

## Traceability

Visit Request Module

FR-REQ-001

FR-REQ-002

FR-REQ-003

FR-REQ-004

FR-REQ-005

Approval Workflow

FR-APP-001

FR-APP-002

FR-APP-003

FR-APP-004

FR-APP-005

## Pass Management

FR-PASS-001

## FR-PASS-002

## FR-PASS-003

## FR-PASS-004

## FR-PASS-005

## 3.7 QR Verification

## FR-QR-001

## Requirement Name

Generate QR Token

## Description

The system shall generate a unique QR token for every approved visitor pass.

## Actors

\- System

## Preconditions

• Pass generated successfully.

## Processing

1. Generate unique token.

2. Associate token with pass.

3. Encode token into QR format.

## Outputs

\- QR Code Generated

## Business Rules

\- BR-005

\- BR-006

## FR-QR-002

Requirement Name

Scan QR Code

## Description

The system shall allow Security Officers to scan visitor QR codes.

## Actors

• Security Officer

## Inputs

\- QR Code

## Outputs

• Verification Request Submitted

## FR-QR-003

## Requirement Name

Validate QR Code

## Description

The system shall verify the authenticity and validity of a QR code.

## Actors

\- System

## Processing

1. Validate token.

2. Validate pass status.

3. Validate expiry.

4. Validate revocation status.

## Outputs

\- Valid

\- Invalid

## Business Rules

\- BR-007

\- BR-008

\- BR-009

## FR-QR-004

## Requirement Name

Record Verification Attempt

## Description

The system shall record every QR validation attempt.

## Actors

\- System

## Outputs

\- Verification Log Created

## Business Rules

\- BR-011

## 3.8 Security Operations

FR-SEC-001

## Requirement Name

Visitor Check-In

## Description

The system shall allow Security Officers to check in verified visitors.

## Actors

• Security Officer

## Preconditions

\- Valid QR code.

• Active pass.

## Processing

1. Verify QR.

2. Verify pass status.

3. Record entry timestamp.

4. Update presence status.

## Outputs

\- Visitor Checked-In

## FR-SEC-002

## Requirement Name

Visitor Check-Out

## Description

The system shall allow Security Officers to record visitor departure.

## Actors

\- Security Officer

## Preconditions

\- Visitor checked in.

## Processing

1. Locate active visit.

2. Record exit timestamp.

3. Update visit status.

## Outputs

\- Visitor Checked-Out

## Business Rules

\- BR-010

## FR-SEC-003

## Requirement Name

Presence Tracking

## Description

The system shall maintain real-time visitor presence status.

## Presence States

Not Arrived

Checked-In

Checked-Out

## Outputs

\- Current Presence Status

## FR-SEC-004

## Requirement Name

Active Visitor Monitoring

## Description

The system shall allow Security Officers to view all active visitors currently inside the facility.

## Actors

\- Security Officer

\- Super Admin

## Outputs

• Active Visitor List

## 3.9 Audit & Activity Logs

## FR-AUDIT-001

## Requirement Name

Create Audit Log Entry

## Description

The system shall create audit records for critical actions.

## Actors

\- System

## Tracked Actions

Login
Logout
Approval
Rejection
Pass Generation
Pass Revocation
QR Verification
Check-In
Check-Out
Settings Changes

## Outputs

\- Audit Record Created

## Business Rules

\- BR-012

\- BR-013

## FR-AUDIT-002

## Requirement Name

View Audit Logs

## Description

The system shall allow administrators to review audit history.

## Actors

\- Super Admin

## Outputs

\- Audit Log List

## FR-AUDIT-003

## Requirement Name

Filter Audit Logs

## Description

The system shall support audit log filtering.

## Filters

Date Range

User

Action Type

Module

Outputs
- Filtered Results

## 3.10 Dashboard & Reporting

## FR-REP-001

## Requirement Name

Dashboard Overview

## Description

The system shall provide operational dashboards.

## Actors

\- Super Admin

\- Tenant

• Security Officer

## Outputs

Total Visitors

Active Visitors

Pending Approvals

Today's Visits

## FR-REP-002

## Requirement Name

Visitor Statistics

## Description

The system shall provide visitor analytics.

## Outputs

Daily Visitors

Weekly Visitors

Monthly Visitors

## FR-REP-003

## Requirement Name

Approval Statistics

## Description

The system shall provide approval metrics.

## Outputs

Approved Requests
Rejected Requests
Pending Requests

## FR-REP-004

## Requirement Name

Export Reports

Description

The system shall support report export functionality.

Export Formats

PDF
Excel

Outputs

\- Generated Report

## 3.11 Notifications

## FR-NOTIF-001

## Requirement Name

Request Status Notification

## Description

The system shall notify users when request status changes.

## Actors

\- System

Triggers

Submitted

Approved

Rejected

Cancelled

## Outputs

\- Notification Sent

## FR-NOTIF-002

## Requirement Name

Pass Generation Notification

## Description

The system shall notify visitors when a pass is generated.

Actors

\- System

## Outputs

\- Notification Sent

## FR-NOTIF-003

Requirement Name

Approval Notification

Description

The system shall notify tenants about pending requests.

Actors

\- System

Outputs

\- Notification Sent

## 3.12 Settings & Administration

FR-ADMIN-001

Requirement Name

Manage Roles

Description

The system shall allow administrators to manage role assignments.

Actors

\- Super Admin

Outputs

\- Roles Updated

## FR-ADMIN-002

## Requirement Name

Manage Permissions

## Description

The system shall allow administrators to manage permissions.

Actors

\- Super Admin

## Outputs

\- Permissions Updated

## FR-ADMIN-003

Requirement Name

Manage System Settings

Description

The system shall allow administrators to configure platform settings.

Actors

\- Super Admin

## Outputs

\- Settings Updated

## FR-ADMIN-004

## Requirement Name

User Account Administration

## Description

The system shall allow administrators to activate, deactivate, and manage user accounts.

Actors

\- Super Admin

Outputs

\- User Status Updated

Functional Requirements Summary

<table><tr><td>AUTH</td><td>4 Requirements</td></tr><tr><td>TEN</td><td>4 Requirements</td></tr><tr><td>VIS</td><td>5 Requirements</td></tr><tr><td>REQ</td><td>5 Requirements</td></tr><tr><td>APP</td><td>5 Requirements</td></tr><tr><td>PASS</td><td>5 Requirements</td></tr><tr><td>QR</td><td>4 Requirements</td></tr><tr><td>SEC</td><td>4 Requirements</td></tr><tr><td>AUDIT</td><td>3 Requirements</td></tr><tr><td>REP</td><td>4 Requirements</td></tr><tr><td>NOTIF</td><td>3 Requirements</td></tr><tr><td>ADMIN</td><td>4 Requirements</td></tr><tr><td colspan="2">Total Functional Requirements</td></tr><tr><td colspan="2">50 Functional Requirements</td></tr></table>

## Section 4 – External Interface Requirements

## 4.1 User Interfaces

## 4.1.1 Super Admin Portal

Purpose

System administration and governance.

Features

\- Dashboard

\- Tenant Management

\- Visitor Management

\- Approval Monitoring

\- Audit Logs

\- Reports

\- Settings

## Access

\- Super Admin Only

## 4.1.2 Tenant Portal

## Purpose

Host management and visitor approvals.

## Features

\- Dashboard

\- Availability Calendar

\- Pending Requests

\- Approval History

\- Notifications

Access

\- Tenant Only

## 4.1.3 Security Portal

## Purpose

Visitor verification and access control.

## Features

\- QR Scanner

• Active Visitors

\- Check-In

\- Check-Out

\- Visitor Search

## Access

• Security Officer Only

## 4.1.4 Visitor Mobile Application

## Purpose

Visitor self-service operations.

## Features

\- Registration

\- Login

\- Create Request

\- Track Request Status

• View QR Pass

\- Notifications

Access

\- Visitor Only

## 4.2 API Interfaces

The platform shall expose REST APIs.

## API Standards

JSON Request/Response

HTTPS

JWT Authentication

RESTful Design

## Response Format

```snap
Success:
{
    "success": true,
    "message": "Operation successful",
    "data": {}
}
Error:
{
    "success": false,
    "message": "Validation failed",
    "errors": []
}
```

## 4.3 Database Interfaces

Database

MySQL

ORM

SQLAlchemy

Database Access Layer

![](images/41b391310cec9e7c56346d6c7e6500493f5c6bcbcbe4bcaaa9020aed26d93b7f.jpg)

## 4.4 Communication Interfaces

Email Service

Used for:

• Approval Notifications

\- Request Updates

• Pass Generation Notifications

QR Service

Used for:

\- QR Generation

\- QR Validation

## Section 5 – Non-Functional Requirements

## 5.1 Security Requirements

## NFR-SEC-001

JWT authentication shall be required for protected resources.

## NFR-SEC-002

Passwords shall be securely hashed.

## NFR-SEC-003

RBAC shall be enforced at the backend layer.

## NFR-SEC-004

All API inputs shall be validated.

## NFR-SEC-005

Critical actions shall generate audit records.

## 5.2 Performance Requirements

## NFR-PERF-001

Average API response time shall remain below 2 seconds.

## NFR-PERF-002

QR verification shall complete within 1 second.

## NFR-PERF-003

Dashboard loading time shall remain below 3 seconds.

## 5.3 Reliability Requirements

## NFR-REL-001

System availability shall exceed 99%.

## NFR-REL-002

Database transactions shall maintain consistency.

## NFR-REL-003

Unexpected failures shall be logged.

## 5.4 Scalability Requirements

## NFR-SCAL-001

Architecture shall support future module expansion.

## NFR-SCAL-002

Database design shall support growth without redesign.

## NFR-SCAL-003

API design shall support future mobile and third-party integrations.

## 5.5 Maintainability Requirements

## NFR-MAIN-001

System shall follow layered architecture.

NFR-MAIN-002

Code shall follow established naming standards.

## NFR-MAIN-003

API documentation shall be maintained.

## Section 6 – Data Requirements

## 6.1 Core Entities

## User

Stores authentication information.

## Role

Stores access permissions.

## Tenant

Stores host information.

## Visitor

Stores visitor information.

Availability

Stores tenant schedules.

Visit Request

Stores visit requests.

## Approval

Stores approval records.

## Pass

Stores visitor passes.

## QR Token

Stores QR verification tokens.

Check-In

Stores entry records.

Stores activity records.

## Notification

Stores notification history.

## 6.2 Entity Relationships

User
Role

Tenant
└ Availability

Visitor
← Visit Request

Visit Request
Approval
Approval
Pass

Pass
└─QR Token

Pass
└─ Check-In

All Modules
Audit Log

## 6.3 Data Retention Requirements

Audit Logs

Minimum retention:

1 Year

Visit Records

Minimum retention:

3 Years

Notifications

Minimum retention:

90 Days

## Section 7 – Acceptance Criteria

AC-AUTH-001

Scenario

User Login

Given

Valid credentials exist.

When

User submits login request.

Then

JWT token shall be issued.

## AC-REQ-001

Scenario

Create Visit Request

Given

Authenticated visitor.

When

Visitor submits request.

## Then

Request shall be created successfully.

## AC-APP-001

## Scenario

Approve Request

Given

Valid pending request.

When

Tenant approves.

Then

Request status shall update.

## AC-PASS-001

## Scenario

Generate Pass

## Given

Tenant approval and admin approval completed.

When

Pass generation executes.

Then

Unique pass and QR code shall be generated.

## AC-QR-001

Scenario

Validate QR

Given

Valid active pass.

When

Security Officer scans QR.

## Then

System shall validate successfully.

## AC-SEC-001

## Scenario

Check-In Visitor

## Given

Valid QR pass.

When

Check-in performed.

## Then

Presence status becomes Checked-In.

## AC-SEC-002

## Scenario

Check-Out Visitor

Given

Checked-In visitor.

## When

Check-out performed.

## Then

Presence status becomes Checked-Out.

In the SRS, the modules can be divided like this:

## Backend Modules

These are the core FastAPI + MySQL modules:

AUTH - Authentication & JWT

TEN - Tenant Management

VIS - Visitor Management

REQ - Visit Request Management

APP - Approval Workflow

PASS - Pass Management

QR - QR Token & Validation

SEC - Check-In / Check-Out

AUDIT - Audit Logs

REP - Reports API

NOTIF - Email Notifications

ADMIN - Settings & Role Management

Backend should start first with:

1. AUTH

2. ADMIN / RBAC

3. TEN

4. VIS

5. REQ

6. APP

7. PASS

8. QR

9. SEC

10. AUDIT

## Frontend Modules

These are the React web modules:
Login Page
Admin Dashboard
Tenant Dashboard
Security Dashboard
Tenant Management UI
Visitor Management UI
Visit Request UI
Approval UI
Pass Management UI
QR Verification UI
Check-In / Check-Out UI
Audit Logs UI
Reports UI
Settings UI

Frontend should start first with:

1. Login UI  
2. Layout / Sidebar / Navbar  
3. Admin Dashboard  
4. Tenant Management UI  
5. Visitor Management UI  
6. Visit Request UI  
7. Approval UI  
8. Security Dashboard

## Mobile Modules

These are the Flutter modules:
Visitor Login / Register
Visitor Dashboard
Create Visit Request
Request Status Tracking
View QR Pass
Visitor Profile
Tenant Mobile Login
Tenant Request Approval
Tenant Availability
Notifications

## Mobile should start first with:

1. Login / Register

2. Visitor Dashboard

3. Create Visit Request

4. Request Status

5. QR Pass Screen

6. Tenant Approval Screen

## Best Parallel Starting Plan

Backend starts:

AUTH + RBAC + Database setup

Frontend starts:

Login + Layout + Dashboard shell

Mobile starts:

Login/Register + Visitor dashboard shell
