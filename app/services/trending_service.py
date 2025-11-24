import json
import random
from typing import List, Optional
import logging
import geohash2
from fastapi import HTTPException, status
from app.repositories.interfaces import IArticleRepository, IEventRepository
from app.core.redis import RedisCache
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class TrendingService:
    def __init__(
        self, 
        event_repository: IEventRepository,
        article_repository: IArticleRepository,
        cache: RedisCache,
        llm_service: LLMService
    ):
        self._event_repo = event_repository
        self._article_repo = article_repository
        self._cache = cache
        self._llm_service = llm_service
    
    async def generate_simulated_events(self, num_events: int = 500, user_id: str = None):
        articles = await self._article_repo.find_all()
        
        if not articles:
            return
        
        event_types = ['view', 'click', 'share']
        event_weights = [0.7, 0.25, 0.05]
        
        events = []
        for _ in range(num_events):
            article = random.choice(articles[:100])
            event_type = random.choices(event_types, weights=event_weights)[0]
            
            # Generate random coordinates (global distribution)
            # Focus more events around major cities for better trending results
            city_coords = [
                (37.7749, -122.4194),  # San Francisco
                (40.7128, -74.0060),   # New York
                (34.0522, -118.2437),  # Los Angeles
                (51.5074, -0.1278),    # London
                (19.0760, 72.8777),    # Mumbai
                (28.7041, 77.1025),    # Delhi
            ]
            
            # 70% chance of event near a major city, 30% random
            if random.random() < 0.7:
                base_lat, base_lon = random.choice(city_coords)
                # Add noise within ~50km radius
                lat = base_lat + random.uniform(-0.5, 0.5)
                lon = base_lon + random.uniform(-0.5, 0.5)
            else:
                # Random global coordinates
                lat = random.uniform(-90, 90)
                lon = random.uniform(-180, 180)
            
            events.append({
                'user_id': user_id,  # Use the authenticated user's ID
                'article_id': article['id'],
                'event_type': event_type,
                'lat': lat,
                'lon': lon
            })
        
        try:
            await self._event_repo.create_events_batch(events)
            logger.info(f"Generated {num_events} simulated events")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate simulated events: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate simulated events"
            )
    
    async def get_trending_news(
        self,
        lat: float,
        lon: float,
        radius: float = 50.0,
        limit: int = 10
    ):
        cache_key = self._get_cache_key(lat, lon, limit)
        
        try:
            cached_data = await self._cache.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for trending news: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
        
        try:
            result = await self._event_repo.get_trending_articles(
                lat=lat,
                lon=lon,
                radius=radius,
                limit=limit
            )
            
            if result:
                try:
                    summaries = await self._llm_service.generate_summaries_batch(result)
                    for article, summary in zip(result, summaries):
                        article['llm_summary'] = summary
                except Exception as e:
                    logger.warning(f"LLM summary generation failed for trending: {e}")
                    for article in result:
                        article['llm_summary'] = "Summary unavailable."
            
            try:
                await self._cache.set(cache_key, json.dumps(result, default=str), ex=300)
                logger.info(f"Cached trending news: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get trending news: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve trending news"
            )
    
    def _get_cache_key(self, lat: float, lon: float, limit: int, precision: int = 5) -> str:
        gh = geohash2.encode(lat, lon, precision=precision)
        return f"trending:{gh}:limit{limit}"
