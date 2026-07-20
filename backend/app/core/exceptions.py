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
