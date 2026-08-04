from typing import Any, List, Optional

class ViziCheckException(Exception):
    """
    Base exception class for all custom exceptions in ViziCheck.
    """
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        errors: Optional[List[Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []

class NotFoundException(ViziCheckException):
    """
    Exception raised when a requested resource is not found (HTTP 404).
    """
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=404, errors=errors)

class ValidationException(ViziCheckException):
    """
    Exception raised when schema or business validation fails (HTTP 422).
    """
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=422, errors=errors)

class AuthorizationException(ViziCheckException):
    """
    Exception raised when access to a resource is denied (HTTP 403).
    """
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=403, errors=errors)

class AuthenticationException(ViziCheckException):
    """
    Exception raised when authentication fails (HTTP 401).
    """
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=401, errors=errors)

class ConflictException(ViziCheckException):
    """
    Exception raised when there is a resource conflict (HTTP 409).
    """
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=409, errors=errors)

class BusinessRuleException(ViziCheckException):
    """
    Exception raised when a business rule is violated (HTTP 400).
    """
    def __init__(self, message: str, errors: Optional[List[Any]] = None):
        super().__init__(message, status_code=400, errors=errors)

class UserInactiveException(AuthenticationException):
    """
    Exception raised when a user account is inactive or disabled (HTTP 401).
    """
    def __init__(self, message: str = "User account is inactive or disabled", errors: Optional[List[Any]] = None):
        super().__init__(message, errors=errors)

class TenantInactiveException(AuthorizationException):
    """
    Exception raised when a tenant organization is inactive or suspended (HTTP 403).
    """
    def __init__(self, message: str = "Tenant organization is inactive or suspended", errors: Optional[List[Any]] = None):
        super().__init__(message, errors=errors)

class InvalidTokenException(AuthenticationException):
    """
    Exception raised when a JWT token signature or claim is invalid (HTTP 401).
    """
    def __init__(self, message: str = "Invalid or malformed authentication token", errors: Optional[List[Any]] = None):
        super().__init__(message, errors=errors)

class ExpiredTokenException(AuthenticationException):
    """
    Exception raised when a JWT token has expired (HTTP 401).
    """
    def __init__(self, message: str = "Authentication token has expired", errors: Optional[List[Any]] = None):
        super().__init__(message, errors=errors)

class AccountLockedException(AuthenticationException):
    """
    Exception raised when a user account is locked due to multiple failed login attempts (HTTP 401).
    """
    def __init__(self, message: str = "Account is temporarily locked due to multiple failed login attempts", errors: Optional[List[Any]] = None):
        super().__init__(message, errors=errors)


