from enum import Enum


class NotificationType(str, Enum):
    """
    Categories of system notification events.
    """
    # Auth & System
    WELCOME_EMAIL = "WELCOME_EMAIL"
    PASSWORD_RESET = "PASSWORD_RESET"

    # Visit Requests
    VISIT_REQUEST_SUBMITTED = "VISIT_REQUEST_SUBMITTED"
    VISIT_REQUEST_APPROVED = "VISIT_REQUEST_APPROVED"
    VISIT_REQUEST_REJECTED = "VISIT_REQUEST_REJECTED"
    VISIT_REQUEST_CANCELLED = "VISIT_REQUEST_CANCELLED"

    # Approvals
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_APPROVED = "APPROVAL_APPROVED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    APPROVAL_ESCALATED = "APPROVAL_ESCALATED"
    APPROVAL_DELEGATED = "APPROVAL_DELEGATED"

    # Visitor Passes & QR
    PASS_GENERATED = "PASS_GENERATED"
    QR_GENERATED = "QR_GENERATED"
    PASS_REVOKED = "PASS_REVOKED"
    PASS_EXPIRED = "PASS_EXPIRED"

    # Gate & Security
    VISITOR_CHECKED_IN = "VISITOR_CHECKED_IN"
    VISITOR_CHECKED_OUT = "VISITOR_CHECKED_OUT"
    OVERSTAY_ALERT = "OVERSTAY_ALERT"
    SECURITY_ALERT = "SECURITY_ALERT"

    # Host Availability
    LEAVE_REMINDER = "LEAVE_REMINDER"
    SCHEDULE_UPDATED = "SCHEDULE_UPDATED"

    # Custom / General
    GENERAL_ANNOUNCEMENT = "GENERAL_ANNOUNCEMENT"


class NotificationChannel(str, Enum):
    """
    Supported delivery channels.
    """
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"


class NotificationStatus(str, Enum):
    """
    Lifecycle status of a notification record.
    """
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class NotificationPriority(str, Enum):
    """
    Notification urgency priority levels.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"
