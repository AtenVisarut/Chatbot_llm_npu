"""
Cache Service Module
Redis operations for session management, caching, and rate limiting
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from app.config import get_settings
from app.models import DiagnosisResult, UserInfo, UserSession, UserState

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    """
    Redis cache service for managing user sessions, diagnosis cache, and rate limiting.

    Key patterns:
    - user:{user_id}:state - User conversation state
    - user:{user_id}:image - Stored image data
    - user:{user_id}:info - User provided information
    - diagnosis:{hash} - Cached diagnosis results
    - rate:{user_id}:{hour} - Rate limiting counter
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize the cache service.

        Args:
            redis_url: Redis connection URL. Defaults to settings.redis_url
        """
        self.redis_url = redis_url or settings.redis_url
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        if self._client is None:
            self._pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                decode_responses=False
            )
            self._client = redis.Redis(connection_pool=self._pool)
            logger.info("Connected to Redis")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        logger.info("Disconnected from Redis")

    async def _get_client(self) -> redis.Redis:
        """Get Redis client, connecting if necessary."""
        if self._client is None:
            await self.connect()
        return self._client

    # ==================== User Session Management ====================

    async def get_user_state(self, user_id: str) -> UserState:
        """
        Get user's current conversation state.

        Args:
            user_id: LINE user ID

        Returns:
            UserState: Current state or IDLE if not found
        """
        client = await self._get_client()
        key = f"user:{user_id}:state"
        state = await client.get(key)
        if state:
            return UserState(state.decode())
        return UserState.IDLE

    async def set_user_state(
        self,
        user_id: str,
        state: UserState,
        expire_hours: int | None = None
    ) -> None:
        """
        Set user's conversation state.

        Args:
            user_id: LINE user ID
            state: New state to set
            expire_hours: Expiry time in hours
        """
        client = await self._get_client()
        key = f"user:{user_id}:state"
        expire = expire_hours or settings.user_state_expiry_hours
        await client.setex(key, expire * 3600, state.value)
        logger.debug(f"Set user state: {user_id} -> {state.value}")

    async def get_user_image(self, user_id: str) -> tuple[bytes | None, str | None]:
        """
        Get stored user image data.

        Args:
            user_id: LINE user ID

        Returns:
            Tuple of (image_data, content_type) or (None, None)
        """
        client = await self._get_client()
        image_key = f"user:{user_id}:image"
        type_key = f"user:{user_id}:image_type"

        image_data = await client.get(image_key)
        content_type = await client.get(type_key)

        if image_data and content_type:
            return image_data, content_type.decode()
        return None, None

    async def set_user_image(
        self,
        user_id: str,
        image_data: bytes,
        content_type: str,
        expire_hours: int | None = None
    ) -> None:
        """
        Store user image data.

        Args:
            user_id: LINE user ID
            image_data: Image binary data
            content_type: MIME type of the image
            expire_hours: Expiry time in hours
        """
        client = await self._get_client()
        image_key = f"user:{user_id}:image"
        type_key = f"user:{user_id}:image_type"
        expire = expire_hours or settings.user_state_expiry_hours

        pipe = client.pipeline()
        pipe.setex(image_key, expire * 3600, image_data)
        pipe.setex(type_key, expire * 3600, content_type)
        await pipe.execute()
        logger.debug(f"Stored image for user: {user_id}")

    async def get_user_info(self, user_id: str) -> UserInfo:
        """
        Get stored user information.

        Args:
            user_id: LINE user ID

        Returns:
            UserInfo: User information or default UserInfo
        """
        client = await self._get_client()
        key = f"user:{user_id}:info"
        data = await client.get(key)
        if data:
            return UserInfo.model_validate_json(data)
        return UserInfo()

    async def set_user_info(
        self,
        user_id: str,
        info: UserInfo,
        expire_hours: int | None = None
    ) -> None:
        """
        Store user information.

        Args:
            user_id: LINE user ID
            info: User information to store
            expire_hours: Expiry time in hours
        """
        client = await self._get_client()
        key = f"user:{user_id}:info"
        expire = expire_hours or settings.user_state_expiry_hours
        await client.setex(key, expire * 3600, info.model_dump_json())
        logger.debug(f"Stored user info: {user_id}")

    async def clear_user_session(self, user_id: str) -> None:
        """
        Clear all session data for a user.

        Args:
            user_id: LINE user ID
        """
        client = await self._get_client()
        keys = [
            f"user:{user_id}:state",
            f"user:{user_id}:image",
            f"user:{user_id}:image_type",
            f"user:{user_id}:info"
        ]
        await client.delete(*keys)
        logger.debug(f"Cleared session for user: {user_id}")

    # ==================== Diagnosis Caching ====================

    def _generate_diagnosis_key(
        self,
        image_data: bytes,
        plant_type: str,
        region: str | None
    ) -> str:
        """
        Generate a cache key for diagnosis results.

        Args:
            image_data: Image binary data
            plant_type: Type of plant
            region: Thai region

        Returns:
            Cache key string
        """
        content = image_data + plant_type.encode() + (region or "").encode()
        hash_value = hashlib.md5(content).hexdigest()
        return f"diagnosis:{hash_value}"

    async def get_cached_diagnosis(
        self,
        image_data: bytes,
        plant_type: str,
        region: str | None = None
    ) -> DiagnosisResult | None:
        """
        Get cached diagnosis result.

        Args:
            image_data: Image binary data
            plant_type: Type of plant
            region: Thai region

        Returns:
            DiagnosisResult if found, None otherwise
        """
        client = await self._get_client()
        key = self._generate_diagnosis_key(image_data, plant_type, region)
        data = await client.get(key)
        if data:
            logger.info(f"Cache hit for diagnosis: {key[:20]}...")
            return DiagnosisResult.model_validate_json(data)
        return None

    async def cache_diagnosis(
        self,
        image_data: bytes,
        plant_type: str,
        region: str | None,
        result: DiagnosisResult,
        expire_hours: int | None = None
    ) -> None:
        """
        Cache diagnosis result.

        Args:
            image_data: Image binary data
            plant_type: Type of plant
            region: Thai region
            result: Diagnosis result to cache
            expire_hours: Expiry time in hours
        """
        client = await self._get_client()
        key = self._generate_diagnosis_key(image_data, plant_type, region)
        expire = expire_hours or settings.cache_expiry_hours
        await client.setex(key, expire * 3600, result.model_dump_json())
        logger.info(f"Cached diagnosis: {key[:20]}...")

    # ==================== Rate Limiting ====================

    async def check_rate_limit(
        self,
        user_id: str,
        max_requests: int | None = None
    ) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: LINE user ID
            max_requests: Maximum requests per hour

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        client = await self._get_client()
        max_req = max_requests or settings.max_requests_per_hour

        current_hour = datetime.utcnow().strftime("%Y%m%d%H")
        key = f"rate:{user_id}:{current_hour}"

        current = await client.get(key)
        count = int(current) if current else 0

        remaining = max_req - count
        is_allowed = count < max_req

        return is_allowed, max(0, remaining)

    async def increment_rate_counter(self, user_id: str) -> int:
        """
        Increment rate limit counter for user.

        Args:
            user_id: LINE user ID

        Returns:
            Current count after increment
        """
        client = await self._get_client()
        current_hour = datetime.utcnow().strftime("%Y%m%d%H")
        key = f"rate:{user_id}:{current_hour}"

        count = await client.incr(key)
        if count == 1:
            await client.expire(key, 3600)

        return count

    # ==================== Health Check ====================

    async def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    # ==================== Utility Methods ====================

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            client = await self._get_client()
            info = await client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Global cache service instance
cache_service = CacheService()
