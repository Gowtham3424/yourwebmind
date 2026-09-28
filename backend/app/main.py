"""Main FastAPI application entrypoint for YourWebMind."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.agent import router as agent_router
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
    logger.info("=== Starting YourWebMind Backend ===")

    if settings.SEARCHMIND_DEMO_MODE:
        logger.info(
            "SEARCHMIND_DEMO_MODE is active. Skipping live Hindsight Embedded daemon initialization "
            "and external LLM provider calls. Operating in deterministic offline evaluator mode."
        )
        yield
        logger.info("=== Shutting down YourWebMind Backend (Demo Mode) ===")
        return

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

    logger.info("=== Shutting down YourWebMind Backend ===")
    hindsight.shutdown()
    logger.info("YourWebMind shutdown complete.")


app = FastAPI(
    title="SearchMind API",
    description="An SEO agent that remembers what happened, learns what worked, and gets smarter over time.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(diagnostic_router)
app.include_router(agent_router)

# Mount static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def get_root(request: Request):
    """Service root endpoint: serves HTML UI for browser requests, JSON for API requests."""
    accept = request.headers.get("accept", "")
    index_file = STATIC_DIR / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(index_file)
    return {
        "service": "YourWebMind API",
        "tagline": "An SEO agent that remembers what happened, learns from outcomes, and gets smarter over time.",
        "version": "0.1.0",
        "health_check": "/health",
        "docs": "/docs",
        "ui": "/app",
    }


@app.get("/app")
def get_app():
    """Direct route to YourWebMind workspace interface."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Frontend static assets not found"}
