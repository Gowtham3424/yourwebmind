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

SMOKE_TEST_BANK = "searchmind-smoke-test"
SMOKE_TEST_CONTENT = (
    "SearchMind smoke test memory. The SEO team tested a title optimization on a commercial product page."
)
SMOKE_TEST_RECALL_QUERY = "What did the SEO team test on the commercial product page?"
SMOKE_TEST_REFLECT_QUERY = "What is known about title optimization tests on commercial product pages?"


def run_smoke_test(cleanup: bool = False) -> Dict[str, Any]:
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
        "memory_bank": SMOKE_TEST_BANK,
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

    # Step 2: Retain
    logger.info("Step 2/4: Retaining smoke-test memory...")
    t0 = time.time()
    try:
        retain_resp = service.retain(
            bank_id=SMOKE_TEST_BANK,
            content=SMOKE_TEST_CONTENT,
            metadata={"source": "smoke_test", "topic": "seo_title_optimization"},
            tags=["smoke_test", "commercial", "title_optimization"],
        )
        results["retain_success"] = True
        results["details"]["retain_time_seconds"] = round(time.time() - t0, 3)
        results["details"]["retain_response"] = str(retain_resp)
        logger.info(f"Retain completed in {results['details']['retain_time_seconds']}s")
    except Exception as exc:
        logger.exception("Retain exception")
        results["errors"].append(f"Retain exception: {exc}")
        results["status"] = "failed"
        return results

    # Step 3: Recall
    logger.info(f"Step 3/4: Recalling memories with query '{SMOKE_TEST_RECALL_QUERY}'...")
    t0 = time.time()
    try:
        recall_resp = service.recall(
            bank_id=SMOKE_TEST_BANK,
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

    # Step 4: Reflect
    logger.info(f"Step 4/4: Reflecting over memories with query '{SMOKE_TEST_REFLECT_QUERY}'...")
    t0 = time.time()
    try:
        reflect_resp = service.reflect(
            bank_id=SMOKE_TEST_BANK,
            query=SMOKE_TEST_REFLECT_QUERY,
            budget="low",
            include_facts=True,
        )
        results["reflect_success"] = True
        results["details"]["reflect_time_seconds"] = round(time.time() - t0, 3)
        # Extract synthesized response text
        reflection_text = getattr(reflect_resp, "response", "") or getattr(reflect_resp, "text", "") or str(reflect_resp)
        results["details"]["reflection_preview"] = (
            reflection_text[:200] + "..." if len(reflection_text) > 200 else reflection_text
        )
        logger.info(f"Reflect completed in {results['details']['reflect_time_seconds']}s")
        logger.info(f"Reflect output: {results['details']['reflection_preview']}")
    except Exception as exc:
        logger.exception("Reflect exception")
        results["errors"].append(f"Reflect exception: {exc}")
        results["status"] = "failed"
        return results

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
