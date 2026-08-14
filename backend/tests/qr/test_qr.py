import pytest
from datetime import datetime, timedelta, timezone
from app.services.qr_service import QRService
from app.validators.qr_validator import QRValidator
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.qr_token import QRToken
from app.core.exceptions import ValidationException

def test_qr_service_generate_and_decode():
    """Verify cryptographically signed JWT QR generation and verification."""
    mock_pass = VisitorPass(
        id=101,
        uuid="pass-uuid-12345",
        tenant_id=1,
        visitor_id=10,
        visit_request_id=20,
        pass_code="PASS-12345",
        status=PassStatus.ACTIVE
    )
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    
    token, claims, qr_uri = QRService.generate_jwt_qr_token(
        visitor_pass=mock_pass,
        version=1,
        expires_at=expires_at
    )

    assert token is not None
    assert claims["sub"] == "pass-uuid-12345"
    assert claims["tenant_id"] == 1
    assert claims["version"] == 1
    assert claims["token_type"] == "VISITOR_PASS"
    assert qr_uri.startswith("data:image/png;base64,")

    # Verify decoding
    decoded = QRService.decode_and_verify_jwt(token)
    assert decoded["sub"] == "pass-uuid-12345"
    assert decoded["token_type"] == "VISITOR_PASS"

def test_qr_service_expired_token():
    """Verify QRService raises ValidationException for expired QR token."""
    mock_pass = VisitorPass(
        id=102,
        uuid="pass-uuid-expired",
        tenant_id=1,
        visitor_id=10,
        visit_request_id=20,
        pass_code="PASS-EXPIRED",
        status=PassStatus.ACTIVE
    )
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    
    token, _, _ = QRService.generate_jwt_qr_token(
        visitor_pass=mock_pass,
        version=1,
        expires_at=expired_at
    )

    with pytest.raises(ValidationException) as exc_info:
        QRService.decode_and_verify_jwt(token)
    assert "expired" in str(exc_info.value).lower()

def test_qr_service_invalid_signature():
    """Verify invalid token signature throws ValidationException."""
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.invalid_signature"
    with pytest.raises(ValidationException):
        QRService.decode_and_verify_jwt(invalid_token)

def test_qr_validator_active_and_version():
    """Verify QRValidator active state and version match logic."""
    mock_pass = VisitorPass(
        id=1,
        latest_qr_version=2,
        status=PassStatus.ACTIVE
    )
    
    # Active matching QR Token
    active_token = QRToken(
        id=1,
        pass_id=1,
        version=2,
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    QRValidator.validate_qr_token_active(active_token)
    QRValidator.validate_token_version_match(active_token, mock_pass)

    # Inactive QR Token
    inactive_token = QRToken(
        id=2,
        pass_id=1,
        version=1,
        is_active=False,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    with pytest.raises(ValidationException) as exc:
        QRValidator.validate_qr_token_active(inactive_token)
    assert "deactivated" in str(exc.value).lower() or "inactive" in str(exc.value).lower()

    # Version mismatch QR Token
    mismatched_token = QRToken(
        id=3,
        pass_id=1,
        version=1, # Version 1 vs Pass Version 2
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    with pytest.raises(ValidationException) as exc:
        QRValidator.validate_token_version_match(mismatched_token, mock_pass)
    assert "mismatch" in str(exc.value).lower()
