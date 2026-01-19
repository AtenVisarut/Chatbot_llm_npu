"""
Session Service Module
In-memory operations for session management
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from app.models import UserInfo, UserState

logger = logging.getLogger(__name__)


class SessionService:
    """
    In-memory session service for managing user sessions.
    Stateless for Vercel deployment.
    
    Warning: Sessions will be lost if the serverless instance restarts.
    """

    def __init__(self):
        """Initialize the in-memory session store."""
        # Simple dictionaries to store session data
        self._user_states: dict[str, tuple[UserState, datetime]] = {}
        self._user_images: dict[str, tuple[bytes, str, datetime]] = {}
        self._user_info: dict[str, tuple[UserInfo, datetime]] = {}
        self._rate_limits: dict[str, dict[str, int]] = {}

    async def connect(self) -> None:
        """No-op for in-memory store."""
        logger.info("In-memory session service initialized")

    async def disconnect(self) -> None:
        """No-op for in-memory store."""
        logger.info("In-memory session service cleaned up")

    # ==================== User Session Management ====================

    async def get_user_state(self, user_id: str) -> UserState:
        """Get user's current conversation state."""
        if user_id in self._user_states:
            state, expiry = self._user_states[user_id]
            if datetime.utcnow() < expiry:
                return state
            del self._user_states[user_id]
        return UserState.IDLE

    async def set_user_state(
        self,
        user_id: str,
        state: UserState,
        expire_hours: int | None = None
    ) -> None:
        """Set user's conversation state."""
        hours = expire_hours or 1
        expiry = datetime.utcnow() + timedelta(hours=hours)
        self._user_states[user_id] = (state, expiry)
        logger.debug(f"Set user state (memory): {user_id} -> {state.value}")

    async def get_user_image(self, user_id: str) -> tuple[bytes | None, str | None]:
        """Get stored user image data."""
        if user_id in self._user_images:
            image_data, content_type, expiry = self._user_images[user_id]
            if datetime.utcnow() < expiry:
                return image_data, content_type
            del self._user_images[user_id]
        return None, None

    async def set_user_image(
        self,
        user_id: str,
        image_data: bytes,
        content_type: str,
        expire_hours: int | None = None
    ) -> None:
        """Store user image data."""
        hours = expire_hours or 1
        expiry = datetime.utcnow() + timedelta(hours=hours)
        self._user_images[user_id] = (image_data, content_type, expiry)
        logger.debug(f"Stored image in memory for user: {user_id}")

    async def get_user_info(self, user_id: str) -> UserInfo:
        """Get stored user information."""
        if user_id in self._user_info:
            info, expiry = self._user_info[user_id]
            if datetime.utcnow() < expiry:
                return info
            del self._user_info[user_id]
        return UserInfo()

    async def set_user_info(
        self,
        user_id: str,
        info: UserInfo,
        expire_hours: int | None = None
    ) -> None:
        """Store user information."""
        hours = expire_hours or 1
        expiry = datetime.utcnow() + timedelta(hours=hours)
        self._user_info[user_id] = (info, expiry)
        logger.debug(f"Stored user info in memory: {user_id}")

    async def clear_user_session(self, user_id: str) -> None:
        """Clear all session data for a user."""
        self._user_states.pop(user_id, None)
        self._user_images.pop(user_id, None)
        self._user_info.pop(user_id, None)
        logger.debug(f"Cleared session in memory for user: {user_id}")

    # ==================== Rate Limiting ====================

    async def check_rate_limit(
        self,
        user_id: str,
        max_requests: int = 10
    ) -> tuple[bool, int]:
        """Check if user has exceeded rate limit (in-memory)."""
        hour_key = datetime.utcnow().strftime("%Y%m%d%H")
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = {}
        
        counts = self._rate_limits[user_id]
        current_count = counts.get(hour_key, 0)
        
        remaining = max_requests - current_count
        is_allowed = current_count < max_requests
        
        return is_allowed, max(0, remaining)

    async def increment_rate_counter(self, user_id: str) -> int:
        """Increment rate limit counter (in-memory)."""
        hour_key = datetime.utcnow().strftime("%Y%m%d%H")
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = {}
            
        counts = self._rate_limits[user_id]
        counts[hour_key] = counts.get(hour_key, 0) + 1
        
        return counts[hour_key]

    # ==================== Utility Methods ====================

    async def get_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        return {
            "active_states": len(self._user_states),
            "active_images": len(self._user_images),
            "active_info": len(self._user_info),
        }


# Global session service instance
session_service = SessionService()
