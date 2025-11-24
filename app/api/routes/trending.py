from fastapi import APIRouter, Depends, Query, HTTPException
from app.models.schemas import NewsResponse
from app.api.dependencies import get_current_user
from app.core.container import get_container, Container

# Create router for trending endpoints with /news prefix
# Note: These endpoints are under /news because they return news articles
router = APIRouter(prefix="/news", tags=["Trending"])

@router.get("/trending", response_model=NewsResponse, dependencies=[Depends(get_current_user)])
async def get_trending_news(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    limit: int = Query(10, ge=1, le=50),
    container: Container = Depends(get_container)
):
    """
    Get Trending News by Location
    
    Authentication: Required
    
    Flow:
    1. Check Redis cache using geohash-based key (5-minute TTL)
    2. If cache miss, calculate trending score from database
    3. Trending score formula:
       (engagement_weight × recency_weight × proximity_weight)
       
       - engagement_weight: view=1, click=3, share=5
       - recency_weight: 1/(1 + hours_since_event)
       - proximity_weight: 1/(1 + distance_km)
    
    4. Filter events from last 24 hours
    5. Filter by location radius
    6. Order by trending_score DESC
    7. Cache result for 5 minutes
    8. Return trending articles
    
    Use case: "What's trending near me right now?"
    
    Technology: PostGIS for geospatial, Redis for caching, Geohash for clustering
    
    Example: GET /api/v1/news/trending?lat=37.7749&lon=-122.4194&limit=10
    """
    articles = await container.trending_service.get_trending_news(lat=lat, lon=lon, limit=limit)
    
    # If no trending data found, suggest running simulation
    if not articles:
        raise HTTPException(
            status_code=404,
            detail="No trending articles found for this location. Try running the event simulation first."
        )
    
    return {
        "articles": articles,
        "total": len(articles),
        "query_info": {"lat": lat, "lon": lon, "trending": True}
    }

@router.post("/trending/simulate-events")
async def simulate_user_events(
    num_events: int = Query(500, ge=100, le=5000),
    current_user: dict = Depends(get_current_user),
    container: Container = Depends(get_container)
):
    """
    Simulate User Events for Testing
    
    Authentication: Required
    
    Flow:
    1. Select random articles from database (first 100)
    2. Generate random events with weighted distribution:
       - 70% views
       - 25% clicks
       - 5% shares
    3. Insert events into user_events table
    4. Events are timestamped within last 48 hours
    
    Use case: Generate fake user engagement data to test trending algorithm
    
    Note: In production, events would come from real user interactions
    (e.g., tracking pixel, click events, share buttons)
    
    Example: POST /api/v1/news/trending/simulate-events?num_events=1000
    """
    await container.trending_service.generate_simulated_events(num_events, current_user['id'])
    return {
        "message": f"Successfully generated {num_events} simulated user events",
        "status": "success"
    }
