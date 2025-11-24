from typing import Optional, List, Dict, Any
import asyncpg
import logging
from fastapi import HTTPException, status
from app.core.interfaces import IDatabase
from app.repositories.interfaces import IArticleRepository

logger = logging.getLogger(__name__)

class ArticleRepository(IArticleRepository):
    def __init__(self, db: IDatabase):
        self._db = db
    
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
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        param_count = 1
        
        if category:
            conditions.append(f"${param_count} = ANY(category)")
            params.append(category)
            param_count += 1
        
        if min_score is not None:
            conditions.append(f"relevance_score >= ${param_count}")
            params.append(min_score)
            param_count += 1
        
        if source_name:
            conditions.append(f"source_name ILIKE ${param_count}")
            params.append(f"%{source_name}%")
            param_count += 1
        
        if search_query:
            conditions.append(f"search_vector @@ plainto_tsquery('english', ${param_count})")
            params.append(search_query)
            param_count += 1
        
        if lat is not None and lon is not None and radius:
            conditions.append(
                f"ST_DWithin(location, ST_SetSRID(ST_MakePoint(${param_count}, ${param_count + 1}), 4326)::geography, ${param_count + 2})"
            )
            params.extend([lon, lat, radius * 1000])
            param_count += 3
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        # Default ordering if not specified
        if not order_by:
            if search_query:
                # Search: rank by text matching score
                order_by = f"ts_rank(search_vector, plainto_tsquery('english', '{search_query}')) DESC"
            elif lat is not None and lon is not None:
                # Nearby: rank by distance (closest first)
                order_by = f"ST_Distance(location, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography)"
            else:
                # Default: rank by publication date (most recent first)
                order_by = "publication_date DESC NULLS LAST"
        
        query = f"""
            SELECT 
                title, description, url, publication_date,
                source_name, category, relevance_score,
                ST_Y(location::geometry) as latitude,
                ST_X(location::geometry) as longitude
            FROM articles
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT {limit}
            OFFSET {offset}
        """

        try:
            rows = await self._db.fetch(query, *params)
            return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in find_by_filters: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database query failed"
            )
        except Exception as e:
            logger.error(f"Unexpected error in find_by_filters: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve articles"
            )
    
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
        conditions = []
        params = []
        param_count = 1
        
        if category:
            conditions.append(f"${param_count} = ANY(category)")
            params.append(category)
            param_count += 1
        
        if min_score is not None:
            conditions.append(f"relevance_score >= ${param_count}")
            params.append(min_score)
            param_count += 1
        
        if source_name:
            conditions.append(f"source_name ILIKE ${param_count}")
            params.append(f"%{source_name}%")
            param_count += 1
        
        if search_query:
            conditions.append(f"search_vector @@ plainto_tsquery('english', ${param_count})")
            params.append(search_query)
            param_count += 1
        
        if lat is not None and lon is not None and radius:
            conditions.append(
                f"ST_DWithin(location, ST_SetSRID(ST_MakePoint(${param_count}, ${param_count + 1}), 4326)::geography, ${param_count + 2})"
            )
            params.extend([lon, lat, radius * 1000])
            param_count += 3
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"SELECT COUNT(*) as count FROM articles WHERE {where_clause}"
        
        try:
            result = await self._db.fetchrow(query, *params)
            return result['count']
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in count_by_filters: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database query failed"
            )
    
    async def find_all(self) -> List[Dict[str, Any]]:
        try:
            rows = await self._db.fetch("SELECT id FROM articles")
            return [dict(row) for row in rows]
        except asyncpg.PostgresError as e:
            logger.error(f"Database error in find_all: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database query failed"
            )
