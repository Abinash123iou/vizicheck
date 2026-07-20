## ViziCheck Architecture Document v1.0

## 1. Purpose

The Architecture Document defines the technical structure of the ViziCheck platform and serves as the blueprint for implementation.

It provides guidance for:

\- Backend Development

\- Frontend Development

\- Mobile Development

\- Database Design

\- API Design

\- Deployment

## 2. Architecture Style

Selected Architecture

Modular Monolithic Architecture

Why?

Suitable for Team Size

3 Developers

Easier Deployment

Single Backend

Single Database

Lower Complexity

No Microservices

No Service Discovery

No Distributed Transactions

## Future Ready

Modules can later be extracted into microservices if needed.

3. High-Level System Architecture  
flowchart LR

U[Visitor]
T[Tenant]
S[Security Officer]
A[Super Admin]

subgraph Client Applications
    WEB[React Web]
    MOBILE[Flutter Mobile]
end

subgraph Backend
    API[FastAPI Application]

    AUTH[Authentication]
    TEN[Tenant]
    VIS[Visitor]
    REQ[Visit Requests]
    APP[Approvals]
    PASS[Passes]
    QR[QR Verification]
    SEC[Security]
    AUDIT[Audit Logs]
    REPORT[Reports]
    NOTIF[Notifications]
    ADMIN[Administration]
end

DB[(MySQL)]

U --> WEB
T --> WEB
S --> WEB
A --> WEB

U --> MOBILE
T --> MOBILE
S --> MOBILE

WEB --> API
MOBILE --> API

API --> AUTH
API --> TEN
API --> VIS
API --> REQ
API --> APP
API --> PASS
API --> QR
API --> SEC
API --> AUDIT
API --> REPORT
API --> NOTIF
API --> ADMIN

AUTH --> DB
TEN --> DB
VIS --> DB
REQ --> DB
APP --> DB
PASS --> DB
QR --> DB
SEC --> DB
AUDIT --> DB
REPORT --> DB
NOTIF --> DB
ADMIN --> DB

4. Layered Architecture
Backend shall follow:

flowchart TD

P[Presentation Layer<br/>FastAPI Routes]

S[Service Layer<br/>Business Logic]

R[Repository Layer<br/>Database Access]

D[(MySQL)]

P --> S
S --> R
R --> D

## 5. Backend Module Architecture

AUTH – Authentication & Identity
TEN – Tenant Management
VIS – Visitor Management
REQ – Visit Request Management
APP – Approval Workflow
PASS – Pass Management
QR – QR Verification
SEC – Security Operations
AUDIT – Audit & Activity Logs
REP – Dashboard & Report
NOTIF - Notifications
ADMIN – Settings & Administration

## Module Dependencies

flowchart LR

AUTH --> TEN
AUTH --> VIS

TEN --> REQ
VIS --> REQ

REQ --> APP

APP --> PASS

PASS --> QR

QR --> SEC

SEC --> AUDIT

PASS --> NOTIF
APP --> NOTIF

AUDIT --> REP

ADMIN --> AUTH
ADMIN --> TEN
ADMIN --> REP

## 6. Authentication Architecture

Authentication Flow

sequenceDiagram

participant User
participant Frontend
participant Backend
participant JWT
participant Database

User->>Frontend: Login

Frontend->>Backend: Email + Password

Backend->>Database: Validate Credentials

Database-->>Backend: Success

Backend->>JWT: Generate Access Token

JWT-->>Backend: JWT Token

Backend-->>Frontend: Return Token

Frontend-->>User: Login Successful

User->>Backend: Authenticated Request

Backend->>JWT: Verify Token

JWT-->>Backend: Valid

Backend-->>Frontend: Protected Response

Authorization

RBAC

Roles:

Super Admin
Tenant
Visitor
Security Officer

## 7. Visitor Request Architecture

Request Lifecycle

flowchart LR

Visitor

Visitor --> CreateRequest

CreateRequest --> Pending

Pending --> TenantApproval

TenantApproval --> Approved

TenantApproval --> Rejected

Approved --> GeneratePass

GeneratePass --> QRPass

QRPass --> CheckIn

CheckIn --> CheckOut

Rejected --> End

Pass Generation Flow

flowchart TD

ApprovedRequest

ApprovedRequest --> GeneratePass

GeneratePass --> CreateQRCode

CreateQRCode --> SavePass

SavePass --> NotifyVisitor

NotifyVisitor --> PassReady

## 9. QR Verification Architecture

Verification Flow

flowchart TD

SecurityOfficer

SecurityOfficer --> ScanQR

ScanQR --> ValidateQR

ValidateQR --> Valid

ValidateQR --> Invalid

Valid --> CheckDatabase

CheckDatabase --> ActivePass

CheckDatabase --> Expired

ActivePass --> AllowEntry

Expired --> DenyEntry

Invalid --> DenyEntry


Check-In Flow  

flowchart LR

Visitor --> ScanQR

ScanQR --> VerifyPass

VerifyPass --> CheckIn

CheckIn --> AuditLog

Check-Out Flow  
 
 flowchart LR

InsideCampus

InsideCampus --> ScanQR

ScanQR --> CheckOut

CheckOut --> AuditLog

## 11. Audit Architecture

Every critical action creates an audit record.
Tracked Events:
Login
Logout
Approval
Rejection
Pass Generation
Pass Revocation
QR Validation
Check-In
Check-Out
Settings Update

## 12. Frontend Architecture

React Application

flowchart TD

App

App --> Login

App --> Dashboard

Dashboard --> Visitors

Dashboard --> Requests

Dashboard --> Approvals

Dashboard --> Passes

Dashboard --> Reports

Dashboard --> Settings

## Major Pages

Login
Admin Dashboard
Tenant Dashboard
Security Dashboard
Visitors
Requests
Approvals
Passes
Reports
Settings

## 13. Mobile Architecture

Flutter Application

flowchart TD

FlutterApp

FlutterApp --> Login

FlutterApp --> Register

FlutterApp --> Dashboard

Dashboard --> CreateRequest

Dashboard --> RequestStatus

Dashboard --> QRPass

Dashboard --> Notifications

Dashboard --> Profile

## 14. Deployment Architecture

## 15. Architecture Principles

## Scalability

Modules should remain loosely coupled.

## Maintainability

Clear folder structure and naming conventions.

## Architecture Diagram V1

The architecture diagram for vizicheck is provided through the following Google Drive link:

View Diagram
