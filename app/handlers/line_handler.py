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
from app.models import ERROR_MESSAGES, PlantPart, PlantType, UserState
from app.services.session_service import session_service
from app.services.image_service import ImageValidationError, image_service
from app.utils.text_messages import TextMessageBuilder
from app.utils.parsers import (
    is_greeting,
    is_help_request,
    is_skip_command,
    parse_plant_type,
    parse_postback_data,
    parse_plant_part,
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

        # Check for greeting or help
        if is_greeting(text) or is_help_request(text):
            self._reply_text(
                reply_token,
                TextMessageBuilder.format_welcome()
            )
            return

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
            is_allowed, remaining = await session_service.check_rate_limit(
                user_id, max_requests=settings.max_requests_per_hour
            )
            if not is_allowed:
                self._reply_text(
                    reply_token,
                    TextMessageBuilder.format_error(
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

            # Send info request message
            self._reply_text(
                reply_token,
                TextMessageBuilder.format_processing()
            )

            # Mark state as processing
            await session_service.set_user_state(
                user_id, UserState.PROCESSING
            )

            # Trigger diagnosis immediately
            await self.message_handler.process_diagnosis(user_id, self)

        except ImageValidationError as e:
            logger.warning(f"Image validation failed: {e}")
            self._reply_text(
                reply_token,
                TextMessageBuilder.format_error(e.user_message)
            )

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            self._reply_text(
                reply_token,
                TextMessageBuilder.format_error(ERROR_MESSAGES["api_error"])
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

        # Postback handlers for plant type/part are deprecated in direct diagnosis flow.
        # We keep the function structure for other postbacks like treatment or retry.
        
        # Handle show treatment
        if data.get("show_treatment"):
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

        self._reply_text(
            reply_token,
            TextMessageBuilder.format_welcome()
        )

    # ==================== Helper Methods ====================


    async def _proceed_to_diagnosis(
        self,
        user_id: str,
        reply_token: str
    ) -> None:
        """Start the diagnosis process."""
        # Send processing message
        self._reply_text(
            reply_token,
            TextMessageBuilder.format_processing()
        )

        # Update state
        await session_service.set_user_state(user_id, UserState.PROCESSING)

        # Run diagnosis (this will send result via push message)
        await self.message_handler.process_diagnosis(user_id, self)


# Global line handler instance
line_handler = LineHandler()
