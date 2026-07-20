# BACKEND_AGENTS.md

# Backend Development Rules

## Stack

* FastAPI
* SQLAlchemy
* Alembic
* MySQL
* JWT
* RBAC

---

## Architecture

Routes
  ↓
Controllers
  ↓
Services
  ↓
Repositories
  ↓
Database

Never skip layers.

---

## Controllers

Controllers must:

* Receive requests
* Validate input
* Call services
* Return responses

Never place business logic inside controllers.

---

## Services

Services should:

* Implement business rules
* Coordinate repositories
* Handle transactions
* Throw meaningful exceptions

---

## Repository Layer

Repositories should:

* Perform database operations only
* Never contain business logic
* Use SQLAlchemy ORM
* Optimize queries

---

## API Standards

Use consistent responses:

Success

```json
{
  "success": true,
  "message": "...",
  "data": {}
}
```

Failure

```json
{
  "success": false,
  "message": "...",
  "errors": []
}
```

---

## Database Rules

* Use UUIDs/IDs consistently.
* Use foreign keys correctly.
* Prevent N+1 queries.
* Use pagination.
* Soft delete where applicable.

---

## Authentication

* JWT Authentication
* Role-Based Access Control
* Permission validation
* Token expiration

---

## Logging

Log:

* Authentication
* Visitor actions
* Approval actions
* Errors
* Audit events

Never log passwords or tokens.

---

## Performance

* Minimize database queries.
* Use eager loading where appropriate.
* Cache when beneficial.
* Avoid duplicate API calls.
