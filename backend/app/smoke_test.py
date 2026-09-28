"""Diagnostic and smoke-test runner for Hindsight Retain -> Recall -> Reflect loop.

Can be run directly via:
    python -m app.smoke_test
"""

import json
import logging
import sys
import time
from typing import Any, Dict

from app.config import get_settings
from app.services.hindsight_service import get_hindsight_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("searchmind.smoke_test")

SMOKE_TEST_BANK = "searchmind-live-test"
SMOKE_TEST_CONTENT = (
    "SearchMind smoke test memory. The SEO team tested a title optimization on a commercial product page."
)
SMOKE_TEST_RECALL_QUERY = "What did the SEO team test on the commercial product page?"
SMOKE_TEST_REFLECT_QUERY = "What is known about title optimization tests on commercial product pages?"


def ensure_groq_capacity(settings, min_tokens: int = 6000, max_wait: int = 120) -> None:
    """Ensure Groq TPM token capacity has recovered to at least min_tokens before making API calls."""
    if settings.HINDSIGHT_API_LLM_PROVIDER.lower() != "groq":
        return
    import httpx, re
    logger.info(f"Checking Groq capacity (ensuring at least {min_tokens} tokens)...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.HINDSIGHT_API_LLM_API_KEY}"},
                json={"model": settings.HINDSIGHT_API_LLM_MODEL, "messages": [{"role": "user", "content": "1"}], "service_tier": "on_demand"},
                timeout=10,
            )
            rem = int(r.headers.get("x-ratelimit-remaining-tokens", 0))
            reset_header = r.headers.get("x-ratelimit-reset-tokens", "")
            logger.info(f"Groq capacity: {rem}/{min_tokens} tokens available (reset in {reset_header})")
            if rem >= min_tokens:
                return
            match = re.search(r"([0-9.]+)", reset_header)
            wait_sec = float(match.group(1)) + 2.0 if match else 15.0
            wait_sec = min(max(wait_sec, 5.0), 30.0)
            logger.info(f"Pausing {wait_sec:.1f}s for Groq tokens to replenish...")
            time.sleep(wait_sec)
        except Exception as e:
            logger.debug(f"Quota check error: {e}")
            time.sleep(5)


def run_smoke_test(bank_id: str = SMOKE_TEST_BANK, cleanup: bool = False) -> Dict[str, Any]:
    """
    Execute the Retain -> Recall -> Reflect smoke test against Hindsight.

    Returns a structured dictionary with diagnostics for each phase.
    """
    settings = get_settings()
    results: Dict[str, Any] = {
        "status": "pending",
        "hindsight_initialized": False,
        "llm_configured": settings.is_llm_configured,
        "llm_provider": settings.HINDSIGHT_API_LLM_PROVIDER,
        "llm_model": settings.HINDSIGHT_API_LLM_MODEL,
        "memory_bank": bank_id,
        "retain_success": False,
        "recall_success": False,
        "reflect_success": False,
        "details": {},
        "errors": [],
    }

    if not settings.is_llm_configured:
        err = "LLM API key is not configured. Set HINDSIGHT_API_LLM_API_KEY in .env to run smoke test."
        logger.error(err)
        results["status"] = "failed"
        results["errors"].append(err)
        return results

    service = get_hindsight_service()

    # Step 1: Initialize Hindsight
    logger.info("Step 1/4: Initializing Hindsight Embedded daemon...")
    t0 = time.time()
    try:
        init_ok = service.initialize()
        if not init_ok or not service.is_connected:
            err = f"Failed to initialize Hindsight runtime: {service.last_error}"
            logger.error(err)
            results["status"] = "failed"
            results["errors"].append(err)
            return results

        results["hindsight_initialized"] = True
        results["details"]["init_time_seconds"] = round(time.time() - t0, 3)
        logger.info(f"Hindsight initialized in {results['details']['init_time_seconds']}s")
    except Exception as exc:
        logger.exception("Initialization exception")
        results["status"] = "failed"
        results["errors"].append(f"Init exception: {exc}")
        return results

    # Optional pre-cleanup to keep prompt size minimal (isolated test bank only)
    try:
        service.get_client().delete_bank(bank_id)
    except Exception:
        pass

    # Ensure Groq has sufficient capacity before retain (skipped for Gemini)
    ensure_groq_capacity(settings, min_tokens=5500)

    is_groq = settings.HINDSIGHT_API_LLM_PROVIDER.lower() == "groq"
    retain_attempts = 3 if is_groq else 1

    # Step 2: Retain
    logger.info(f"Step 2/4: Retaining smoke-test memory in bank '{bank_id}'...")
    for attempt in range(1, retain_attempts + 1):
        t0 = time.time()
        try:
            retain_resp = service.retain(
                bank_id=bank_id,
                content=SMOKE_TEST_CONTENT,
                metadata={"source": "smoke_test", "topic": "seo_title_optimization"},
                tags=["smoke_test", "commercial", "title_optimization"],
            )
            results["retain_success"] = True
            results["details"]["retain_time_seconds"] = round(time.time() - t0, 3)
            results["details"]["retain_response"] = str(retain_resp)
            logger.info(f"Retain completed in {results['details']['retain_time_seconds']}s")
            break
        except Exception as exc:
            err_str = str(exc)
            if is_groq and ("429" in err_str or "Rate limit" in err_str or "quota" in err_str.lower()) and attempt < retain_attempts:
                wait_sec = 20 * attempt
                logger.warning(
                    f"Retain hit rate limit on attempt {attempt}/{retain_attempts}. "
                    f"Waiting {wait_sec}s for token bucket replenishment before retrying..."
                )
                time.sleep(wait_sec)
            else:
                logger.exception("Retain exception")
                results["errors"].append(f"Retain exception: {exc}")
                results["status"] = "failed"
                return results

    # Step 3: Recall
    logger.info(f"Step 3/4: Recalling memories from bank '{bank_id}' with query '{SMOKE_TEST_RECALL_QUERY}'...")
    t0 = time.time()
    try:
        recall_resp = service.recall(
            bank_id=bank_id,
            query=SMOKE_TEST_RECALL_QUERY,
            budget="mid",
        )
        results["recall_success"] = True
        results["details"]["recall_time_seconds"] = round(time.time() - t0, 3)
        results["details"]["recall_results_count"] = (
            len(recall_resp.results) if hasattr(recall_resp, "results") and recall_resp.results else 0
        )
        logger.info(
            f"Recall completed in {results['details']['recall_time_seconds']}s "
            f"(found {results['details']['recall_results_count']} results)"
        )
    except Exception as exc:
        logger.exception("Recall exception")
        results["errors"].append(f"Recall exception: {exc}")
        results["status"] = "failed"
        return results

    # Ensure Groq token bucket has recovered before Reflect (skipped for Gemini)
    ensure_groq_capacity(settings, min_tokens=5500)

    reflect_attempts = 3 if is_groq else 1

    # Step 4: Reflect
    logger.info(f"Step 4/4: Reflecting over memories in bank '{bank_id}' with query '{SMOKE_TEST_REFLECT_QUERY}'...")
    for attempt in range(1, reflect_attempts + 1):
        t0 = time.time()
        try:
            reflect_resp = service.reflect(
                bank_id=bank_id,
                query=SMOKE_TEST_REFLECT_QUERY,
                budget="low",
                include_facts=False,
            )
            results["reflect_success"] = True
            results["details"]["reflect_time_seconds"] = round(time.time() - t0, 3)
            # Extract synthesized response text
            reflection_text = getattr(reflect_resp, "response", "") or getattr(reflect_resp, "text", "") or str(reflect_resp)
            results["details"]["reflection_preview"] = (
                reflection_text[:300] + "..." if len(reflection_text) > 300 else reflection_text
            )
            logger.info(f"Reflect completed in {results['details']['reflect_time_seconds']}s")
            logger.info(f"Reflect output: {results['details']['reflection_preview']}")
            break
        except Exception as exc:
            err_str = str(exc)
            if is_groq and ("429" in err_str or "Rate limit" in err_str or "quota" in err_str.lower()) and attempt < reflect_attempts:
                wait_sec = 65
                logger.warning(
                    f"Reflect hit rate limit on attempt {attempt}/{reflect_attempts}. "
                    f"Waiting {wait_sec}s for complete 60s sliding window replenishment before retrying..."
                )
                time.sleep(wait_sec)
            else:
                logger.exception("Reflect exception")
                results["errors"].append(f"Reflect exception: {exc}")
                results["status"] = "failed"
                return results

    if cleanup:
        try:
            service.get_client().delete_bank(bank_id)
        except Exception:
            pass

    results["status"] = "success"
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("SEARCHMIND: Hindsight Retain -> Recall -> Reflect Smoke Test")
    print("=" * 60)
    output = run_smoke_test()
    print("\nResult Summary:")
    print(json.dumps(output, indent=2))
    if output["status"] == "success":
        print("\nAll Hindsight operations (Retain, Recall, Reflect) verified successfully!")
        sys.exit(0)
    else:
        print("\nSmoke test failed or was incomplete.")
        sys.exit(1)
