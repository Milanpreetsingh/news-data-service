from abc import ABC, abstractmethod
from typing import Optional, List, Any
import asyncpg

class IDatabase(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        pass
    
    @abstractmethod
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        pass
    
    @abstractmethod
    async def execute(self, query: str, *args) -> str:
        pass
    
    @abstractmethod
    async def executemany(self, query: str, args: List) -> None:
        pass
    
    @abstractmethod
    async def transaction(self):
        pass
