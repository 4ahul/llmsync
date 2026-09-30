import redis.asyncio as aioredis
from llmsync.config import settings
from typing import Optional

class RedisClient:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def set_with_expiry(self, key: str, value: str, expire_seconds: int):
        """Set key with expiration."""
        await self.redis.setex(key, expire_seconds, value)

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self.redis.get(key)

    async def delete(self, key: str):
        """Delete key."""
        await self.redis.delete(key)

    async def sadd(self, key: str, *values):
        """Add to set."""
        await self.redis.sadd(key, *values)

    async def srem(self, key: str, *values):
        """Remove from set."""
        await self.redis.srem(key, *values)

    async def smembers(self, key: str) -> set:
        """Get all set members."""
        return await self.redis.smembers(key)

    async def publish(self, channel: str, message: str):
        """Publish message to channel."""
        await self.redis.publish(channel, message)

    async def subscribe(self, *channels):
        """Subscribe to channels. Returns pubsub object."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

redis_client = RedisClient()
