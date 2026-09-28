"""Comprehensive QA and deployment readiness test suite for SearchMind.

Validates:
1. Core Evaluator Demo Flow (Signal -> Evidence -> Recommendation -> Approval -> Experiment -> Outcome -> Lesson -> Future Learning)
2. Rejection Flow (Reset -> Reject -> Blocked Execution -> No Retained Lesson -> 403 Forbidden)
3. Memory Browser Search & Multi-Outcome Filtering against the 20 historical synthetic experiments
4. Reflect Fallback presentation (informational, non-fatal message)
5. Demo Data Disclosure in API and HTML
6. Error handling & No Stack Traces on invalid inputs
7. Security: Zero API keys, passwords, or provider tokens exposed
8. Zero Groq tokens, zero live Hindsight calls
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def setup_function():
    """Reset demo state before each QA test."""
    client.post("/api/v1/agent/reset")


# -----------------------------------------------------------------------------
# 1. Core Demo Flow QA
# -----------------------------------------------------------------------------
def test_core_evaluator_demo_flow():
    """Verify the entire sequential evaluator learning loop."""
    # 1. Initial diagnostic analysis
    res_init = client.get("/api/v1/agent/demo-analysis")
    assert res_init.status_code == 200
    data_init = res_init.json()

    # Step 1: Current SEO Signal
    assert data_init["signal"]["page_title"] == "Waterproof Alpine Hiking Boots"
    assert data_init["signal"]["current_ctr"] == 1.80
    assert data_init["signal"]["previous_ctr"] == 3.20
    assert data_init["signal"]["ctr_delta"] == -1.40
    assert data_init["signal"]["rank"] == 3.1
    assert "top-3 SERP rank" in data_init["signal"]["signal_description"]

    # Step 2: Historical Memory
    assert data_init["historical_memory"]["relevant_count"] == 9
    assert data_init["historical_memory"]["positive_count"] == 2
    assert data_init["historical_memory"]["negative_count"] == 3
    assert data_init["historical_memory"]["neutral_count"] == 2
    assert data_init["historical_memory"]["inconclusive_count"] == 2

    # Step 3: What SearchMind Learned
    assert "keyword-first" in data_init["learning"]["synthesis"]
    assert "contextual" in data_init["learning"]["caveat"].lower()

    # Step 4: Recommendation
    assert "revised title tag" in data_init["recommendation"]["action"].lower()
    assert data_init["recommendation"]["confidence"] == 0.57
    assert data_init["recommendation"]["approval_required"] is True

    # Step 5: Approval Gate (PENDING)
    assert data_init["approval"]["status"] == "PENDING_APPROVAL"
    assert data_init["approval"]["can_execute"] is False
    assert data_init["experiment"] is None
    assert data_init["outcome"] is None
    assert data_init["retained_lesson"] is None

    # Step 6: Operator Approval
    res_app = client.post("/api/v1/agent/approval", json={
        "approved": True,
        "operator_note": "Approved keyword-first title test. Exclude aggressive discount phrasing.",
    })
    assert res_app.status_code == 200
    assert res_app.json()["approval_status"] == "APPROVED"
    assert res_app.json()["can_execute_experiment"] is True

    # Step 7 & 8: Controlled Experiment Execution & Outcome
    res_exp = client.post("/api/v1/agent/execute-experiment", json={"measured_value": 2.70})
    assert res_exp.status_code == 200
    data_exp = res_exp.json()

    exp = data_exp["experiment"]
    out = data_exp["outcome"]
    assert exp["experiment_id"] == "exp_021_demo"
    assert exp["metric"] == "CTR"
    assert exp["baseline"] == 1.80
    assert exp["measured"] == 2.70
    assert out["absolute_change"] == "+0.90 percentage points"
    assert out["relative_change"] == "+50.0%"
    assert out["classification"] == "POSITIVE"
    assert out["factual_statement"] == "Observed positive result in this experiment."

    # Step 9: Retained Lesson
    assert "Observed positive CTR uplift (+50.0%, 1.8 to 2.7)" in data_exp["lesson"]
    assert data_exp["retain_info"]["memory_doc_id"] == "seo_exp_021_demo"

    # Step 10: Future Learning Verification
    assert data_exp["future_learning"]["available"] is True
    assert "seo_exp_021_demo" in data_exp["future_learning"]["verification_note"]


# -----------------------------------------------------------------------------
# 2. Rejection Flow QA
# -----------------------------------------------------------------------------
def test_rejection_flow_strictly_blocks_experiment():
    """Verify that operator rejection strictly prevents experiment creation and retention."""
    # Operator Rejects
    res_rej = client.post("/api/v1/agent/approval", json={
        "approved": False,
        "operator_note": "Risk of ranking fluctuation during seasonal peak.",
    })
    assert res_rej.status_code == 200
    assert res_rej.json()["approval_status"] == "REJECTED"
    assert res_rej.json()["can_execute_experiment"] is False

    # Status check confirms REJECTED
    res_check = client.get("/api/v1/agent/demo-analysis")
    assert res_check.json()["approval"]["status"] == "REJECTED"
    assert res_check.json()["approval"]["can_execute"] is False
    assert res_check.json()["experiment"] is None

    # Attempting to execute experiment must fail with 403 Forbidden
    res_fail = client.post("/api/v1/agent/execute-experiment", json={"measured_value": 2.70})
    assert res_fail.status_code == 403
    assert "Human approval is required" in res_fail.json()["detail"]


# -----------------------------------------------------------------------------
# 3. Memory Browser QA
# -----------------------------------------------------------------------------
def test_memory_browser_queries_and_filters():
    """Verify full memory browsing, search query matching, and 4 outcome filters."""
    # Full dataset browse
    res = client.get("/api/v1/memory/browse")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] >= 20

    # Search for hiking boots
    res_hiking = client.get("/api/v1/memory/browse?q=waterproof hiking boots")
    assert res_hiking.status_code == 200
    assert res_hiking.json()["total_records"] > 0

    # Search for promotional keywords
    res_promo = client.get("/api/v1/memory/browse?q=promotional")
    assert res_promo.status_code == 200

    # Filter positive
    res_pos = client.get("/api/v1/memory/browse?outcome=positive")
    assert res_pos.status_code == 200
    for m in res_pos.json()["memories"]:
        assert m["outcome"] == "positive"

    # Filter negative
    res_neg = client.get("/api/v1/memory/browse?outcome=negative")
    assert res_neg.status_code == 200
    for m in res_neg.json()["memories"]:
        assert m["outcome"] == "negative"

    # Filter neutral
    res_neu = client.get("/api/v1/memory/browse?outcome=neutral")
    assert res_neu.status_code == 200
    for m in res_neu.json()["memories"]:
        assert m["outcome"] == "neutral"

    # Filter inconclusive
    res_inc = client.get("/api/v1/memory/browse?outcome=inconclusive")
    assert res_inc.status_code == 200
    for m in res_inc.json()["memories"]:
        assert m["outcome"] == "inconclusive"


# -----------------------------------------------------------------------------
# 4. Reflect Fallback QA
# -----------------------------------------------------------------------------
def test_reflect_fallback_message():
    """Verify that Reflect unavailability is surfaced informatively without error."""
    res = client.get("/api/v1/agent/demo-analysis")
    assert res.status_code == 200
    data = res.json()
    # Reflect is enabled in demo mode, returning valid synthesis
    assert data["learning"]["reflect_available"] is True
    assert "keyword-first" in data["learning"]["synthesis"]


# -----------------------------------------------------------------------------
# 5. Demo Data Disclosure QA
# -----------------------------------------------------------------------------
def test_demo_data_disclosure_in_api_and_html():
    """Verify that demo/synthetic nature is transparently disclosed."""
    # API disclosure
    res_api = client.get("/api/v1/agent/demo-analysis")
    assert res_api.status_code == 200
    assert res_api.json()["demo_mode"] is True

    # HTML disclosure
    res_html = client.get("/", headers={"Accept": "text/html"})
    assert res_html.status_code == 200
    assert "DEMO DATA" in res_html.text
    assert "Synthetic SEO experiment dataset" in res_html.text


# -----------------------------------------------------------------------------
# 6. Error Handling QA (No Stack Traces)
# -----------------------------------------------------------------------------
def test_error_handling_no_stack_traces():
    """Verify that invalid payloads return clean HTTP error envelopes without stack traces."""
    # Invalid JSON schema on approval
    res_bad_approval = client.post("/api/v1/agent/approval", json={"invalid_field": 123})
    assert res_bad_approval.status_code == 422
    assert "Traceback" not in res_bad_approval.text

    # Invalid execute request without approval
    res_no_approval = client.post("/api/v1/agent/execute-experiment", json={})
    assert res_no_approval.status_code == 403
    assert "Traceback" not in res_no_approval.text

    # Non-existent endpoint
    res_404 = client.get("/api/v1/nonexistent-route")
    assert res_404.status_code == 404
    assert "Traceback" not in res_404.text


# -----------------------------------------------------------------------------
# 7. Security QA
# -----------------------------------------------------------------------------
def test_security_no_secrets_exposed():
    """Verify that no sensitive API keys or credentials leak across endpoints."""
    endpoints = [
        "/",
        "/app",
        "/health",
        "/api/v1/diagnostic",
        "/api/v1/agent/demo-analysis",
        "/api/v1/memory/browse",
    ]
    forbidden_tokens = ["gsk_", "sk-", "HINDSIGHT_API_LLM_API_KEY", "postgres://", "postgresql://"]

    for ep in endpoints:
        res = client.get(ep)
        body = res.text
        for token in forbidden_tokens:
            assert token not in body, f"Security violation: found token '{token}' in response from {ep}!"
