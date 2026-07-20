# backend/error-handling.md

# Error Handling Standards

## Standard Error Response

{
"success": false,
"message": "Validation failed",
"errors": []
}

---

## Error Types

Validation Error

HTTP 422

Example:

Missing email

---

Authentication Error

HTTP 401

Example:

Invalid credentials

---

Authorization Error

HTTP 403

Example:

Permission denied

---

Not Found Error

HTTP 404

Example:

Visitor not found

---

Conflict Error

HTTP 409

Example:

Email already exists

---

Internal Error

HTTP 500

Example:

Unexpected server error

---

## Custom Exceptions

ValidationException

AuthorizationException

NotFoundException

ConflictException

BusinessRuleException
