import hashlib
from typing import Optional, Union
from redis.asyncio.client import Redis
from redis.asyncio.client import Redis as AsyncRedis


class SessionsDictRedisCLI:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def add_to_dict(self, dict_name: str, key: str, value: str) -> None:
        """Add a key-value pair to a dictionary in Redis."""
        await self.redis.hset(dict_name, key, value)
    
    async def get_from_dict(self, dict_name: str, key: str) -> Optional[bytes]:
        """Get a value from a dictionary in Redis."""
        return await self.redis.hget(dict_name, key)
    
    async def remove_from_dict(self, dict_name: str, key: str) -> None:
        """Remove a key-value pair from a dictionary in Redis."""
        await self.redis.hdel(dict_name, key)
    
    async def get_all_from_dict(self, dict_name: str) -> dict:
        """Get all key-value pairs from a dictionary in Redis."""
        return await self.redis.hgetall(dict_name)
    
    async def del_all_from_dict(self, dict_name: str) -> None:
        """Remove a user dictionary from Redis."""
        await self.redis.delete(dict_name)


class CacheService:
    FORMATER = "{}_service_::{}"

    def __init__(self, name: str, redis_host: str, redis_port: int):
        
        connection = AsyncRedis(
            host=redis_host,
            port=redis_port,
            decode_responses=False
        )
        self.name = name
        self.redis = SessionsDictRedisCLI(connection)
    
    @classmethod
    def from_string(cls, value: str) -> str:
        return hashlib.md5(str(value).encode()).hexdigest()
    
    def _get_key(self, key: str) -> str:
        cache_key = self.from_string(key)
        return self.FORMATER.format(self.name, cache_key)
    
    async def add_to_dict(self, dict_name: Union[int, str], key: str, value: str) -> None:
        await self.redis.add_to_dict(self._get_key(dict_name), key, value)
    
    async def get_all_from_dict(self, key: Union[int, str]) -> dict:
        return await self.redis.get_all_from_dict(self._get_key(key))
    
    async def get_from_dict(self, dict_name: Union[int, str], key: str) -> str:
        value: Optional[bytes] = await self.redis.get_from_dict(self._get_key(dict_name), key)
        return value.decode() if value else None
    
    async def remove_from_dict(self, dict_name: Union[int, str], key: str) -> None:
        await self.redis.remove_from_dict(self._get_key(dict_name), key)
    
    async def del_all_from_dict(self, dict_name: Union[int, str]) -> None:
        await self.redis.del_all_from_dict(dict_name)


class SessionService:
    def __init__(self, redis_host: str, redis_port: int):
        self.cache = CacheService("session", redis_host, redis_port)
    
    async def add_refresh_token(self, user_id: int, session_id: str, refresh_token: str) -> None:
        await self.cache.add_to_dict(user_id, session_id, refresh_token)
    
    async def get_refresh_token(self, user_id: int, session_id: str) -> str:
        return await self.cache.get_from_dict(user_id, session_id)
    
    async def get_all_sessions(self, user_id: int) -> dict:
        return await self.cache.get_all_from_dict(user_id)
    
    async def del_user_session(self, user_id: int, session_id: str):
        await self.cache.remove_from_dict(user_id, session_id)
    
    async def del_all_sessions(self, user_id: int):
        await self.cache.del_all_from_dict(user_id)
