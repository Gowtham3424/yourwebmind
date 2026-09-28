"""Health check endpoint for SearchMind backend."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.services.hindsight_service import HindsightService, get_hindsight_service

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Structured health check response."""

    status: str = Field(..., description="Overall service status (ok, degraded)")
    service: str = Field(default="searchmind", description="Service identifier")
    hindsight: str = Field(..., description="Hindsight memory engine status (connected, disconnected, unconfigured, offline)")
    llm: str = Field(..., description="LLM provider configuration status (configured, unconfigured)")
    provider: Optional[str] = Field(None, description="Configured LLM provider name without exposing secrets")
    mode: Optional[str] = Field(None, description="Operating mode: demo or live")
    hindsight_live: Optional[bool] = Field(None, description="Whether live Hindsight daemon is active")
    llm_calls: Optional[int] = Field(None, description="Count of external LLM API calls made")


@router.get("/health", response_model=HealthResponse)
def get_health(
    settings: Settings = Depends(get_settings),
    hindsight: HindsightService = Depends(get_hindsight_service),
) -> HealthResponse:
    """
    Check the health of SearchMind service and Hindsight memory engine connection.

    Does not make expensive LLM calls.
    """
    llm_status = "configured" if settings.is_llm_configured else "unconfigured"

    if settings.SEARCHMIND_DEMO_MODE:
        return HealthResponse(
            status="ok",
            service="searchmind",
            hindsight="offline",
            llm=llm_status,
            provider=settings.HINDSIGHT_API_LLM_PROVIDER,
            mode="demo",
            hindsight_live=False,
            llm_calls=0,
        )

    if hindsight.is_connected:
        hindsight_status = "connected"
    elif not settings.is_llm_configured:
        hindsight_status = "unconfigured"
    else:
        hindsight_status = "disconnected"

    # Overall system status
    overall_status = "ok" if hindsight_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        service="searchmind",
        hindsight=hindsight_status,
        llm=llm_status,
        provider=settings.HINDSIGHT_API_LLM_PROVIDER,
        mode="live",
        hindsight_live=hindsight.is_connected,
        llm_calls=0,
    )
