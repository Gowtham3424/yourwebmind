"""Diagnostic API endpoint for SearchMind backend."""

from typing import Any, Dict
from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.services.hindsight_service import HindsightService, get_hindsight_service
from app.smoke_test import run_smoke_test

router = APIRouter(prefix="/api/v1", tags=["Diagnostics"])


@router.get("/diagnostic")
def get_diagnostics(
    settings: Settings = Depends(get_settings),
    hindsight: HindsightService = Depends(get_hindsight_service),
) -> Dict[str, Any]:
    """
    Development diagnostic endpoint to inspect Hindsight runtime and LLM configuration.

    Does not expose sensitive credentials.
    """
    is_demo = settings.SEARCHMIND_DEMO_MODE
    return {
        "service": "searchmind",
        "environment": settings.ENVIRONMENT,
        "mode": "demo" if is_demo else "live",
        "hindsight_live": False if is_demo else hindsight.is_connected,
        "llm_calls": 0,
        "hindsight": {
            "initialized": False if is_demo else hindsight.is_connected,
            "live": False if is_demo else hindsight.is_connected,
            "profile": settings.HINDSIGHT_PROFILE,
            "database_url": settings.HINDSIGHT_API_DATABASE_URL,
            "last_error": "Demo mode active (live Hindsight skipped)" if is_demo else hindsight.last_error,
        },
        "llm": {
            "configured": settings.is_llm_configured,
            "provider": settings.HINDSIGHT_API_LLM_PROVIDER,
            "model": settings.HINDSIGHT_API_LLM_MODEL,
            "base_url": settings.HINDSIGHT_API_LLM_BASE_URL,
        },
    }


@router.post("/diagnostic/smoke-test")
def trigger_smoke_test(
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Trigger the Retain -> Recall -> Reflect smoke test on the development server."""
    if settings.SEARCHMIND_DEMO_MODE:
        return {
            "status": "skipped",
            "message": "Smoke test skipped: SEARCHMIND_DEMO_MODE is active. Disable demo mode to run live smoke test.",
        }
    return run_smoke_test()
