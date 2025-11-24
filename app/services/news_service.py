from typing import Optional, List
import logging
from fastapi import HTTPException, status
from app.repositories.interfaces import IArticleRepository
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self, article_repository: IArticleRepository, llm_service: LLMService):
        self._article_repo = article_repository
        self._llm_service = llm_service
    
    async def fetch_news(
        self,
        category: Optional[str] = None,
        min_score: Optional[float] = None,
        source_name: Optional[str] = None,
        search_query: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[float] = None,
        limit: int = 5,
        offset: int = 0
    ):
        order_by = None
        if search_query:
            # For search: rank by text matching score (ts_rank) + relevance_score
            order_by = f"ts_rank(search_vector, plainto_tsquery('english', '{search_query}')) DESC, relevance_score DESC"
        elif min_score is not None:
            # For score filter: rank by relevance_score (highest first)
            order_by = "relevance_score DESC"
        elif lat is not None and lon is not None:
            # For nearby: rank by distance (closest first)
            order_by = f"ST_Distance(location, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography)"
        elif category is not None or source_name is not None:
            # For category and source: rank by publication_date (most recent first)
            order_by = "publication_date DESC NULLS LAST"
        
        try:
            articles = await self._article_repo.find_by_filters(
                category=category,
                min_score=min_score,
                source_name=source_name,
                search_query=search_query,
                lat=lat,
                lon=lon,
                radius=radius,
                limit=limit,
                offset=offset,
                order_by=order_by
            )
            
            if articles:
                try:
                    summaries = await self._llm_service.generate_summaries_batch(articles)
                    for article, summary in zip(articles, summaries):
                        article['llm_summary'] = summary
                except Exception as e:
                    logger.warning(f"LLM summary generation failed: {e}")
                    for article in articles:
                        article['llm_summary'] = "Summary unavailable."
            
            return articles
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in fetch_news: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve news"
            )
    
    async def search_news(
        self,
        query: str,
        category: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 5,
        offset: int = 0
    ):
        try:
            entities_data = await self._llm_service.extract_entities(query)
            search_terms = " ".join(entities_data.get("search_terms", [query]))
            
            return await self.fetch_news(
                search_query=search_terms,
                category=category,
                min_score=min_score,
                limit=limit,
                offset=offset
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_news: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search news"
            )
    
    async def nearby_news(
        self,
        lat: float,
        lon: float,
        radius: float = 10.0,
        category: Optional[str] = None,
        limit: int = 5,
        offset: int = 0
    ):
        return await self.fetch_news(
            lat=lat,
            lon=lon,
            radius=radius,
            category=category,
            limit=limit,
            offset=offset
        )
