import asyncio

from inspect import iscoroutinefunction, isawaitable
from functools import wraps
from typing import Any, Callable, Optional
from redis.asyncio.client import Redis as AsyncRedis

from tools.SimpleCache.Coder import PickleCoder
from tools.SimpleCache.KeyBuilder import pickle_keygen, from_string
from tools.SimpleCache.Redis import RedisBackend
from tools.SimpleCache.types import Coder, KeyGen
from src.settings import settings


host: str = settings.redis_host
port: int = settings.redis_port
connection = AsyncRedis(host=host, port=port, decode_responses=False)
    

def get_connection() -> RedisBackend:
    return RedisBackend(connection)


class CacheDecorator:
    """Simple caching decorator for functions."""
    FORMATER = "{}_deco_::{}"
    
    def __init__(
        self, 
        name: str,
        redis: Optional[RedisBackend] = get_connection()
    ) -> None:
        
        """Initialize DeCache with a name and Redis connection details."""
        self.name = name
        self.redis = redis

    def cache(
        self,
        expire: Optional[int] = None,
        keygen: Optional[KeyGen] = None,
        coder: Optional[Coder] = None
    ) -> Callable:
        """Decorator to cache function results."""
        
        def wrapper(func: Callable) -> Callable:

            @wraps(func)
            async def inner(*args, **kwargs) -> Any:
                """Inner function to execute the function and cache its result."""

                nonlocal expire
                nonlocal keygen
                nonlocal coder

                async def is_async_func(*args, **kwargs) -> Optional[Any]:
                    """Check if the function is asynchronous and execute accordingly."""
                    if iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return await asyncio.to_thread(func, *args, **kwargs)
                
                keygen = keygen or pickle_keygen
                coder = coder or PickleCoder
                expire = expire or None

                cache_key = keygen(func, args, kwargs)
                
                if isawaitable(cache_key):
                    cache_key = await cache_key

                assert isinstance(cache_key, str)

                redis_key = self.FORMATER.format(self.name, cache_key)

                result = await self.redis.get(key=redis_key)

                if result is None:
                    result = await is_async_func(*args, *kwargs)
                    to_cache = coder.encode(result)
                    await self.redis.set(redis_key, to_cache, expire)
                else:
                    result = coder.decode(result)

                return result
            
            return inner
        
        return wrapper


class CacheTool:
    FORMATER = "{}_service_::{}"

    def __init__(
        self, 
        name: str,  
        redis: Optional[RedisBackend] = get_connection(),
    ):
        self.name = name
        self.redis = redis

    async def _get_key(self, key: str) -> str:
        cache_key = from_string(key)
        return self.FORMATER.format(self.name, cache_key)
        

    async def set_data(self, key: str, value: Any) -> None: 
        await self.redis.set(
            (await self._get_key(key)),
            PickleCoder.encode(value)
        )

    async def set_with_exp(self, key: str, value: Any, exp: int=3600) -> None:
        await self.redis.set(
            (await self._get_key(key)),
            PickleCoder.encode(value),
            expire=exp
        )

    async def get_data(self, key: str) -> Any:
        data = await self.redis.get(await self._get_key(key))
        if data:
            return PickleCoder.decode(data)
        else:
            return None
    
    async def del_data(self, key: str) -> None:
        await self.redis.delete(await self._get_key(key))
    
    async def clear_data(self):
        await self.redis.clear(f"{self.name}_service_")