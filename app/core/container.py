from functools import lru_cache
from app.core.database import db
from app.core.redis import cache
from app.repositories.user_repository import UserRepository
from app.repositories.article_repository import ArticleRepository
from app.repositories.event_repository import EventRepository
from app.services.auth_service import AuthService
from app.services.news_service import NewsService
from app.services.trending_service import TrendingService
from app.services.llm_service import LLMService

class Container:
    def __init__(self):
        self._user_repository = None
        self._article_repository = None
        self._event_repository = None
        self._auth_service = None
        self._news_service = None
        self._trending_service = None
        self._llm_service = None
    
    @property
    def user_repository(self) -> UserRepository:
        if self._user_repository is None:
            self._user_repository = UserRepository(db)
        return self._user_repository
    
    @property
    def article_repository(self) -> ArticleRepository:
        if self._article_repository is None:
            self._article_repository = ArticleRepository(db)
        return self._article_repository
    
    @property
    def event_repository(self) -> EventRepository:
        if self._event_repository is None:
            self._event_repository = EventRepository(db)
        return self._event_repository
    
    @property
    def llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service
    
    @property
    def auth_service(self) -> AuthService:
        if self._auth_service is None:
            self._auth_service = AuthService(self.user_repository)
        return self._auth_service
    
    @property
    def news_service(self) -> NewsService:
        if self._news_service is None:
            self._news_service = NewsService(
                self.article_repository,
                self.llm_service
            )
        return self._news_service
    
    @property
    def trending_service(self) -> TrendingService:
        if self._trending_service is None:
            self._trending_service = TrendingService(
                self.event_repository,
                self.article_repository,
                cache,
                self.llm_service
            )
        return self._trending_service

@lru_cache()
def get_container() -> Container:
    return Container()
