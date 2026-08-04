import re
from typing import Optional
from app.core.exceptions import ValidationException

class SecurityValidator:
    """
    Validator for password strength and security parameters.
    """

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Enforce enterprise password policy:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        errors = []
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
            errors.append("Password must contain at least one special character")

        if errors:
            raise ValidationException(
                message="Password does not meet security requirements",
                errors=errors
            )
