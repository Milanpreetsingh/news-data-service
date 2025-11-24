from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.models.schemas import NewsResponse
from app.api.dependencies import get_current_user
from app.core.container import get_container, Container

# Create router for news endpoints with /news prefix
router = APIRouter(prefix="/news", tags=["News"])

@router.get("/category", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def get_news_by_category(
    category: str = Query(..., description="News category (e.g., Technology, Sports)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(5, ge=1, le=50, description="Items per page"),
    container: Container = Depends(get_container)
):
    """
    Get News by Category
    
    Authentication: Required (JWT token in Authorization header)
    
    Flow:
    1. Dependency get_current_user validates JWT token
    2. Get news_service from DI container
    3. Service queries ArticleRepository for articles in specified category
    4. LLM generates summaries for each article
    5. Return articles with summaries
    
    Pagination: Use page and limit parameters
    
    Example: GET /api/v1/news/category?category=Technology&page=1&limit=10
    """
    offset = (page - 1) * limit
    articles = await container.news_service.fetch_news(category=category, limit=limit, offset=offset)
    return {
        "articles": articles,
        "total": len(articles),
        "page": page,
        "page_size": limit,
        "query_info": {"category": category}
    }

@router.get("/score", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def get_news_by_score(
    min_score: float = Query(0.7, ge=0, le=1, description="Minimum relevance score"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(5, ge=1, le=50, description="Items per page"),
    container: Container = Depends(get_container)
):
    """
    Get News by Relevance Score
    
    Authentication: Required
    
    Flow:
    1. Filter articles with relevance_score >= min_score
    2. Order by relevance_score DESC (highest scores first)
    3. Generate LLM summaries
    4. Return filtered articles
    
    Pagination: Use page and limit parameters
    
    Use case: Get high-quality, relevant articles only
    
    Example: GET /api/v1/news/score?min_score=0.8&page=1&limit=5
    """
    offset = (page - 1) * limit
    articles = await container.news_service.fetch_news(min_score=min_score, limit=limit, offset=offset)
    return {
        "articles": articles,
        "total": len(articles),
        "page": page,
        "page_size": limit,
        "query_info": {"min_score": min_score}
    }

@router.get("/source", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def get_news_by_source(
    source_name: str = Query(..., description="News source name (e.g., Reuters, BBC)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(5, ge=1, le=50, description="Items per page"),
    container: Container = Depends(get_container)
):
    """
    Get News by Source Name
    
    Authentication: Required
    
    Flow:
    1. Search articles where source_name matches (case-insensitive partial match)
    2. Generate LLM summaries
    3. Return matching articles
    
    Use case: Get articles from specific news outlets
    
    Example: GET /api/v1/news/source?source_name=Reuters&page=1&limit=5
    """
    offset = (page - 1) * limit
    articles = await container.news_service.fetch_news(source_name=source_name, limit=limit, offset=offset)
    return {
        "articles": articles,
        "total": len(articles),
        "page": page,
        "page_size": limit,
        "query_info": {"source_name": source_name}
    }

@router.get("/search", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def search_news(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum relevance score"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(5, ge=1, le=50, description="Items per page"),
    container: Container = Depends(get_container)
):
    """
    Intelligent Search with LLM
    
    Authentication: Required
    
    Flow:
    1. Send query to Google Gemini for entity extraction
    2. LLM identifies entities, intent, and search terms
    3. Use extracted terms for PostgreSQL full-text search
    4. Optionally filter by category and min_score
    5. Rank results by text relevance (ts_rank)
    6. Generate summaries
    
    Pagination: Use page and limit parameters
    
    Use case: Natural language search (e.g., "latest AI developments")
    
    Example: GET /api/v1/news/search?query=climate+change&category=Science&page=1
    """
    offset = (page - 1) * limit
    articles = await container.news_service.search_news(
        query=query,
        category=category,
        min_score=min_score,
        limit=limit,
        offset=offset
    )
    return {
        "articles": articles,
        "total": len(articles),
        "page": page,
        "page_size": limit,
        "query_info": {"query": query, "category": category, "min_score": min_score}
    }

@router.get("/nearby", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def get_nearby_news(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(10.0, ge=1, le=100, description="Radius in kilometers"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(5, ge=1, le=50, description="Items per page"),
    container: Container = Depends(get_container)
):
    """
    Get Nearby News (Geospatial Search)
    
    Pagination: Use page and limit parameters
    
    Authentication: Required
    
    Flow:
    1. Use PostGIS ST_DWithin to find articles within radius
    2. Calculate distance from user's location
    3. Order by distance (closest first)
    4. Generate summaries
    
    Use case: "Show me news near my location"
    
    Technology: PostGIS geography type with Haversine distance
    
    Example: GET /api/v1/news/nearby?lat=37.7749&lon=-122.4194&radius=50&page=1
    """
    offset = (page - 1) * limit
    articles = await container.news_service.nearby_news(
        lat=lat,
        lon=lon,
        radius=radius,
        category=category,
        limit=limit,
        offset=offset
    )
    return {
        "articles": articles,
        "total": len(articles),
        "page": page,
        "page_size": limit,
        "query_info": {"lat": lat, "lon": lon, "radius": radius, "category": category}
    }

@router.get("", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def get_news_unified(
    category: Optional[str] = Query(None, description="News category"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum relevance score"),
    source_name: Optional[str] = Query(None, description="News source name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(5, ge=1, le=50, description="Items per page"),
    container: Container = Depends(get_container)
):
    """
    Unified News Endpoint (Multiple Filters)
    
    Pagination: Use page and limit parameters
    
    Authentication: Required
    
    Flow:
    1. Accept multiple optional filters
    2. Build dynamic WHERE clause based on provided parameters
    3. Apply all filters simultaneously
    4. Generate summaries
    
    Use case: Complex queries combining multiple criteria
    
    Example: GET /api/v1/news?category=Technology&min_score=0.7&source_name=BBC&page=1
    """
    offset = (page - 1) * limit
    articles = await container.news_service.fetch_news(
        category=category,
        min_score=min_score,
        source_name=source_name,
        limit=limit,
        offset=offset
    )
    return {
        "articles": articles,
        "total": len(articles),
        "page": page,
        "page_size": limit,
        "query_info": {
            "category": category,
            "min_score": min_score,
            "source_name": source_name
        }
    }
