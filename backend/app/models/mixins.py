from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class SoftDeleteMixin:
    """
    Mixin for soft-deletable models.
    Provides is_deleted and deleted_at columns with helper methods.
    """
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    def delete(self, deleted_at_time: Optional[datetime] = None) -> None:
        """Soft delete the model instance."""
        self.is_deleted = True
        self.deleted_at = deleted_at_time or datetime.now(timezone.utc).replace(tzinfo=None)

    def restore(self) -> None:
        """Restore a soft-deleted model instance."""
        self.is_deleted = False
        self.deleted_at = None
