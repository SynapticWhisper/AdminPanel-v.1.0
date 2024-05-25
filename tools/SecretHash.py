import os
import hashlib

from pydantic import BaseModel

from tools.SimpleCache import CacheDecorator, CacheTool
from tools.SimpleCache.KeyBuilder import str_keygen

from src.settings import settings


class PydanticModel(BaseModel):
    ...


cache = CacheDecorator(name="secret_cache")
exp_seconds = settings.auth_jwt.access_token_expire_minutes * 60


@cache.cache(expire=exp_seconds, keygen=str_keygen)
async def generate_secret(data: str, solt: bytes, iterations: int, algorithm: str = "sha-256") -> str:
    secret = hashlib.pbkdf2_hmac(algorithm, data.encode("utf-8"), solt, iterations).hex()
    return secret


class Secret:
    ITERATIONS: int = 1000
    CACHE = CacheTool(name="secret")

    @classmethod
    async def __get_solt(cls, data: str) -> bytes:
        solt = await cls.CACHE.get_data(data)
        if solt is None:
            solt = os.urandom(32)
            await cls.CACHE.set_data(data, solt)
        return solt

    @classmethod
    async def __create(cls, data: PydanticModel) -> str:
        data = data.model_dump_json()
        solt = await cls.__get_solt(data)
        secret = await generate_secret(data, solt, cls.ITERATIONS)
        return secret
    
    @classmethod
    async def create(cls, data: PydanticModel) -> str:
        return await cls.__create(data)

    @classmethod
    async def verify(cls, plain_secret: str, data: PydanticModel) -> bool:
        return plain_secret == (await cls.__create(data))