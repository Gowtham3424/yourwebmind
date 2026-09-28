"""Unit tests for the health check endpoint."""

from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.config import Settings, get_settings
from app.services.hindsight_service import HindsightService, get_hindsight_service


def test_health_unconfigured():
    """Verify health endpoint response when LLM is unconfigured."""
    test_settings = Settings(HINDSIGHT_API_LLM_API_KEY="", _env_file=None)
    mock_hindsight = MagicMock(spec=HindsightService)
    mock_hindsight.is_connected = False

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_hindsight_service] = lambda: mock_hindsight

    client = TestClient(app)
    response = client.get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "searchmind"
    assert data["status"] == "degraded"
    assert data["hindsight"] == "unconfigured"
    assert data["llm"] == "unconfigured"
    assert "HINDSIGHT_API_LLM_API_KEY" not in str(data)


def test_health_connected():
    """Verify health endpoint response when Hindsight is fully connected."""
    test_settings = Settings(
        HINDSIGHT_API_LLM_API_KEY="sk-secret-key",
        HINDSIGHT_API_LLM_PROVIDER="openai",
        _env_file=None,
    )
    mock_hindsight = MagicMock(spec=HindsightService)
    mock_hindsight.is_connected = True

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_hindsight_service] = lambda: mock_hindsight

    client = TestClient(app)
    response = client.get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "searchmind"
    assert data["status"] == "ok"
    assert data["hindsight"] == "connected"
    assert data["llm"] == "configured"
    assert data["provider"] == "openai"
    # Never leak secret keys
    assert "sk-secret-key" not in str(data)


def test_health_demo_mode():
    """Verify health endpoint response in explicit demo mode."""
    test_settings = Settings(
        SEARCHMIND_DEMO_MODE=True,
        HINDSIGHT_API_LLM_API_KEY="sk-secret-key",
        _env_file=None,
    )
    mock_hindsight = MagicMock(spec=HindsightService)
    mock_hindsight.is_connected = False

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_hindsight_service] = lambda: mock_hindsight

    client = TestClient(app)
    response = client.get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "searchmind"
    assert data["status"] == "ok"
    assert data["mode"] == "demo"
    assert data["hindsight_live"] is False
    assert data["llm_calls"] == 0
    assert data["hindsight"] == "offline"

