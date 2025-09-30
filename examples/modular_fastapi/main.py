"""
Modular FastAPI Application Example.

Demonstrates best practices for structuring a FastAPI application:
- Modular architecture with routers
- Middleware configuration (CORS, error handling)
- Startup/shutdown lifecycle events
- Health check endpoint
"""

from contextlib import asynccontextmanager

from config import settings
from database import create_db_and_tables, engine
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from users.routes import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    print("Starting up application...")
    await create_db_and_tables()
    print("Database tables created")

    yield

    # Shutdown
    print("Shutting down application...")
    await engine.dispose()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Modular FastAPI Example",
    description="Example of a modular FastAPI application with SQLModel and async patterns",
    version="1.0.0",
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
        "version": "1.0.0",
        "database": "connected",
    }


# Include routers from domain modules
app.include_router(users_router, prefix="/users", tags=["users"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
