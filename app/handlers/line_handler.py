"""
LINE Webhook Handler Module
Handles LINE webhook events and message routing
"""

import logging
from typing import Any

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    Event,
    FollowEvent,
    ImageMessageContent,
    MessageEvent,
    PostbackEvent,
    TextMessageContent,
)

from app.config import get_settings
from app.handlers.message_handler import MessageHandler
from app.models import ERROR_MESSAGES, PlantType, Region, UserState
from app.services.session_service import session_service
from app.services.image_service import ImageValidationError, image_service
from app.utils.flex_messages import FlexMessageBuilder
from app.utils.parsers import (
    is_greeting,
    is_help_request,
    is_skip_command,
    parse_plant_type,
    parse_postback_data,
    parse_region,
    sanitize_text,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class LineHandler:
    """
    Handler for LINE webhook events.

    Manages:
    - Webhook signature verification
    - Event routing (message, postback, follow)
    - User state management
    - Message sending
    """

    def __init__(self):
        """Initialize LINE handler with SDK clients."""
        self.webhook_handler = WebhookHandler(settings.line_channel_secret)
        self.configuration = Configuration(
            access_token=settings.line_channel_access_token
        )
        self.message_handler = MessageHandler()

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers with webhook handler."""

        @self.webhook_handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event: MessageEvent) -> None:
            """Handle text message events."""
            self._handle_text_message_sync(event)

        @self.webhook_handler.add(MessageEvent, message=ImageMessageContent)
        def handle_image_message(event: MessageEvent) -> None:
            """Handle image message events."""
            self._handle_image_message_sync(event)

        @self.webhook_handler.add(PostbackEvent)
        def handle_postback(event: PostbackEvent) -> None:
            """Handle postback events."""
            self._handle_postback_sync(event)

        @self.webhook_handler.add(FollowEvent)
        def handle_follow(event: FollowEvent) -> None:
            """Handle follow events."""
            self._handle_follow_sync(event)

    async def handle_webhook(self, body: str, signature: str) -> None:
        """
        Handle incoming webhook request.
        Runs the synchronous handler in a separate thread to avoid event loop conflicts.
        """
        import asyncio
        import functools

        # Run the synchronous SDK handler in a thread
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, 
            functools.partial(self.webhook_handler.handle, body, signature)
        )

    def _get_messaging_api(self) -> MessagingApi:
        """Get MessagingApi client."""
        api_client = ApiClient(self.configuration)
        return MessagingApi(api_client)

    def _reply_message(
        self,
        reply_token: str,
        messages: list
    ) -> None:
        """
        Send reply message.

        Args:
            reply_token: LINE reply token
            messages: List of messages to send
        """
        try:
            api = self._get_messaging_api()
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=messages
                )
            )
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

    def _reply_text(self, reply_token: str, text: str) -> None:
        """Send a simple text reply."""
        self._reply_message(reply_token, [TextMessage(text=text)])

    def _reply_flex(self, reply_token: str, flex_message) -> None:
        """Send a flex message reply."""
        self._reply_message(reply_token, [flex_message])


    # ==================== Synchronous Event Handlers ====================

    def _handle_text_message_sync(self, event: MessageEvent) -> None:
        """Handle text message event (sync wrapper)."""
        import asyncio
        import threading

        # Create a new event loop for this thread if it doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self._handle_text_message(event))

    def _handle_image_message_sync(self, event: MessageEvent) -> None:
        """Handle image message event (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self._handle_image_message(event))

    def _handle_postback_sync(self, event: PostbackEvent) -> None:
        """Handle postback event (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self._handle_postback(event))

    def _handle_follow_sync(self, event: FollowEvent) -> None:
        """Handle follow event (sync wrapper)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self._handle_follow(event))

    # ==================== Async Event Handlers ====================

    async def _handle_text_message(self, event: MessageEvent) -> None:
        """
        Handle text message event.

        Args:
            event: LINE message event
        """
        user_id = event.source.user_id
        text = sanitize_text(event.message.text)
        reply_token = event.reply_token

        logger.info(f"Text message from {user_id}: {text[:50]}...")

        # Check for greeting
        if is_greeting(text):
            self._reply_flex(
                reply_token,
                FlexMessageBuilder.create_welcome_message()
            )
            return

        # Check for help request
        if is_help_request(text):
            self._reply_flex(
                reply_token,
                FlexMessageBuilder.create_welcome_message()
            )
            return

        # Get current user state
        state = await session_service.get_user_state(user_id)

        if state == UserState.WAITING_FOR_PLANT_TYPE:
            await self._handle_plant_type_input(
                user_id, text, reply_token
            )
        elif state == UserState.WAITING_FOR_PLANT_PART:
            await self._handle_plant_part_input(
                user_id, text, reply_token
            )
        else:
            # Default response - prompt to send image
            self._reply_text(
                reply_token,
                "กรุณาส่งรูปภาพพืชที่ต้องการวินิจฉัยโรค 📷"
            )

    async def _handle_image_message(self, event: MessageEvent) -> None:
        """
        Handle image message event.

        Args:
            event: LINE message event
        """
        user_id = event.source.user_id
        message_id = event.message.id
        reply_token = event.reply_token

        logger.info(f"Image message from {user_id}: {message_id}")

        try:
            # Check rate limit
            is_allowed, remaining = await session_service.check_rate_limit(user_id)
            if not is_allowed:
                self._reply_flex(
                    reply_token,
                    FlexMessageBuilder.create_error_message(
                        ERROR_MESSAGES["rate_limit_exceeded"].format(minutes=60)
                    )
                )
                return

            # Download and process image
            image_data, content_type = await image_service.process_line_image(
                message_id,
                settings.line_channel_access_token
            )

            # Store image in session
            await session_service.set_user_image(
                user_id, image_data, content_type
            )

            # Update state to waiting for plant type
            await session_service.set_user_state(
                user_id, UserState.WAITING_FOR_PLANT_TYPE
            )

            # Send info request message
            self._reply_flex(
                reply_token,
                FlexMessageBuilder.create_info_request_message()
            )

        except ImageValidationError as e:
            logger.warning(f"Image validation failed: {e}")
            self._reply_flex(
                reply_token,
                FlexMessageBuilder.create_error_message(e.user_message)
            )

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            self._reply_flex(
                reply_token,
                FlexMessageBuilder.create_error_message(
                    ERROR_MESSAGES["api_error"]
                )
            )

    async def _handle_postback(self, event: PostbackEvent) -> None:
        """
        Handle postback event.

        Args:
            event: LINE postback event
        """
        user_id = event.source.user_id
        data = parse_postback_data(event.postback.data)
        reply_token = event.reply_token

        logger.info(f"Postback from {user_id}: {data}")

        # Handle plant type selection
        if "plant_type" in data:
            plant_type_str = data["plant_type"]

            if plant_type_str == "other":
                await session_service.set_user_state(
                    user_id, UserState.WAITING_FOR_PLANT_TYPE
                )
                self._reply_text(
                    reply_token,
                    "กรุณาพิมพ์ชื่อพืชที่ต้องการวินิจฉัย"
                )
            else:
                try:
                    plant_type = PlantType[plant_type_str]
                    await self._set_plant_type_and_proceed(
                        user_id, plant_type, reply_token
                    )
                except KeyError:
                    self._reply_text(
                        reply_token,
                        "ไม่รู้จักชนิดพืชนี้ กรุณาเลือกใหม่"
                    )

        # Handle plant part selection
        elif "plant_part" in data:
            plant_part_str = data["plant_part"]

            if plant_part_str == "skip":
                await self._proceed_to_diagnosis(user_id, reply_token)
            else:
                try:
                    plant_part = PlantPart[plant_part_str]
                    await self._set_plant_part_and_diagnose(
                        user_id, plant_part, reply_token
                    )
                except KeyError:
                    await self._proceed_to_diagnosis(user_id, reply_token)

        # Handle show treatment
        elif data.get("show_treatment"):
            await self.message_handler.show_treatment(user_id, reply_token, self)

        # Handle show diagnosis
        elif data.get("show_diagnosis"):
            await self.message_handler.show_diagnosis(user_id, reply_token, self)

        # Handle new diagnosis
        elif data.get("new_diagnosis"):
            await session_service.clear_user_session(user_id)
            self._reply_text(
                reply_token,
                "กรุณาส่งรูปภาพพืชที่ต้องการวินิจฉัยโรค 📷"
            )

        # Handle retry
        elif data.get("retry"):
            await session_service.clear_user_session(user_id)
            self._reply_text(
                reply_token,
                "กรุณาส่งรูปภาพใหม่อีกครั้ง 📷"
            )

    async def _handle_follow(self, event: FollowEvent) -> None:
        """
        Handle follow event (new user).

        Args:
            event: LINE follow event
        """
        user_id = event.source.user_id
        reply_token = event.reply_token

        logger.info(f"New follower: {user_id}")

        self._reply_flex(
            reply_token,
            FlexMessageBuilder.create_welcome_message()
        )

    # ==================== Helper Methods ====================

    async def _handle_plant_type_input(
        self,
        user_id: str,
        text: str,
        reply_token: str
    ) -> None:
        """Handle plant type text input."""
        plant_type = parse_plant_type(text)

        if plant_type:
            await self._set_plant_type_and_proceed(
                user_id, plant_type, reply_token
            )
        else:
            # Store as other plant type with custom name
            user_info = await session_service.get_user_info(user_id)
            user_info.additional_info = f"ชนิดพืช: {text}"
            await session_service.set_user_info(user_id, user_info)

            # Proceed to plant part selection
            await session_service.set_user_state(
                user_id, UserState.WAITING_FOR_PLANT_PART
            )
            self._reply_flex(
                reply_token,
                FlexMessageBuilder.create_plant_part_request_message()
            )

    async def _handle_plant_part_input(
        self,
        user_id: str,
        text: str,
        reply_token: str
    ) -> None:
        """Handle plant part text input."""
        if is_skip_command(text):
            await self._proceed_to_diagnosis(user_id, reply_token)
        else:
            # We don't really have a parser for plant parts, so just treat as additional info
            user_info = await session_service.get_user_info(user_id)
            additional = user_info.additional_info or ""
            user_info.additional_info = f"{additional} จุดที่พบ: {text}".strip()
            await session_service.set_user_info(user_id, user_info)
            await self._proceed_to_diagnosis(user_id, reply_token)

    async def _set_plant_type_and_proceed(
        self,
        user_id: str,
        plant_type: PlantType,
        reply_token: str
    ) -> None:
        """Set plant type and proceed to region selection."""
        user_info = await session_service.get_user_info(user_id)
        user_info.plant_type = plant_type
        await session_service.set_user_info(user_id, user_info)

        # Move to plant part selection
        await session_service.set_user_state(
            user_id, UserState.WAITING_FOR_PLANT_PART
        )

        self._reply_flex(
            reply_token,
            FlexMessageBuilder.create_plant_part_request_message()
        )

    async def _set_plant_part_and_diagnose(
        self,
        user_id: str,
        plant_part: PlantPart,
        reply_token: str
    ) -> None:
        """Set plant part and start diagnosis."""
        user_info = await session_service.get_user_info(user_id)
        user_info.plant_part = plant_part
        await session_service.set_user_info(user_id, user_info)

        await self._proceed_to_diagnosis(user_id, reply_token)

    async def _proceed_to_diagnosis(
        self,
        user_id: str,
        reply_token: str
    ) -> None:
        """Start the diagnosis process."""
        # Send processing message
        self._reply_flex(
            reply_token,
            FlexMessageBuilder.create_processing_message()
        )

        # Update state
        await session_service.set_user_state(user_id, UserState.PROCESSING)

        # Run diagnosis (this will send result via push message)
        await self.message_handler.process_diagnosis(user_id, self)


# Global line handler instance
line_handler = LineHandler()
