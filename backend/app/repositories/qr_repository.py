from typing import Optional
from sqlalchemy.orm import Session
from app.models.qr_token import QRToken


class QRRepository:
    """
    Database access layer for QRToken entity operations.
    """

    @staticmethod
    def find_active_by_pass_id(db: Session, pass_id: int) -> Optional[QRToken]:
        """
        Find the currently active QRToken for a visitor pass.
        """
        return db.query(QRToken).filter(
            QRToken.pass_id == pass_id,
            QRToken.is_active.is_(True)
        ).first()

    @staticmethod
    def deactivate_tokens_for_pass(db: Session, pass_id: int) -> int:
        """
        Deactivate all active QR tokens linked to a pass (e.g. upon QR regeneration or revocation).
        """
        updated_count = db.query(QRToken).filter(
            QRToken.pass_id == pass_id,
            QRToken.is_active.is_(True)
        ).update({"is_active": False}, synchronize_session=False)
        db.commit()
        return updated_count

    @staticmethod
    def create(db: Session, qr_entity: QRToken) -> QRToken:
        """
        Persist a new QRToken entity.
        """
        db.add(qr_entity)
        db.commit()
        db.refresh(qr_entity)
        return qr_entity

    @staticmethod
    def update(db: Session, qr_entity: QRToken) -> QRToken:
        """
        Save changes to an existing QRToken entity.
        """
        db.commit()
        db.refresh(qr_entity)
        return qr_entity
