"""SearchMind synthetic SEO dataset seeder for Hindsight memory.

Ingests the validated synthetic SEO dataset into the persistent Hindsight
memory bank 'searchmind-demo' (or a user-specified bank).

Features:
- Strict Pydantic model validation prior to ingestion
- Token bucket capacity checking (Groq TPM guardrail)
- Rate-limit pacing and automatic exponential backoff
- Idempotent document retention using deterministic document IDs
- Recall and Reflect verification queries against live memory

Usage:
    # Run full seeding and verification:
    python -m app.seeding.demo

    # Dry-run validation only (no external calls):
    python -m app.seeding.demo --dry-run

    # Seed without verification queries:
    python -m app.seeding.demo --skip-verify

    # Target a custom memory bank:
    python -m app.seeding.demo --bank my-custom-bank
"""

import argparse
import logging
import sys
import time
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.seo.demo_dataset import (
    build_hindsight_memory_documents,
    load_demo_dataset,
    validate_demo_dataset,
)
from app.services.hindsight_service import get_hindsight_service
from app.smoke_test import ensure_groq_capacity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("searchmind.seeding.demo")

DEFAULT_BANK = "searchmind-demo"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed Hindsight memory bank with SearchMind synthetic SEO dataset."
    )
    parser.add_argument(
        "--bank",
        type=str,
        default=DEFAULT_BANK,
        help=f"Target Hindsight memory bank identifier (default: '{DEFAULT_BANK}')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate dataset and preview memory documents without calling Hindsight.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip post-seeding Recall and Reflect verification queries.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=4.0,
        help="Inter-document pacing delay in seconds (default: 4.0s).",
    )
    parser.add_argument(
        "--reset-bank",
        action="store_true",
        help="Delete existing bank prior to seeding (warning: clears previous memories in bank).",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="1-based document index to start retaining from (default: 1)",
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="1-based document index to stop retaining at, inclusive (default: all)",
    )
    return parser.parse_args()


def run_seeding(
    bank_id: str = DEFAULT_BANK,
    dry_run: bool = False,
    skip_verify: bool = False,
    delay: float = 4.0,
    reset_bank: bool = False,
    start_index: int = 1,
    end_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Execute the dataset validation, retention, and verification pipeline.

    Returns:
        Structured results dictionary with status, counts, and timings.
    """
    settings = get_settings()
    results: Dict[str, Any] = {
        "status": "pending",
        "bank_id": bank_id,
        "dry_run": dry_run,
        "dataset_validation": None,
        "documents_retained": 0,
        "retained_ids": [],
        "recall_results": [],
        "reflect_result": None,
        "timing": {},
        "errors": [],
    }

    # Step 1: Strict Pydantic dataset validation
    logger.info("=" * 60)
    logger.info("SearchMind Demo Dataset Seeder")
    logger.info("=" * 60)
    logger.info("Step 1/3: Validating synthetic SEO dataset schemas and references...")

    t0 = time.time()
    validation_report = validate_demo_dataset()
    results["timing"]["validation_seconds"] = round(time.time() - t0, 3)
    results["dataset_validation"] = validation_report

    if not validation_report["valid"]:
        logger.error("Dataset validation failed with errors:")
        for err in validation_report["errors"]:
            logger.error(f"  - {err}")
        results["status"] = "validation_failed"
        results["errors"] = validation_report["errors"]
        return results

    logger.info("Dataset validation PASSED:")
    for entity, count in validation_report["counts"].items():
        logger.info(f"  - {entity}: {count} records")
    logger.info(f"  - Outcome distribution: {validation_report['outcome_distribution']}")

    # Step 2: Build memory documents
    documents = build_hindsight_memory_documents()
    logger.info(f"Generated {len(documents)} structured memory documents for Hindsight.")

    if dry_run:
        logger.info("Dry-run requested. Skipping Hindsight retention.")
        logger.info(f"First preview document ID: {documents[0]['document_id']}")
        logger.info(f"Sample content preview:\n{documents[0]['content'][:250]}...")
        results["status"] = "dry_run_success"
        results["documents_retained"] = len(documents)
        return results

    # Verify LLM configuration
    if not settings.is_llm_configured:
        err = (
            "HINDSIGHT_API_LLM_API_KEY is not configured in .env. "
            "Cannot connect to Hindsight or Groq LLM for real memory retention."
        )
        logger.error(err)
        results["status"] = "unconfigured_llm"
        results["errors"].append(err)
        return results

    # Step 3: Initialize Hindsight Service
    logger.info(f"Connecting to Hindsight memory engine (Profile: {settings.HINDSIGHT_PROFILE})...")
    service = get_hindsight_service(settings)
    if not service.initialize():
        err = f"Failed to initialize Hindsight service: {service.last_error}"
        logger.error(err)
        results["status"] = "init_failed"
        results["errors"].append(err)
        return results

    client = service.get_client()

    if reset_bank:
        logger.info(f"Resetting bank '{bank_id}' before seeding...")
        try:
            client.delete_bank(bank_id)
            logger.info(f"Deleted existing bank '{bank_id}'.")
        except Exception as e:
            logger.debug(f"Reset bank notice (may not exist): {e}")

    # Step 4: Ingest documents into Hindsight with rate-limit pacing
    start_pos = max(1, start_index) - 1
    end_pos = end_index if end_index is not None else len(documents)
    target_docs = documents[start_pos:end_pos]
    logger.info(f"Step 2/3: Retaining {len(target_docs)} SEO experiments (range {start_index}..{end_pos}) into bank '{bank_id}'...")
    retain_start = time.time()
    max_retries = 4

    for local_idx, doc in enumerate(target_docs):
        global_idx = start_pos + local_idx + 1
        doc_id = doc["document_id"]
        logger.info(f"[{global_idx}/{len(documents)}] Retaining {doc_id} ({doc['metadata'].get('experiment_type')}, outcome: {doc['metadata'].get('outcome_class')})...")

        # Guard Groq TPM limit before calling retain
        ensure_groq_capacity(settings, min_tokens=5500)

        ingested = False
        for attempt in range(1, max_retries + 1):
            t_doc = time.time()
            try:
                service.retain(
                    bank_id=bank_id,
                    content=doc["content"],
                    context=doc.get("context"),
                    metadata=doc.get("metadata"),
                    tags=doc.get("tags"),
                    document_id=doc_id,
                    timestamp=doc.get("timestamp"),
                    update_mode="replace",
                )
                elapsed = round(time.time() - t_doc, 2)
                logger.info(f"  -> Retained {doc_id} successfully ({elapsed}s)")
                results["documents_retained"] += 1
                results["retained_ids"].append(doc_id)
                ingested = True
                break
            except Exception as exc:
                err_str = str(exc)
                if ("429" in err_str or "Rate limit" in err_str or "quota" in err_str.lower()) and attempt < max_retries:
                    wait_sec = 25 * attempt
                    logger.warning(
                        f"  -> Rate limit encountered on {doc_id} (attempt {attempt}/{max_retries}). "
                        f"Waiting {wait_sec}s for token bucket replenishment..."
                    )
                    time.sleep(wait_sec)
                else:
                    logger.error(f"  -> Failed to retain {doc_id}: {exc}")
                    results["errors"].append(f"Retain failed for {doc_id}: {exc}")
                    break

        if not ingested:
            logger.warning(f"Could not ingest {doc_id} after {max_retries} attempts.")

        # Pacing delay between retain operations to respect sliding TPM window
        if local_idx < len(target_docs) - 1 and delay > 0:
            time.sleep(delay)

    total_retain_time = round(time.time() - retain_start, 2)
    results["timing"]["retain_seconds"] = total_retain_time
    logger.info(
        f"Seeding completed: {results['documents_retained']}/{len(target_docs)} documents retained in {total_retain_time}s."
    )

    if skip_verify:
        results["status"] = "success"
        return results

    # Step 5: Verification Queries (3 Recall queries + 1 Reflect query)
    logger.info("=" * 60)
    logger.info("Step 3/3: Running Live Memory Verification Queries")
    logger.info("=" * 60)

    recall_queries = [
        "What happened when we optimized title tags on commercial product pages?",
        "What were the results of adding FAQ content to category pages?",
        "Which experiments showed negative or inconclusive results?",
    ]

    for q_idx, query in enumerate(recall_queries, start=1):
        logger.info(f"Verification Query {q_idx}/4 (Recall): '{query}'")
        ensure_groq_capacity(settings, min_tokens=5500)
        t_q = time.time()
        try:
            recall_resp = service.recall(bank_id=bank_id, query=query, budget="mid")
            q_time = round(time.time() - t_q, 2)
            num_results = len(recall_resp.results) if hasattr(recall_resp, "results") and recall_resp.results else 0
            logger.info(f"  -> Recall succeeded in {q_time}s (found {num_results} memory units)")
            if hasattr(recall_resp, "results") and recall_resp.results:
                for r_item in recall_resp.results[:2]:
                    snippet = getattr(r_item, "text", "") or ""
                    logger.info(f"     [Sample Fact]: {snippet[:120]}...")
            results["recall_results"].append({
                "query": query,
                "count": num_results,
                "time_seconds": q_time,
                "sample_facts": [getattr(r, "text", "") for r in (recall_resp.results[:3] if hasattr(recall_resp, "results") and recall_resp.results else [])],
            })
        except Exception as exc:
            logger.error(f"  -> Recall query failed: {exc}")
            results["errors"].append(f"Recall query '{query}' failed: {exc}")

    # Reflect query
    reflect_query = (
        "Based on past experiments, what optimization strategies have proven most reliable for category pages?"
    )
    logger.info(f"Verification Query 4/4 (Reflect): '{reflect_query}'")
    ensure_groq_capacity(settings, min_tokens=7200)
    reflect_attempts = 3
    for attempt in range(1, reflect_attempts + 1):
        t_ref = time.time()
        try:
            reflect_resp = service.reflect(
                bank_id=bank_id,
                query=reflect_query,
                budget="low",
            )
            ref_time = round(time.time() - t_ref, 2)
            answer = getattr(reflect_resp, "text", None) or getattr(reflect_resp, "response", None) or getattr(reflect_resp, "answer", None) or str(reflect_resp)
            logger.info(f"  -> Reflect succeeded in {ref_time}s:")
            logger.info(f"     Reflect Output:\n{answer}")
            results["reflect_result"] = {
                "query": reflect_query,
                "answer": str(answer),
                "time_seconds": ref_time,
            }
            break
        except Exception as exc:
            err_str = str(exc)
            if ("429" in err_str or "Rate limit" in err_str or "quota" in err_str.lower()) and attempt < reflect_attempts:
                wait_sec = 35 * attempt
                logger.warning(
                    f"  -> Reflect hit rate limit on attempt {attempt}/{reflect_attempts}. "
                    f"Waiting {wait_sec}s for token bucket replenishment..."
                )
                time.sleep(wait_sec)
                ensure_groq_capacity(settings, min_tokens=7200)
            else:
                logger.error(f"  -> Reflect query failed: {exc}")
                results["errors"].append(f"Reflect query '{reflect_query}' failed: {exc}")
                break

    results["status"] = "success" if not results["errors"] else "partial_success"
    return results


def main() -> None:
    """CLI entry point for seeding script."""
    args = parse_args()
    results = run_seeding(
        bank_id=args.bank,
        dry_run=args.dry_run,
        skip_verify=args.skip_verify,
        delay=args.delay,
        reset_bank=args.reset_bank,
        start_index=args.start_index,
        end_index=args.end_index,
    )

    print("\n" + "=" * 60)
    print("SEARCHMIND MEMORY SEEDING SUMMARY")
    print("=" * 60)
    print(f"Status:             {results['status'].upper()}")
    print(f"Memory Bank:        {results['bank_id']}")
    print(f"Documents Retained: {results['documents_retained']}")
    if "timing" in results:
        for phase, t in results["timing"].items():
            print(f"Time ({phase}): {t}s")
    if results.get("errors"):
        print(f"Errors ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  - {err}")
    print("=" * 60 + "\n")

    if results["status"] not in ("success", "dry_run_success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
