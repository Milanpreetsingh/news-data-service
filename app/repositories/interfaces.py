from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

class IUserRepository(ABC):
    @abstractmethod
    async def create(self, email: str, username: str, hashed_password: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def exists_by_email_or_username(self, email: str, username: str) -> bool:
        pass

class IArticleRepository(ABC):
    @abstractmethod
    async def find_by_filters(
        self,
        category: Optional[str] = None,
        min_score: Optional[float] = None,
        source_name: Optional[str] = None,
        search_query: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[float] = None,
        limit: int = 5,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def count_by_filters(
        self,
        category: Optional[str] = None,
        min_score: Optional[float] = None,
        source_name: Optional[str] = None,
        search_query: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[float] = None
    ) -> int:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Dict[str, Any]]:
        pass

class IEventRepository(ABC):
    @abstractmethod
    async def create_event(
        self,
        user_id: UUID,
        article_id: UUID,
        event_type: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> None:
        pass
    
    @abstractmethod
    async def create_events_batch(self, events: List[Dict[str, Any]]) -> None:
        pass
    
    @abstractmethod
    async def get_trending_articles(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[float] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        pass
