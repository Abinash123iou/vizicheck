from datetime import datetime
from typing import Optional
from app.models.visitor_pass import VisitorPass, PassStatus
from app.models.qr_token import QRToken
from app.core.exceptions import ValidationException, AuthorizationException


class QRValidator:
    """
    Validator for QR Token verification during scanning, gate check-in, and regeneration.
    """

    @classmethod
    def validate_qr_token_active(cls, qr_token: Optional[QRToken]) -> None:
        """
        Verify QR Token is active and not expired.
        """
        if not qr_token:
            raise ValidationException("Invalid or missing QR Token")

        if not qr_token.is_active:
            raise ValidationException("QR Token has been deactivated or regenerated. Please use the latest QR code.")

        now = datetime.now()
        exp_naive = qr_token.expires_at.replace(tzinfo=None) if qr_token.expires_at.tzinfo else qr_token.expires_at
        if exp_naive < now:
            raise ValidationException("QR Token has expired")

    @classmethod
    def validate_token_version_match(cls, qr_token: QRToken, visitor_pass: VisitorPass) -> None:
        """
        Ensure QR Token version matches pass.latest_qr_version.
        Rejects old QR screenshots.
        """
        if qr_token.version != visitor_pass.latest_qr_version:
            raise ValidationException(
                f"QR Token version mismatch (Token Version: {qr_token.version}, Latest Version: {visitor_pass.latest_qr_version}). "
                "This QR code has been superseded by a regenerated token."
            )
