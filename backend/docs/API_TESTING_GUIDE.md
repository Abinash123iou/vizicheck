# ViziCheck API Testing Guide & Specification

Complete technical specification and Postman execution manual for testing **ViziCheck** (Multi-Tenant Visitor Management System).

---

## 1. Environment & Setup

### Prerequisites
1. **Backend Server**: Running at `http://127.0.0.1:8000`
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. **Database Seeding**: Run Python seed script prior to testing:
   ```powershell
   python scripts/seed_testing_data.py
   ```
3. **Import Files into Postman**:
   - `postman/ViziCheck.postman_collection.json`
   - `postman/ViziCheck.postman_environment.json`

---

## 2. API Endpoints Reference

### 🔑 Authentication Module

#### `POST /api/v1/auth/login`
- **Description**: Authenticate user and issue JWT access & refresh tokens.
- **Request Body**:
  ```json
  {
    "email": "admin@vizicheck.com",
    "password": "TestPassword123!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Login successful",
    "data": {
      "access_token": "eyJhbGciOiJIUzI1Ni...",
      "token_type": "bearer",
      "user": {
        "id": 1,
        "email": "admin@vizicheck.com",
        "role": { "name": "SUPER_ADMIN" }
      }
    }
  }
  ```

#### `GET /api/v1/auth/me`
- **Description**: Fetch profile of currently authenticated user.
- **Headers**: `Authorization: Bearer <access_token>`

---

### 🏢 Tenant Management Module

#### `POST /api/v1/tenants`
- **Description**: Register a new tenant organization (Super Admin only).
- **Request Body**:
  ```json
  {
    "name": "Infosys Technology Center",
    "slug": "infosys-tech-center",
    "code": "TEN-INFOSYS",
    "contact_person": "Narayana Murthy",
    "contact_email": "contact@infosys-tech.com",
    "contact_phone": "+918028520261",
    "description": "Infosys SEZ Campus, Electronic City, Bengaluru"
  }
  ```

#### `GET /api/v1/tenants`
- **Description**: Paginated list of tenants with search and filter.
- **Query Params**: `page=1&page_size=10&search=Capnis`

---

### 👥 Visitor Management Module

#### `POST /api/v1/visitors`
- **Description**: Register an external visitor.
- **Request Body**:
  ```json
  {
    "tenant_id": 373,
    "first_name": "Arjun",
    "last_name": "Kapoor",
    "email": "arjun.kapoor@techmah.com",
    "phone": "+919811223344",
    "company": "Tech Mahindra",
    "government_id_type": "PAN",
    "government_id_number": "ABCDE1234F"
  }
  ```

---

### 📋 Visit Request Module

#### `POST /api/v1/requests`
- **Description**: Submit a visit request.
- **Request Body**:
  ```json
  {
    "tenant_id": 373,
    "visitor_id": 1,
    "host_id": 1,
    "purpose": "Architecture Planning Meeting",
    "department": "Engineering",
    "scheduled_start_time": "2026-07-30T22:00:00Z",
    "scheduled_end_time": "2026-07-31T06:00:00Z"
  }
  ```

#### `PATCH /api/v1/requests/{id}/approve`
- **Description**: Approve pending visit request.

---

### 🎫 Visitor Pass Module

#### `POST /api/v1/passes/generate/{visit_request_id}`
- **Description**: Generate a visitor pass and cryptographically signed JWT QR token.

---

### 🚪 Gate Security & Check-In Module

#### `POST /api/v1/checkin/scan`
- **Description**: Execute QR entry check-in via 12-stage validation pipeline.
- **Request Body**:
  ```json
  {
    "qr_token": "VIZICHECK:PASS:<uuid>:V1:<jwt>",
    "device_meta": {
      "gate_device_id": "DEV-GATE-NORTH-01",
      "scanner_name": "North Gate Scanner",
      "gate_name": "North Gate"
    },
    "notes": "Verified visitor badge"
  }
  ```

#### `POST /api/v1/checkin/manual`
- **Description**: Manual check-in override for guard when QR is unavailable.

#### `POST /api/v1/checkout/scan`
- **Description**: Exit scan check-out with automatic attendance duration computation.

#### `GET /api/v1/checkins/live-dashboard`
- **Description**: Real-time campus occupancy metrics, peak occupancy, gate & department breakdown.

---

## 3. Standard Response & Error Envelopes

### Success Envelope (`200 OK` / `201 Created`)
```json
{
  "success": true,
  "message": "Operation executed successfully",
  "data": { ... },
  "errors": null
}
```

### Error Envelope (`400` / `401` / `403` / `404` / `409` / `422`)
```json
{
  "success": false,
  "message": "Validation failed / Access denied / Conflict detected",
  "data": null,
  "errors": [
    "Detailed error description"
  ]
}
```
