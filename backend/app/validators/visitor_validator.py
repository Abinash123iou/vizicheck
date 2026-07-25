import re
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.visitor import Visitor, VisitorStatus
from app.core.exceptions import ValidationException, AuthorizationException
from app.core.permissions import SystemRoles

class VisitorValidator:
    """
    Validation service providing strict business logic checks, duplicate prevention across phone/email/gov_id,
    tenant boundary enforcement, and state transition safety for Visitor management.
    """

    PHONE_REGEX = re.compile(r"^\+?[\d\s\-\(\)]{5,20}$")
    EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """
        Validate phone number format.
        """
        if not phone or not phone.strip():
            raise ValidationException("Phone number is required")
        cleaned_phone = phone.strip()
        if not cls.PHONE_REGEX.match(cleaned_phone):
            raise ValidationException("Invalid phone number format")
        return cleaned_phone

    @classmethod
    def validate_email(cls, email: Optional[str]) -> Optional[str]:
        """
        Validate email address format if provided.
        """
        if not email:
            return None
        cleaned_email = email.strip().lower()
        if not cls.EMAIL_REGEX.match(cleaned_email):
            raise ValidationException("Invalid email address format")
        return cleaned_email

    @classmethod
    def validate_duplicate_visitor(
        cls,
        db: Session,
        tenant_id: int,
        phone: str,
        email: Optional[str] = None,
        government_id_number: Optional[str] = None,
        exclude_visitor_id: Optional[int] = None
    ) -> None:
        """
        Triple duplicate validation: Ensure phone, email, and government_id_number are unique within tenant.
        """
        # Check phone uniqueness within tenant
        phone_query = db.query(Visitor).filter(
            Visitor.tenant_id == tenant_id,
            Visitor.phone == phone.strip(),
            Visitor.is_deleted.is_(False)
        )
        if exclude_visitor_id:
            phone_query = phone_query.filter(Visitor.id != exclude_visitor_id)
        if phone_query.first():
            raise ValidationException(f"A visitor with phone number '{phone}' already exists in this tenant organization")

        # Check email uniqueness within tenant
        if email and email.strip():
            email_query = db.query(Visitor).filter(
                Visitor.tenant_id == tenant_id,
                Visitor.email.ilike(email.strip()),
                Visitor.is_deleted.is_(False)
            )
            if exclude_visitor_id:
                email_query = email_query.filter(Visitor.id != exclude_visitor_id)
            if email_query.first():
                raise ValidationException(f"A visitor with email address '{email}' already exists in this tenant organization")

        # Check Government ID uniqueness within tenant
        if government_id_number and government_id_number.strip():
            gov_query = db.query(Visitor).filter(
                Visitor.tenant_id == tenant_id,
                Visitor.government_id_number == government_id_number.strip(),
                Visitor.is_deleted.is_(False)
            )
            if exclude_visitor_id:
                gov_query = gov_query.filter(Visitor.id != exclude_visitor_id)
            if gov_query.first():
                raise ValidationException(f"A visitor with Government ID number '{government_id_number}' already exists in this tenant organization")

    @classmethod
    def validate_tenant_boundary(
        cls, 
        current_user: User, 
        target_tenant_id: Optional[int], 
        db: Optional[Session] = None
    ) -> Optional[int]:
        """
        Enforce tenant isolation. Non-Super Admins are locked to their assigned tenant_id.
        Super Admins return specified target_tenant_id, caller tenant_id, or first DB tenant fallback.
        Verifies target_tenant_id exists in database if provided.
        """
        from app.models.tenant import Tenant

        resolved_tenant_id: Optional[int] = None

        if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN:
            if target_tenant_id is not None:
                resolved_tenant_id = target_tenant_id
            elif current_user.tenant_id:
                resolved_tenant_id = current_user.tenant_id
            elif db:
                first_tenant = db.query(Tenant).filter_by(is_deleted=False).first()
                if first_tenant:
                    resolved_tenant_id = first_tenant.id
        else:
            if not current_user.tenant_id:
                raise AuthorizationException("Current user is not associated with any tenant organization")

            if target_tenant_id is not None and target_tenant_id != current_user.tenant_id:
                raise AuthorizationException("Forbidden. Access restricted to caller's tenant organization")

            resolved_tenant_id = current_user.tenant_id

        if resolved_tenant_id is not None:
            if resolved_tenant_id <= 0:
                raise ValidationException(f"Invalid tenant_id '{resolved_tenant_id}'. Tenant ID must be a positive integer (e.g., 1, 2, 3)")
            if db:
                tenant_exists = db.query(Tenant).filter(Tenant.id == resolved_tenant_id, Tenant.is_deleted.is_(False)).first()
                if not tenant_exists:
                    raise ValidationException(f"Tenant organization with ID '{resolved_tenant_id}' does not exist")

        return resolved_tenant_id



    @classmethod
    def validate_visitor_access(cls, current_user: User, visitor: Visitor) -> None:
        """
        Ensure calling user has authorization to view or mutate the target visitor entity.
        """
        if current_user.role and current_user.role.name == SystemRoles.SUPER_ADMIN:
            return

        if visitor.tenant_id != current_user.tenant_id:
            raise AuthorizationException("Forbidden. Visitor belongs to another tenant organization")

    @classmethod
    def validate_blacklist_rules(cls, visitor: Visitor, action_description: str = "perform operation on") -> None:
        """
        Check that blacklisted visitors cannot undergo certain actions without removing blacklist status first.
        """
        if visitor.blacklisted:
            raise ValidationException(
                f"Cannot {action_description} visitor '{visitor.first_name} {visitor.last_name}' because they are blacklisted. Reason: {visitor.blacklist_reason or 'No reason recorded'}"
            )

    @classmethod
    def validate_emergency_contact(
        cls, 
        contact_name: Optional[str], 
        contact_phone: Optional[str]
    ) -> None:
        """
        Validate emergency contact phone format if specified.
        """
        if contact_phone and contact_phone.strip():
            if not cls.PHONE_REGEX.match(contact_phone.strip()):
                raise ValidationException("Invalid emergency contact phone number format")

    @classmethod
    def validate_date_of_birth(cls, dob: Optional[date]) -> None:
        """
        Ensure date of birth is in the past.
        """
        if dob:
            if dob >= date.today():
                raise ValidationException("Date of birth must be a past date")
