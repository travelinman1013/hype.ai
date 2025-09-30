"""
HypeAI FastAPI Application.

Main application entry point that integrates all modules.
"""

import logging
from contextlib import asynccontextmanager

# Import routers
from auth.routes import router as auth_router
from config import settings
from database import create_db_and_tables, engine
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from heartrate.routes import router as heartrate_router
from music.routes import router as music_router
from users.routes import router as users_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting up HypeAI application...")
    await create_db_and_tables()
    logger.info("Database tables created successfully")

    yield

    # Shutdown
    logger.info("Shutting down HypeAI application...")
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="HypeAI - Bio-Responsive Music Streaming",
    description="Backend service that syncs real-time heart rate with Spotify for adaptive workout playlists",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all uncaught exceptions.

    Args:
        request: HTTP request
        exc: Exception raised

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else None,
        },
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "hypeai",
        "version": "0.1.0",
        "environment": settings.environment,
    }


# Include routers from domain modules
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(heartrate_router, tags=["heartrate"])
app.include_router(music_router, prefix="/music", tags=["music"])
app.include_router(users_router, prefix="/users", tags=["users"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
