import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

class RedisCache:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        self.client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        if self.client:
            await self.client.close()
    
    async def get(self, key: str):
        return await self.client.get(key)
    
    async def set(self, key: str, value: str, ex: int = 300):
        return await self.client.set(key, value, ex=ex)
    
    async def delete(self, key: str):
        return await self.client.delete(key)

cache = RedisCache()
