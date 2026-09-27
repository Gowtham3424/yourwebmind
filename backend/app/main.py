"""Main FastAPI application entrypoint for SearchMind."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.diagnostic import router as diagnostic_router
from app.api.health import router as health_router
from app.config import get_settings
from app.services.hindsight_service import get_hindsight_service

# Configure root logger
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("searchmind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager handling startup and shutdown of Hindsight."""
    logger.info("=== Starting SearchMind Backend ===")
    hindsight = get_hindsight_service()

    if settings.is_llm_configured:
        logger.info("LLM configured. Initializing persistent Hindsight memory engine...")
        success = hindsight.initialize()
        if success:
            logger.info("Hindsight memory engine active and ready.")
        else:
            logger.warning(f"Hindsight failed to initialize: {hindsight.last_error}")
    else:
        logger.warning(
            "HINDSIGHT_API_LLM_API_KEY is not set. Memory features are unconfigured. "
            "Please configure your LLM API key in .env to enable Retain, Recall, and Reflect."
        )

    yield

    logger.info("=== Shutting down SearchMind Backend ===")
    hindsight.shutdown()
    logger.info("SearchMind shutdown complete.")


app = FastAPI(
    title="SearchMind API",
    description="An SEO agent that remembers what happened, learns what worked, and gets smarter over time.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(diagnostic_router)


@app.get("/")
def get_root():
    """Service root endpoint."""
    return {
        "service": "SearchMind API",
        "tagline": "An SEO agent that remembers what happened, learns what worked, and gets smarter over time.",
        "version": "0.1.0",
        "health_check": "/health",
        "docs": "/docs",
    }
