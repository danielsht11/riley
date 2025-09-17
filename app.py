"""
Voice Agent FastAPI Application

Main FastAPI application for the voice agent system.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config.logging_config import setup_logging
from api.routes.customer_routes import router as customer_router
from api.routes.twilio_routes import router as twilio_router
from api.routes.onboarding import router as onboarding_router  # noqa: F401
from infrastructure.redis.redis_client import redis_client
from infrastructure.database import init_db, shutdown_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging(level="INFO")
    await redis_client.connect()
    await init_db()
    yield
    # Shutdown
    await redis_client.disconnect()
    await shutdown_db()

# Create FastAPI app
app = FastAPI(
    title="Voice Agent API",
    description="API for voice agent system with customer management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customer_router)
app.include_router(twilio_router)
app.include_router(onboarding_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = await redis_client.health_check()
    return {
        "status": "healthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "services": {
            "api": "running",
            "redis": "connected" if redis_healthy else "disconnected"
        }
    }



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": request.url.path
        }
    )
