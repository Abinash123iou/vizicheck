from typing import List, Optional
from app.models.notification import Notification, NotificationTemplate, NotificationPreference
from app.schemas.notification import (
    NotificationResponse, NotificationTemplateResponse, NotificationPreferenceResponse
)


class NotificationMapper:
    """
    Mapper layer converting Notification domain entity models into Pydantic DTO responses.
    """

    @classmethod
    def to_notification_response(cls, entity: Notification) -> NotificationResponse:
        """Map Notification model to NotificationResponse DTO."""
        return NotificationResponse.model_validate(entity)

    @classmethod
    def to_notification_response_list(cls, entities: List[Notification]) -> List[NotificationResponse]:
        """Map list of Notification models to list of NotificationResponse DTOs."""
        return [cls.to_notification_response(item) for item in entities]

    @classmethod
    def to_template_response(cls, entity: NotificationTemplate) -> NotificationTemplateResponse:
        """Map NotificationTemplate model to NotificationTemplateResponse DTO."""
        return NotificationTemplateResponse.model_validate(entity)

    @classmethod
    def to_template_response_list(cls, entities: List[NotificationTemplate]) -> List[NotificationTemplateResponse]:
        """Map list of NotificationTemplate models to list of NotificationTemplateResponse DTOs."""
        return [cls.to_template_response(item) for item in entities]

    @classmethod
    def to_preference_response(cls, entity: NotificationPreference) -> NotificationPreferenceResponse:
        """Map NotificationPreference model to NotificationPreferenceResponse DTO."""
        return NotificationPreferenceResponse.model_validate(entity)
