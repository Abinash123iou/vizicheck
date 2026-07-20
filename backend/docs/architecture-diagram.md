# architecture/architecture-diagram.md

# ViziCheck Architecture Diagrams

## System Overview

```mermaid
flowchart TB

Visitor[Visitor Mobile App]
Admin[Admin Portal]
Security[Security Officer]

Visitor --> API
Admin --> API
Security --> API

API[FastAPI Backend]

API --> AUTH[Authentication Module]
API --> USER[User Module]
API --> TENANT[Tenant Module]
API --> REQUEST[Visit Request Module]
API --> APPROVAL[Approval Module]
API --> PASS[Pass Module]
API --> QR[QR Module]
API --> NOTIFICATION[Notification Module]
API --> AUDIT[Audit Module]

AUTH --> DB[(MySQL Database)]
USER --> DB
TENANT --> DB
REQUEST --> DB
APPROVAL --> DB
PASS --> DB
QR --> DB
NOTIFICATION --> DB
AUDIT --> DB
```

---

## Backend Architecture

```mermaid
flowchart TD

A[API Routes]

A --> B[Service Layer]

B --> C[Repository Layer]

C --> D[SQLAlchemy ORM]

D --> E[(MySQL Database)]
```

---

## Deployment Architecture

```mermaid
flowchart TB

Users
   ↓
Flutter Mobile App

React Admin Portal
      ↓
Nginx Reverse Proxy
      ↓
FastAPI Application
      ↓
MySQL Database
      ↓
Backup Storage
```

---

## Security Architecture

```mermaid
flowchart LR

Login
  ↓
JWT Authentication
  ↓
RBAC Authorization
  ↓
Protected APIs
  ↓
Audit Logging
```

---

## Notification Architecture

```mermaid
flowchart TD

Business Event
     ↓
Notification Service
     ↓
Database Notification
     ↓
User Notification
```
