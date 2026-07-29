from jose import jwt, JWTError, ExpiredSignatureError
import base64
import io
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from config import settings
from app.models.visitor_pass import VisitorPass
from app.core.exceptions import ValidationException
from app.utils.logger import get_logger

logger = get_logger("qr_service")


class QRService:
    """
    Cryptographic JWT token generator and verifier for secure Visitor Pass QR codes.
    """

    TOKEN_TYPE = "VISITOR_PASS"
    ISSUER = "ViziCheck"
    AUDIENCE = "GateScanner"

    @classmethod
    def generate_jwt_qr_token(
        cls, 
        visitor_pass: VisitorPass, 
        version: int, 
        expires_at: datetime
    ) -> Tuple[str, Dict[str, Any], str]:
        """
        Generate a cryptographically signed JWT QR token and payload.
        Returns tuple of (jwt_string, decoded_claims, base64_qr_placeholder).
        """
        iat = int(datetime.now(timezone.utc).timestamp())
        exp = int(expires_at.replace(tzinfo=timezone.utc).timestamp()) if expires_at.tzinfo else int(expires_at.timestamp())

        claims = {
            "sub": visitor_pass.uuid,
            "tenant_id": visitor_pass.tenant_id,
            "visitor_id": visitor_pass.visitor_id,
            "visit_request_id": visitor_pass.visit_request_id,
            "version": version,
            "token_type": cls.TOKEN_TYPE,
            "iss": cls.ISSUER,
            "aud": cls.AUDIENCE,
            "iat": iat,
            "exp": exp
        }

        token = jwt.encode(
            claims,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

        # Base64 encoded payload representation for gate scanner rendering
        raw_qr_payload = f"VIZICHECK:PASS:{visitor_pass.uuid}:V{version}:{token}"
        qr_base64 = base64.b64encode(raw_qr_payload.encode("utf-8")).decode("utf-8")
        qr_data_uri = f"data:image/png;base64,{qr_base64}"

        return token, claims, qr_data_uri

    @classmethod
    def decode_and_verify_jwt(cls, token: str) -> Dict[str, Any]:
        """
        Decode and verify JWT QR token signature and standard claims.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                audience=cls.AUDIENCE,
                issuer=cls.ISSUER
            )
            if payload.get("token_type") != cls.TOKEN_TYPE:
                raise ValidationException("Invalid QR token type")
            return payload
        except ExpiredSignatureError:
            raise ValidationException("QR Token has expired")
        except JWTError as e:
            raise ValidationException(f"Invalid QR Token signature or format: {str(e)}")
