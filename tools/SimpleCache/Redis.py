from typing import Optional, Coroutine, Any
from redis.asyncio.client import Redis


class RedisBackend:
    """Backend for interacting with Redis."""
    
    def __init__(self, redis: Redis):
        """Initialize with a Redis instance."""
        self.redis = redis

    async def get(self, key: str) -> Coroutine[Optional[bytes], Any, Any]:
        """Get value from Redis."""
        return await self.redis.get(key)
        
    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> Coroutine[None, Any, Any]:
        """Set value in Redis with an optional expiration time."""
        if expire:
            await self.redis.set(key, value, ex=expire)
        else:
            await self.redis.set(key, value)

    async def delete(self, key: str) -> Coroutine[None, Any, Any]:
        """Delete a key from Redis."""
        await self.redis.delete(key)

    async def clear(self, name: str) -> Coroutine[None, Any, Any]:
        """Clear all keys with a specific prefix from Redis."""
        keys = await self.redis.keys(f"{name}::")
        await self.redis.delete(*keys)
        
