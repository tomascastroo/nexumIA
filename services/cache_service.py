import os
import redis.asyncio as aioredis
import asyncio
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

class RedisCache:
    """
    Servicio de caching Redis asíncrono para Nexum IA.
    Métodos: get, set, delete, invalidate_pattern.
    Uso recomendado: await RedisCache.get_instance().set(...)
    """
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.redis = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = RedisCache()
                    await cls._instance._init()
        return cls._instance

    async def _init(self):
        redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        kwargs = {"encoding": "utf-8", "decode_responses": True}
        if REDIS_PASSWORD not in (None, "", "null", "None"):
            kwargs["password"] = REDIS_PASSWORD
        self.redis = await aioredis.from_url(redis_url, **kwargs)

    async def get(self, key: str) -> Optional[Any]:
        if self.redis is None:
            raise RuntimeError("Redis connection is not initialized.")
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        if self.redis is None:
            raise RuntimeError("Redis connection is not initialized.")
        await self.redis.set(key, value, ex=ttl)

    async def delete(self, key: str):
        if self.redis is None:
            raise RuntimeError("Redis connection is not initialized.")
        await self.redis.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Elimina todas las keys que matchean el patrón (ej: 'debtors:*')"""
        if self.redis is None:
            raise RuntimeError("Redis connection is not initialized.")
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key) 