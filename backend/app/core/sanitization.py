"""Input sanitization utilities to prevent XSS and injection attacks.

Provides:
- HTML entity encoding for user inputs
- String length validation
- Pattern-based validation for common fields
"""
import re
import html
from typing import Optional


# Patterns for common validations
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?[\d\s\-()]{7,20}$')
SAFE_STRING_PATTERN = re.compile(r'^[\w\s\-.,!?()[\]{}:;\'"@#$%^&*+=/\\|~`<>"]*$')

# Maximum field lengths to prevent DoS
MAX_STRING_LENGTH = 1000
MAX_TEXT_LENGTH = 10000
MAX_NAME_LENGTH = 255


def sanitize_string(value: Optional[str], max_length: int = MAX_STRING_LENGTH) -> Optional[str]:
    """Sanitize a string input: strip, truncate, and HTML-encode."""
    if value is None:
        return None
    # Strip whitespace
    value = value.strip()
    # Truncate
    value = value[:max_length]
    # HTML-encode to prevent XSS
    value = html.escape(value)
    return value


def sanitize_text(value: Optional[str], max_length: int = MAX_TEXT_LENGTH) -> Optional[str]:
    """Sanitize a text field (longer, preserves newlines)."""
    if value is None:
        return None
    value = value.strip()
    value = value[:max_length]
    value = html.escape(value)
    return value


def sanitize_name(value: str) -> str:
    """Sanitize a name field."""
    if not value:
        raise ValueError("Name cannot be empty")
    value = value.strip()[:MAX_NAME_LENGTH]
    value = html.escape(value)
    return value


def sanitize_email(value: Optional[str]) -> Optional[str]:
    """Validate and sanitize an email address."""
    if not value:
        return None
    value = value.strip().lower()
    if not EMAIL_PATTERN.match(value):
        raise ValueError("Invalid email format")
    return html.escape(value)


def sanitize_phone(value: Optional[str]) -> Optional[str]:
    """Validate and sanitize a phone number."""
    if not value:
        return None
    value = value.strip()
    if not PHONE_PATTERN.match(value):
        raise ValueError("Invalid phone number format")
    return html.escape(value)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum security requirements.

    Policy: minimum 6 characters (simple).

    Returns:
        (is_valid, message)
    """
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    return True, "Password meets requirements"
