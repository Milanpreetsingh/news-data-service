import asyncpg
from typing import Optional
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.interfaces import IDatabase

class Database(IDatabase):
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def disconnect(self):
        if self.pool:
            await self.pool.close()
    
    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)
    
    async def execute(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    async def executemany(self, query: str, args):
        async with self.pool.acquire() as connection:
            return await connection.executemany(query, args)
    
    @asynccontextmanager
    async def transaction(self):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection

db = Database()
