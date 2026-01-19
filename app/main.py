"""
FastAPI Main Application Module
Plant Disease Detection LINE Chatbot
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from linebot.v3.exceptions import InvalidSignatureError

from app import __version__
from app.config import get_settings
from app.database.crud import db
from app.handlers.line_handler import line_handler
from app.models import ErrorResponse, HealthCheckResponse
from app.services.cache_service import cache_service
from app.services.gemini_service import gemini_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
settings = get_settings()

# Set log level based on settings
logging.getLogger().setLevel(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting Plant Disease Detection Chatbot v{__version__}")
    logger.info(f"Environment: {settings.environment}")

    try:
        # Connect to Redis
        await cache_service.connect()
        logger.info("Connected to Redis")

        # Initialize database
        await db.create_tables()
        logger.info("Database initialized")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        if settings.is_production:
            raise

    yield

    # Shutdown
    logger.info("Shutting down...")

    try:
        await cache_service.disconnect()
        await db.close()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="Plant Disease Detection Chatbot",
    description="LINE Chatbot for diagnosing plant diseases using AI Vision",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Middleware ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.3f}s"
    )

    return response


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID header for tracking."""
    import uuid

    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# ==================== Exception Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=str(exc.detail),
            detail=None
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="internal_server_error",
                message="An internal error occurred",
                detail=None
            ).model_dump()
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            message=str(exc),
            detail=repr(exc)
        ).model_dump()
    )


# ==================== Endpoints ====================

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "name": "Plant Disease Detection Chatbot",
        "version": __version__,
        "status": "running"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.

    Returns status of all services.
    """
    services = {}

    # Check Redis
    redis_healthy = await cache_service.health_check()
    services["redis"] = "healthy" if redis_healthy else "unhealthy"

    # Check Database
    db_healthy = await db.health_check()
    services["database"] = "healthy" if db_healthy else "unhealthy"

    # Check Gemini
    gemini_healthy = await gemini_service.health_check()
    services["gemini"] = "healthy" if gemini_healthy else "unhealthy"

    # Overall status
    all_healthy = all(s == "healthy" for s in services.values())
    status_str = "healthy" if all_healthy else "degraded"

    return HealthCheckResponse(
        status=status_str,
        version=__version__,
        timestamp=datetime.utcnow(),
        services=services
    )


@app.post("/webhook")
async def webhook(request: Request):
    """
    LINE webhook endpoint.

    Handles incoming LINE events.
    """
    # Get signature
    signature = request.headers.get("X-Line-Signature", "")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Line-Signature header"
        )

    # Get body
    body = await request.body()
    body_str = body.decode("utf-8")

    logger.info(f"Webhook received: {len(body_str)} bytes")

    try:
        line_handler.handle_webhook(body_str, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

    return {"status": "ok"}


@app.get("/stats")
async def get_statistics():
    """
    Get application statistics.

    Returns diagnosis statistics and cache stats.
    """
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stats endpoint disabled in production"
        )

    daily_stats = await db.get_daily_statistics()
    disease_dist = await db.get_disease_distribution(days=7)
    cache_stats = await cache_service.get_stats()

    return {
        "daily_statistics": daily_stats,
        "disease_distribution": disease_dist,
        "cache_stats": cache_stats
    }


# ==================== Development Endpoints ====================

if settings.is_development:

    @app.get("/debug/config")
    async def debug_config():
        """Get configuration (development only)."""
        return {
            "environment": settings.environment,
            "log_level": settings.log_level,
            "max_image_size_mb": settings.max_image_size_mb,
            "cache_expiry_hours": settings.cache_expiry_hours,
            "max_requests_per_hour": settings.max_requests_per_hour,
        }

    @app.post("/debug/clear-cache")
    async def debug_clear_cache(user_id: str):
        """Clear user cache (development only)."""
        await cache_service.clear_user_session(user_id)
        return {"status": "cleared", "user_id": user_id}


# ==================== Main Entry Point ====================

def main():
    """Run the application with Uvicorn."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        workers=1 if settings.is_development else 4,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
