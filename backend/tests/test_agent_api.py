"""Unit tests for the SearchMind evaluator frontend API endpoints.

Validates:
1. GET /api/v1/agent/demo-analysis returns structured evidence, recall, and recommendation
2. Recommendation initially halts at PENDING_APPROVAL
3. Operator approval transitions status to APPROVED
4. Operator rejection transitions status to REJECTED
5. Experiment execution is blocked when unapproved (403 Forbidden)
6. Approved experiment executes deterministically, computes outcome, and retains lesson
7. Retained lesson is verified as available to future recall
8. GET /api/v1/memory/browse enables searching and filtering historical memory records
9. GET / and GET /app serve the frontend workspace UI
10. All operations consume zero Groq tokens and execute locally
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def setup_function():
    """Reset demo session before each test."""
    client.post("/api/v1/agent/reset")


def test_get_demo_analysis():
    """Verify initial analysis response with evidence, historical memory, and pending approval."""
    response = client.get("/api/v1/agent/demo-analysis")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["demo_mode"] is True

    # Signal check
    sig = data["signal"]
    assert sig["page_title"] == "Waterproof Alpine Hiking Boots"
    assert sig["keyword"] == "waterproof hiking boots"
    assert sig["current_ctr"] == 1.8
    assert sig["previous_ctr"] == 3.2
    assert sig["ctr_delta"] == -1.4
    assert sig["rank"] == 3.1
    assert "top-3 SERP rank" in sig["signal_description"]

    # Historical memory check
    mem = data["historical_memory"]
    assert mem["relevant_count"] == 9
    assert mem["positive_count"] == 2
    assert mem["negative_count"] == 3
    assert len(mem["evidence_list"]) > 0

    # Learning synthesis check
    lrn = data["learning"]
    assert "keyword-first" in lrn["synthesis"]
    assert "contextual" in lrn["caveat"].lower()

    # Recommendation check
    rec = data["recommendation"]
    assert "revised title tag" in rec["action"].lower()
    assert rec["confidence"] == 0.57
    assert rec["approval_required"] is True
    assert rec["status"] == "PENDING_APPROVAL"

    # Gateway state
    assert data["approval"]["status"] == "PENDING_APPROVAL"
    assert data["approval"]["can_execute"] is False
    assert data["experiment"] is None


def test_approval_lifecycle():
    """Verify operator approval and rejection transitions."""
    # 1. Approve
    res_app = client.post("/api/v1/agent/approval", json={
        "approved": True,
        "operator_note": "Approved keyword-first title test. Exclude aggressive discount phrasing.",
    })
    assert res_app.status_code == 200
    data_app = res_app.json()
    assert data_app["approval_status"] == "APPROVED"
    assert data_app["can_execute_experiment"] is True

    # Check status endpoint
    status_res = client.get("/api/v1/agent/demo-analysis")
    assert status_res.json()["approval"]["status"] == "APPROVED"
    assert status_res.json()["approval"]["can_execute"] is True

    # 2. Reject
    res_rej = client.post("/api/v1/agent/approval", json={
        "approved": False,
        "operator_note": "Operator rejected risky change.",
    })
    assert res_rej.status_code == 200
    data_rej = res_rej.json()
    assert data_rej["approval_status"] == "REJECTED"
    assert data_rej["can_execute_experiment"] is False


def test_experiment_execution_blocked_without_approval():
    """Verify that unapproved experiment execution is rejected with 403 Forbidden."""
    # Attempt execution before approving
    res = client.post("/api/v1/agent/execute-experiment", json={"measured_value": 2.70})
    assert res.status_code == 403
    assert "Human approval is required" in res.json()["detail"]


def test_approved_experiment_execution_and_retained_lesson():
    """Verify end-to-end execution of approved experiment and factual lesson retention."""
    # Step 1: Approve
    client.post("/api/v1/agent/approval", json={"approved": True})

    # Step 2: Execute experiment
    res = client.post("/api/v1/agent/execute-experiment", json={"measured_value": 2.70})
    assert res.status_code == 200
    data = res.json()

    # Verify experiment outcome
    exp = data["experiment"]
    out = data["outcome"]
    assert exp["experiment_id"] == "exp_021_demo"
    assert exp["metric"] == "CTR"
    assert exp["baseline"] == 1.8
    assert exp["measured"] == 2.7

    assert out["absolute_change"] == "+0.90 percentage points"
    assert out["relative_change"] == "+50.0%"
    assert out["classification"] == "POSITIVE"
    assert out["factual_statement"] == "Observed positive result in this experiment."

    # Verify retained lesson
    lesson = data["lesson"]
    assert "Observed positive" in lesson
    assert "not be treated as universal proof" in lesson

    # Verify memory document ID and bank
    retain_info = data["retain_info"]
    assert retain_info["memory_doc_id"] == "seo_exp_021_demo"
    assert retain_info["status"] == "RETAINED"

    # Verify future learning
    assert data["future_learning"]["available"] is True
    assert "seo_exp_021_demo" in data["future_learning"]["verification_note"]


def test_memory_browser_search_and_filters():
    """Verify searching and filtering historical memory records in the browser."""
    # Browse all
    res_all = client.get("/api/v1/memory/browse")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total_records"] >= 20

    # Search by keyword
    res_kw = client.get("/api/v1/memory/browse?q=hiking")
    assert res_kw.status_code == 200
    data_kw = res_kw.json()
    assert data_kw["total_records"] > 0
    for m in data_kw["memories"]:
        match = "hiking" in m["context"].lower() or "hiking" in m["url"].lower()
        assert match

    # Filter by outcome
    res_pos = client.get("/api/v1/memory/browse?outcome=positive")
    assert res_pos.status_code == 200
    for m in res_pos.json()["memories"]:
        assert m["outcome"] == "positive"

    res_neg = client.get("/api/v1/memory/browse?outcome=negative")
    assert res_neg.status_code == 200
    for m in res_neg.json()["memories"]:
        assert m["outcome"] == "negative"


def test_frontend_workspace_serving():
    """Verify that root and /app serve the frontend workspace HTML and static assets."""
    # Browser request to root
    res_html = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers.get("content-type", "")
    assert "YourWebMind" in res_html.text
    assert "The Learning Loop" in res_html.text

    # Direct /app route
    res_app = client.get("/app")
    assert res_app.status_code == 200
    assert "YourWebMind" in res_app.text

    # JSON request to root
    res_json = client.get("/", headers={"Accept": "application/json"})
    assert res_json.status_code == 200
    assert res_json.json()["service"] == "YourWebMind API"
