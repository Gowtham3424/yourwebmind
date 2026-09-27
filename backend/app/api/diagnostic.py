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
    return {
        "service": "searchmind",
        "environment": settings.ENVIRONMENT,
        "hindsight": {
            "initialized": hindsight.is_connected,
            "profile": settings.HINDSIGHT_PROFILE,
            "database_url": settings.HINDSIGHT_API_DATABASE_URL,
            "last_error": hindsight.last_error,
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
    return run_smoke_test()
