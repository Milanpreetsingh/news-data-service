from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncpg
import logging
from fastapi import HTTPException, status
from app.core.interfaces import IDatabase
from app.repositories.interfaces import IEventRepository

logger = logging.getLogger(__name__)

class EventRepository(IEventRepository):
    def __init__(self, db: IDatabase):
        self._db = db
    
    async def create_event(
        self,
        user_id: UUID,
        article_id: UUID,
        event_type: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> None:
        try:
            if lat is not None and lon is not None:
                await self._db.execute(
                    """
                    INSERT INTO user_events (user_id, article_id, event_type, location)
                    VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326)::geography)
                    """,
                    user_id, article_id, event_type, lon, lat
                )
            else:
                await self._db.execute(
                    """
                    INSERT INTO user_events (user_id, article_id, event_type)
                    VALUES ($1, $2, $3)
                    """,
                    user_id, article_id, event_type
                )
        except asyncpg.ForeignKeyViolationError:
            logger.error(f"Invalid user_id or article_id: {user_id}, {article_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User or article not found"
            )
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in create_event: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create event"
            )
    
    async def create_events_batch(self, events: List[Dict[str, Any]]) -> None:
        args = []
        for event in events:
            lat = event.get('lat')
            lon = event.get('lon')
            if lat is not None and lon is not None:
                args.append((
                    event['user_id'],
                    event['article_id'],
                    event['event_type'],
                    lon,
                    lat
                ))
        
        if args:
            try:
                await self._db.executemany(
                    """
                    INSERT INTO user_events (user_id, article_id, event_type, user_lat, user_lon)
                    VALUES ($1, $2, $3, $5, $4)
                    """,
                    args
                )
            except asyncpg.PostgresError as e:
                logger.error(f"Database error in create_events_batch: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create events batch"
                )
    
    async def get_trending_articles(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius: Optional[float] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        location_filter = ""
        params = []
        
        if lat is not None and lon is not None and radius:
            location_filter = """
                AND ST_DWithin(
                    ue.user_location,
                    ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                    $3
                )
            """
            params = [lon, lat, radius * 1000]
        
        query = f"""
            WITH event_stats AS (
                SELECT 
                    ue.article_id,
                    COUNT(CASE WHEN ue.event_type = 'view' THEN 1 END) as views,
                    COUNT(CASE WHEN ue.event_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN ue.event_type = 'share' THEN 1 END) as shares,
                    MAX(ue.created_at) as latest_event,
                    AVG(
                        CASE 
                            WHEN {'' if not params else f'ST_Distance(ue.user_location, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography) > 0 THEN'}
                            {'' if not params else f'1.0 / (1.0 + ST_Distance(ue.user_location, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography) / 1000.0)'}
                            {'1.0' if not params else 'ELSE 1.0'}
                            END
                    ) as avg_proximity
                FROM user_events ue
                WHERE ue.created_at > NOW() - INTERVAL '48 hours'
                {location_filter}
                GROUP BY ue.article_id
            ),
            trending_scores AS (
                SELECT 
                    es.article_id,
                    (
                        (es.views * 1.0 + es.clicks * 3.0 + es.shares * 5.0) *
                        (1.0 / (1.0 + EXTRACT(EPOCH FROM (NOW() - es.latest_event)) / 3600.0)) *
                        COALESCE(es.avg_proximity, 1.0)
                    ) as trending_score
                FROM event_stats es
            )
            SELECT 
                a.title, a.description, a.url, a.publication_date,
                a.source_name, a.category, a.relevance_score,
                ST_Y(a.location::geometry) as latitude,
                ST_X(a.location::geometry) as longitude,
                ts.trending_score
            FROM articles a
            JOIN trending_scores ts ON a.id = ts.article_id
            ORDER BY ts.trending_score DESC
            LIMIT {limit}
        """
        
        try:
            rows = await self._db.fetch(query, *params)
            return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in get_trending_articles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve trending articles"
            )
