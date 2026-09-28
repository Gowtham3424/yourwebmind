"""Integration tests for Hindsight Retain -> Recall -> Reflect lifecycle."""

import pytest
from app.config import get_settings
from app.services.hindsight_service import HindsightService
from app.smoke_test import run_smoke_test, SMOKE_TEST_BANK


@pytest.mark.integration
def test_hindsight_smoke_test_lifecycle():
    """
    Test the full Retain -> Recall -> Reflect loop against live Hindsight.

    Skipped if no live LLM API key is configured.
    """
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.is_llm_configured:
        pytest.skip("Skipping Hindsight integration test: HINDSIGHT_API_LLM_API_KEY is not configured.")
    if settings.SEARCHMIND_DEMO_MODE:
        pytest.skip("Skipping Hindsight integration test: SEARCHMIND_DEMO_MODE is active.")

    results = run_smoke_test(bank_id=SMOKE_TEST_BANK)

    assert results["hindsight_initialized"] is True, f"Init failed: {results.get('errors')}"
    assert results["retain_success"] is True, f"Retain failed: {results.get('errors')}"
    assert results["recall_success"] is True, f"Recall failed: {results.get('errors')}"
    assert results["reflect_success"] is True, f"Reflect failed: {results.get('errors')}"
    assert results["status"] == "success"
