# Sprint 1 – Day 11: Host Availability Management Module

## Overview

The **Host Availability Management System** in ViziCheck provides granular schedule definition, break management, holiday/leave exception tracking, and dynamic time-slot calculation for hosts across multi-tenant enterprise environments.

It ensures that visitors can only request or schedule visits when hosts are working, not on break, not on leave, and within set host visitor capacity bounds (`max_visitors`).

---

## Technical Architecture & Design Patterns

The module strictly follows Clean Architecture, Repository Pattern, Specification Pattern, and SOLID principles:

```
                  ┌─────────────────────────────────────┐
                  │    HTTP Client / Postman / Frontend │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │      FastAPI Router Layer           │
                  │   (/api/v1/availability)            │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │       Availability Service          │
                  │   (Business Logic & Slot Engine)    │
                  └──────┬──────────────────────┬───────┘
                         │                      │
                         ▼                      ▼
    ┌───────────────────────────┐        ┌───────────────────────────┐
    │   Availability Validator   │        │  Availability Repository  │
    │ (Tenant & Overlap Rules)  │        │ (SQLAlchemy ORM & Filters)│
    └───────────────────────────┘        └──────────────┬────────────┘
                                                        │
                                                        ▼
                                         ┌───────────────────────────┐
                                         │       MySQL Database      │
                                         │(host_availability &       │
                                         │ availability_exceptions)  │
                                         └───────────────────────────┘
```

---

## Implemented API Endpoints (9 Endpoints)

| # | HTTP Method | Route Path | Description | Required Permissions |
|---|-------------|------------|-------------|----------------------|
| 1 | `POST` | `/api/v1/availability` | Create working availability schedule | `AVAILABILITY_CREATE` |
| 2 | `GET` | `/api/v1/availability` | List working schedules with filters & pagination | `AVAILABILITY_READ` |
| 3 | `GET` | `/api/v1/availability/slots` | Calculate available booking slots for a host & date | `AVAILABILITY_READ` |
| 4 | `GET` | `/api/v1/availability/{id}` | Retrieve availability schedule by ID | `AVAILABILITY_READ` |
| 5 | `PUT` | `/api/v1/availability/{id}` | Update working availability schedule | `AVAILABILITY_UPDATE` |
| 6 | `DELETE` | `/api/v1/availability/{id}` | Soft delete working availability schedule | `AVAILABILITY_DELETE` |
| 7 | `POST` | `/api/v1/availability/exceptions` | Create holiday, leave, or maintenance exception | `AVAILABILITY_CREATE` |
| 8 | `GET` | `/api/v1/availability/exceptions` | List availability exceptions | `AVAILABILITY_READ` |
| 9 | `DELETE` | `/api/v1/availability/exceptions/{id}` | Soft delete an availability exception | `AVAILABILITY_DELETE` |

---

## Database Schemas

### 1. `host_availability` Table
Stores working schedules per host and weekday.

| Column | Type | Constraints / Details |
|--------|------|-----------------------|
| `id` | BigInteger | Primary Key, Auto-increment |
| `tenant_id` | BigInteger | Foreign Key (`tenants.id`), Indexed |
| `user_id` | BigInteger | Foreign Key (`users.id`), Host User |
| `weekday` | Enum | `MONDAY`, `TUESDAY`, `WEDNESDAY`, `THURSDAY`, `FRIDAY`, `SATURDAY`, `SUNDAY` |
| `start_time` | Time | Working shift start time |
| `end_time` | Time | Working shift end time |
| `break_start` | Time | Optional break/lunch start time |
| `break_end` | Time | Optional break/lunch end time |
| `max_visitors` | Integer | Max concurrent/slot visitor limit (Default: 5) |
| `is_available` | Boolean | Availability toggle (Default: `True`) |
| `effective_from` | Date | Optional schedule effective start date |
| `effective_until` | Date | Optional schedule effective expiry date |
| `recurrence_type`| Enum | `WEEKLY`, `CUSTOM`, `NONE` |
| `notes` | String(255) | Notes / remarks |
| `created_at` | DateTime | Timestamp |
| `updated_at` | DateTime | Timestamp |
| `is_deleted` | Boolean | Soft delete flag |
| `deleted_at` | DateTime | Soft delete timestamp |
| `created_by_id` | BigInteger | Audit creator reference |
| `updated_by_id` | BigInteger | Audit modifier reference |
| `deleted_by_id` | BigInteger | Audit remover reference |

### 2. `availability_exceptions` Table
Stores overrides for holidays, personal leaves, and emergency maintenance.

| Column | Type | Constraints / Details |
|--------|------|-----------------------|
| `id` | BigInteger | Primary Key, Auto-increment |
| `tenant_id` | BigInteger | Foreign Key (`tenants.id`), Indexed |
| `user_id` | BigInteger | Foreign Key (`users.id`), Nullable (Null = Tenant-wide holiday) |
| `title` | String(100) | Exception title (e.g. "Annual Offsite") |
| `exception_type`| Enum | `HOLIDAY`, `LEAVE`, `MAINTENANCE`, `OTHER` |
| `start_date` | Date | Exception start date |
| `end_date` | Date | Exception end date |
| `is_full_day` | Boolean | Full day flag |
| `start_time` | Time | Partial day start time |
| `end_time` | Time | Partial day end time |
| `notes` | String(255) | Notes |
| `is_deleted` | Boolean | Soft delete flag |
| `deleted_at` | DateTime | Soft delete timestamp |

---

## Validation Pipeline (6 Stages)

1. **Tenant Isolation Guard**: Validates that all requests operate within the user's tenant boundary (`current_user.tenant_id`).
2. **Host User Check**: Verifies that `user_id` exists in the database and belongs to the specified tenant.
3. **RBAC & Management Check**: Hosts can manage their own schedules; Tenant Admins / Receptionists can manage schedules for any host in their tenant.
4. **Time Bounds & Break Integrity**:
   - `start_time < end_time`
   - `start_time <= break_start < break_end <= end_time`
5. **Effective Date Boundaries**:
   - `effective_from <= effective_until`
6. **Overlap Detection Engine**: Rejects schedule creation/updates if an active overlapping schedule already exists for the same host, weekday, and date window.

---

## Dynamic Time-Slot Calculation Engine

The `GET /api/v1/availability/slots` endpoint calculates real-time available time slots:
1. Checks for tenant-wide or host-specific full-day holiday/leave exceptions on the target date.
2. Retrieves host's working schedule for the weekday.
3. Generates discrete time slots (e.g. 30-minute intervals).
4. Evaluates break timing overlaps and marks affected slots as unavailable (`reason: "Scheduled Lunch / Break"`).
5. Queries active visit requests for the host on that date.
6. Calculates `remaining_capacity = max_visitors - active_bookings` for each slot.
7. Returns complete availability status array for calendar integration.

---

## Verification & Testing

- Unit tests written in `tests/availability/test_availability.py` (7/7 tests passing).
- Comprehensive test coverage including schedule CRUD, overlap rejection, break validation, exception handling, and slot calculations.
- Integrated into `scripts/seed_testing_data.py` for Postman testing.
