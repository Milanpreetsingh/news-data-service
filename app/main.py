from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from app.core.database import db
from app.core.redis import cache
from app.api.routes import auth, news, trending

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager handles application startup and shutdown.
    - Runs once when server starts (before yield)
    - Runs once when server stops (after yield)
    This ensures proper resource management for database and cache connections.
    """
    # STARTUP: Establish database and Redis connections
    try:
        await db.connect()
        await cache.connect()
        logger.info("Database and Redis connections established")
    except Exception as e:
        logger.error(f"Failed to connect to database or Redis: {e}")
        raise
    
    # Application is running - yield control back to FastAPI
    yield
    
    # SHUTDOWN: Close database and Redis connections gracefully
    try:
        await db.disconnect()
        await cache.disconnect()
        logger.info("Database and Redis connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application instance
app = FastAPI(
    title="News Data Service API",
    description="Contextual news retrieval system with LLM-powered insights",
    version="1.0.0",
    lifespan=lifespan  # Attach lifespan manager for startup/shutdown
)

# Add CORS middleware to allow cross-origin requests
# This enables frontend apps from different domains to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins (use specific domains in production)
    allow_credentials=True,        # Allow cookies to be sent with requests
    allow_methods=["*"],           # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],           # Allow all headers (Authorization, Content-Type, etc.)
)

# Register route modules with /api/v1 prefix
# Each router handles a specific domain (auth, news, trending)
app.include_router(auth.router, prefix="/api/v1")       # Authentication endpoints
app.include_router(news.router, prefix="/api/v1")       # News retrieval endpoints
app.include_router(trending.router, prefix="/api/v1")   # Trending news endpoints

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error for {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred"}
    )

@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.
    Accessible without authentication.
    """
    return {
        "message": "News Data Service API",
        "version": "1.0.0",
        "docs": "/docs",       # Swagger UI documentation
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint - used by monitoring tools and load balancers.
    Returns 200 OK if the server is running.
    """
    return {"status": "healthy"}
