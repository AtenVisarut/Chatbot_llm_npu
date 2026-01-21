"""
Message Handler Module
Handles message processing and diagnosis workflow
"""

import logging
from typing import TYPE_CHECKING

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)

from app.config import get_settings
from app.models import DiagnosisResult, ERROR_MESSAGES, PlantType, UserState
from app.services.session_service import session_service
from app.services.gemini_service import GeminiAPIError, gemini_service
from app.utils.text_messages import TextMessageBuilder

if TYPE_CHECKING:
    from app.handlers.line_handler import LineHandler

logger = logging.getLogger(__name__)
settings = get_settings()


class MessageHandler:
    """
    Handler for message processing and diagnosis workflow.

    Manages:
    - Diagnosis processing pipeline
    - Result management
    - Push message sending
    """

    def __init__(self):
        """Initialize message handler."""
        self.configuration = Configuration(
            access_token=settings.line_channel_access_token
        )
        # Store last diagnosis result per user
        self._last_results: dict[str, DiagnosisResult] = {}

    def _get_messaging_api(self) -> MessagingApi:
        """Get MessagingApi client."""
        api_client = ApiClient(self.configuration)
        return MessagingApi(api_client)

    def _push_message(self, user_id: str, messages: list) -> None:
        """
        Send push message to user.

        Args:
            user_id: LINE user ID
            messages: List of messages to send
        """
        try:
            api = self._get_messaging_api()
            api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=messages
                )
            )
        except Exception as e:
            logger.error(f"Failed to send push message: {e}")

    def _push_text(self, user_id: str, text: str) -> None:
        """Send a simple text push message."""
        self._push_message(user_id, [TextMessage(text=text)])

    async def process_diagnosis(
        self,
        user_id: str,
        line_handler: "LineHandler"
    ) -> None:
        """
        Process diagnosis for user.

        Args:
            user_id: LINE user ID
            line_handler: LINE handler for sending messages
        """
        try:
            # Get user data from session
            image_data, content_type = await session_service.get_user_image(user_id)
            user_info = await session_service.get_user_info(user_id)

            if not image_data:
                self._push_text(
                    user_id,
                    TextMessageBuilder.format_error(ERROR_MESSAGES["session_expired"])
                )
                await session_service.clear_user_session(user_id)
                return

            # Call Gemini for diagnosis
            logger.info(f"Running Gemini diagnosis for user {user_id}")
            result = await gemini_service.diagnose(
                image_data=image_data,
                plant_type=user_info.plant_type,
                content_type=content_type or "image/jpeg",
                plant_part=user_info.plant_part,
                additional_info=user_info.additional_info
            )

            # Store in memory for quick access during the session
            self._last_results[user_id] = result

            # Increment rate limit counter
            await session_service.increment_rate_counter(user_id)

            # Check confidence level
            if result.confidence_level < 50:
                self._push_text(
                    user_id,
                    TextMessageBuilder.format_error(ERROR_MESSAGES["low_confidence"])
                )
            else:
                # Send diagnosis and treatment as one text message
                diagnosis_text = TextMessageBuilder.format_diagnosis_result(result)
                self._push_text(user_id, diagnosis_text)

            # Update state
            await session_service.set_user_state(user_id, UserState.COMPLETED)

        except GeminiAPIError as e:
            logger.error(f"Gemini API error for user {user_id}: {e}")
            self._push_text(
                user_id,
                TextMessageBuilder.format_error(e.user_message)
            )
            await session_service.set_user_state(user_id, UserState.IDLE)

        except Exception as e:
            logger.error(f"Diagnosis failed for user {user_id}: {e}")
            self._push_text(
                user_id,
                TextMessageBuilder.format_error(ERROR_MESSAGES["api_error"])
            )
            await session_service.set_user_state(user_id, UserState.IDLE)

    async def show_treatment(
        self,
        user_id: str,
        reply_token: str,
        line_handler: "LineHandler"
    ) -> None:
        """
        Show treatment details for last diagnosis.
        """
        result = self._last_results.get(user_id)

        if result:
            line_handler._reply_text(
                reply_token,
                TextMessageBuilder.format_diagnosis_result(result)
            )
        else:
            line_handler._reply_text(
                reply_token,
                "ไม่พบผลวินิจฉัย กรุณาส่งรูปภาพใหม่"
            )

    async def show_diagnosis(
        self,
        user_id: str,
        reply_token: str,
        line_handler: "LineHandler"
    ) -> None:
        """
        Show diagnosis result again.
        """
        result = self._last_results.get(user_id)

        if result:
            line_handler._reply_text(
                reply_token,
                TextMessageBuilder.format_diagnosis_result(result)
            )
        else:
            line_handler._reply_text(
                reply_token,
                "ไม่พบผลวินิจฉัย กรุณาส่งรูปภาพใหม่"
            )

    def clear_user_results(self, user_id: str) -> None:
        """
        Clear diagnosis results for user.
        """
        if user_id in self._last_results:
            del self._last_results[user_id]
