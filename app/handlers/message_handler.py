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
from app.services.cache_service import cache_service
from app.services.gemini_service import GeminiAPIError, gemini_service
from app.utils.flex_messages import FlexMessageBuilder

if TYPE_CHECKING:
    from app.handlers.line_handler import LineHandler

logger = logging.getLogger(__name__)
settings = get_settings()


class MessageHandler:
    """
    Handler for message processing and diagnosis workflow.

    Manages:
    - Diagnosis processing pipeline
    - Result caching and retrieval
    - Push message sending
    """

    def __init__(self):
        """Initialize message handler."""
        self.configuration = Configuration(
            access_token=settings.line_channel_access_token
        )
        # Store last diagnosis result per user
        self._diagnosis_cache: dict[str, DiagnosisResult] = {}

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

    def _push_flex(self, user_id: str, flex_message) -> None:
        """Send a flex push message."""
        self._push_message(user_id, [flex_message])

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
            # Get user data from cache
            image_data, content_type = await cache_service.get_user_image(user_id)
            user_info = await cache_service.get_user_info(user_id)

            if not image_data:
                self._push_flex(
                    user_id,
                    FlexMessageBuilder.create_error_message(
                        ERROR_MESSAGES["session_expired"]
                    )
                )
                await cache_service.clear_user_session(user_id)
                return

            # Get plant type (default to rice if not specified)
            plant_type = user_info.plant_type or PlantType.RICE

            # Check for cached diagnosis
            cached_result = await cache_service.get_cached_diagnosis(
                image_data,
                plant_type.value,
                user_info.region.value if user_info.region else None
            )

            if cached_result:
                logger.info(f"Using cached diagnosis for user {user_id}")
                result = cached_result
            else:
                # Call Gemini for diagnosis
                logger.info(f"Running Gemini diagnosis for user {user_id}")
                result = await gemini_service.diagnose(
                    image_data=image_data,
                    plant_type=plant_type,
                    content_type=content_type or "image/jpeg",
                    region=user_info.region,
                    additional_info=user_info.additional_info
                )

                # Cache the result
                await cache_service.cache_diagnosis(
                    image_data,
                    plant_type.value,
                    user_info.region.value if user_info.region else None,
                    result
                )

            # Store in memory cache for quick access
            self._diagnosis_cache[user_id] = result

            # Increment rate limit counter
            await cache_service.increment_rate_counter(user_id)

            # Check confidence level
            if result.confidence_level < 50:
                self._push_flex(
                    user_id,
                    FlexMessageBuilder.create_error_message(
                        ERROR_MESSAGES["low_confidence"]
                    )
                )
            else:
                # Send diagnosis result
                self._push_flex(
                    user_id,
                    FlexMessageBuilder.create_diagnosis_result_message(result)
                )

            # Update state
            await cache_service.set_user_state(user_id, UserState.COMPLETED)

        except GeminiAPIError as e:
            logger.error(f"Gemini API error for user {user_id}: {e}")
            self._push_flex(
                user_id,
                FlexMessageBuilder.create_error_message(e.user_message)
            )
            await cache_service.set_user_state(user_id, UserState.IDLE)

        except Exception as e:
            logger.error(f"Diagnosis failed for user {user_id}: {e}")
            self._push_flex(
                user_id,
                FlexMessageBuilder.create_error_message(
                    ERROR_MESSAGES["api_error"]
                )
            )
            await cache_service.set_user_state(user_id, UserState.IDLE)

    async def show_treatment(
        self,
        user_id: str,
        reply_token: str,
        line_handler: "LineHandler"
    ) -> None:
        """
        Show treatment details for last diagnosis.

        Args:
            user_id: LINE user ID
            reply_token: LINE reply token
            line_handler: LINE handler for sending messages
        """
        result = self._diagnosis_cache.get(user_id)

        if result:
            line_handler._reply_flex(
                reply_token,
                FlexMessageBuilder.create_treatment_message(result)
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

        Args:
            user_id: LINE user ID
            reply_token: LINE reply token
            line_handler: LINE handler for sending messages
        """
        result = self._diagnosis_cache.get(user_id)

        if result:
            line_handler._reply_flex(
                reply_token,
                FlexMessageBuilder.create_diagnosis_result_message(result)
            )
        else:
            line_handler._reply_text(
                reply_token,
                "ไม่พบผลวินิจฉัย กรุณาส่งรูปภาพใหม่"
            )

    def clear_user_cache(self, user_id: str) -> None:
        """
        Clear diagnosis cache for user.

        Args:
            user_id: LINE user ID
        """
        if user_id in self._diagnosis_cache:
            del self._diagnosis_cache[user_id]
