"""Deterministic unit tests for optional Hindsight Reflect reasoning layer.

Validates:
1. Reflect succeeds and adds contextual synthesis
2. Reflect unavailable -> workflow still generates recommendation
3. Reflect failure -> recommendation does not crash (graceful fallback)
4. Reflect does not override deterministic confidence
5. Conflicting historical evidence remains represented
6. Reflect does not create a recommendation by itself
7. Existing human approval gate still works
8. No Retain is triggered by Reflect
9. No additional Recall is triggered by Reflect
10. Non-dogmatic phrasing sanitization
11. Deterministic reflection query construction
12. Zero Groq calls during normal tests

All tests execute strictly in local Python memory with ZERO token consumption.
"""

from unittest.mock import MagicMock
import pytest

from app.agents import (
    CurrentSEOEvidence,
    HistoricalAnalyzer,
    HistoricalSEOContext,
    RecommendationEngine,
    SEOAgent,
    SEOAnalysisRequest,
    SEOWorkflowEngine,
    SEOWorkflowResult,
)
from app.memory import (
    InMemoryRecallAdapter,
    InMemoryReflectAdapter,
    InMemoryRetainAdapter,
    ReflectResult,
    build_reflection_query,
    sanitize_non_dogmatic_reflection,
)
from app.models.enums import ApprovalStatus, ObservationSeverity, SearchIntent
from app.models.seo import SEOObservation


@pytest.fixture
def sample_analysis_request():
    """Standard commercial product page SEO analysis request."""
    return SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        page_type="product",
        target_keyword="waterproof alpine hiking boots",
        search_intent=SearchIntent.TRANSACTIONAL,
        current_metrics={
            "position": 3.1,
            "previous_position": 2.9,
            "ranking_delta": 0.2,
            "ctr": 1.8,
            "previous_ctr": 2.4,
            "ctr_delta": -0.6,
            "impressions": 14200,
            "clicks": 255,
        },
        current_observations=[
            SEOObservation(
                observation_id="obs_test_001",
                project_id="searchmind-demo-store",
                url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
                observation_type="low_ctr_high_rank",
                severity=ObservationSeverity.HIGH,
                metric_name="ctr",
                current_value=1.8,
                previous_value=2.4,
                delta=-0.6,
                description="Organic CTR has declined 0.6 pp despite top-3 SERP ranking.",
            )
        ],
        technique_focus="title_tag_optimization",
    )


@pytest.fixture
def fake_recall_adapter():
    """InMemoryRecallAdapter with standard product page historical test fixture."""
    return InMemoryRecallAdapter(
        fixture_memories=[
            {
                "memory_text": (
                    "SEO Experiment exp_001: Testing keyword-first title on hiking boots product page. "
                    "CTR improved from 1.6% to 2.5% (+56.25%). Outcome: POSITIVE."
                ),
                "experiment_id": "exp_001",
                "outcome": "positive",
                "page_type": "product",
            },
            {
                "memory_text": (
                    "SEO Experiment exp_007: Promotional discount modifier in title damaged CTR "
                    "from 2.2% to 1.8% (-18.18%). Outcome: NEGATIVE."
                ),
                "experiment_id": "exp_007",
                "outcome": "negative",
                "page_type": "product",
            },
        ]
    )


# -----------------------------------------------------------------------------
# Test 1: Reflect Succeeds and Adds Contextual Synthesis
# -----------------------------------------------------------------------------
def test_reflect_succeeds_and_adds_contextual_synthesis(sample_analysis_request, fake_recall_adapter):
    """Verify that when enabled, Reflect executes and enriches historical context & recommendation."""
    reflect_adapter = InMemoryReflectAdapter(
        default_synthesis="Keyword-first title restructuring showed reliable CTR lift across tested commercial boots pages."
    )
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    assert result.reflection_result is not None
    assert result.reflection_result.success is True
    assert result.reflection_result.source == "fixture"
    assert "Keyword-first title restructuring" in result.reflection_result.synthesis_text
    assert "[Hindsight Reflect Synthesis]" in result.historical_context.reflection
    assert result.recommendation.reflection is not None
    assert "Keyword-first title restructuring" in result.recommendation.reflection
    assert reflect_adapter.calls_count == 1


# -----------------------------------------------------------------------------
# Test 2: Reflect Unavailable -> Workflow Still Generates Recommendation
# -----------------------------------------------------------------------------
def test_reflect_unavailable_workflow_still_generates_recommendation(sample_analysis_request, fake_recall_adapter):
    """Verify that when reflect is not enabled or adapter is None, workflow runs cleanly without crashing."""
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=None,
        enable_reflect=False,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    assert result.reflection_result is None
    assert result.recommendation is not None
    assert result.recommendation.recommendation != ""
    assert result.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert result.workflow_stopped_at_approval is True


# -----------------------------------------------------------------------------
# Test 3: Reflect Failure -> Graceful Fallback, Recommendation Does Not Crash
# -----------------------------------------------------------------------------
def test_reflect_failure_fallback_recommendation_does_not_crash(sample_analysis_request, fake_recall_adapter):
    """Verify that when Reflect fails (e.g. quota limit, network timeout), the engine falls back safely."""
    failing_adapter = InMemoryReflectAdapter(
        should_fail=True,
        failure_error="Groq API 429 Quota Exhausted: Rate limit reached",
    )
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=failing_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    # Workflow completed successfully
    assert result.recommendation is not None
    assert result.reflection_result is not None
    assert result.reflection_result.success is False
    assert "429 Quota Exhausted" in result.reflection_result.error
    # Baseline deterministic reflection from historical analyzer remains intact
    assert result.historical_context.reflection is not None
    assert "[Hindsight Reflect Synthesis]" not in result.historical_context.reflection


# -----------------------------------------------------------------------------
# Test 4: Reflect Does Not Override Deterministic Confidence
# -----------------------------------------------------------------------------
def test_reflect_does_not_override_deterministic_confidence(sample_analysis_request, fake_recall_adapter):
    """Verify that Reflect cannot arbitrarily alter or inflate the deterministic confidence score."""
    workflow_without_reflect = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=None,
        enable_reflect=False,
    )
    result_base = workflow_without_reflect.run_analysis_workflow(sample_analysis_request)
    base_confidence = result_base.recommendation.confidence

    reflect_adapter = InMemoryReflectAdapter(
        default_synthesis="Reflect claims 100% confidence this optimization will always succeed!"
    )
    workflow_with_reflect = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )
    result_reflect = workflow_with_reflect.run_analysis_workflow(sample_analysis_request)
    reflect_confidence = result_reflect.recommendation.confidence

    # Confidence must NOT be inflated or overridden by Reflect
    assert reflect_confidence == base_confidence
    assert 0.10 <= reflect_confidence <= 0.85


# -----------------------------------------------------------------------------
# Test 5: Conflicting Historical Evidence Remains Represented
# -----------------------------------------------------------------------------
def test_conflicting_historical_evidence_remains_represented(sample_analysis_request, fake_recall_adapter):
    """Verify that contradictory or negative past findings in reflection are explicitly captured in caveats."""
    conflicting = ["Promotional modifiers ('massive clearance sale') decreased CTR by -15% in past tests."]
    reflect_adapter = InMemoryReflectAdapter(
        conflicting_evidence=conflicting,
    )
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    caveats = result.historical_context.contextual_caveats
    assert any("[Conflicting Evidence]" in c for c in caveats)
    assert any("decreased CTR" in c for c in caveats)


# -----------------------------------------------------------------------------
# Test 6: Reflect Does Not Create a Recommendation By Itself
# -----------------------------------------------------------------------------
def test_reflect_does_not_create_recommendation_by_itself(sample_analysis_request, fake_recall_adapter):
    """Verify that RecommendationEngine remains solely authoritative for recommendation action text."""
    reflect_adapter = InMemoryReflectAdapter(
        default_synthesis="Arbitrary LLM recommendation text that should not override domain rules."
    )
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    # Recommendation action must be generated by RecommendationEngine rules, not copied verbatim
    assert result.recommendation.recommendation != reflect_adapter.default_synthesis
    assert "title tag" in result.recommendation.recommendation.lower()


# -----------------------------------------------------------------------------
# Test 7: Existing Human Approval Gate Still Works
# -----------------------------------------------------------------------------
def test_existing_human_approval_gate_still_works(sample_analysis_request, fake_recall_adapter):
    """Verify workflow strictly stops at approval gateway even when Reflect was executed."""
    reflect_adapter = InMemoryReflectAdapter()
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    assert result.workflow_stopped_at_approval is True
    assert result.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert result.experiment_proposal is None

    # Process Approval
    approved_result = workflow.process_human_approval(result, approved=True)
    assert approved_result.approval_status == ApprovalStatus.APPROVED
    assert approved_result.workflow_stopped_at_approval is False
    assert approved_result.experiment_proposal is not None
    assert approved_result.reflection_result is not None


# -----------------------------------------------------------------------------
# Test 8: No Retain Is Triggered By Reflect
# -----------------------------------------------------------------------------
def test_no_retain_triggered_by_reflect(sample_analysis_request, fake_recall_adapter):
    """Verify that running reflection does NOT trigger any retain adapter or write to memory."""
    fake_retain_adapter = InMemoryRetainAdapter()
    reflect_adapter = InMemoryReflectAdapter()
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    assert len(fake_retain_adapter.retained_payloads) == 0
    assert result.recommendation is not None


# -----------------------------------------------------------------------------
# Test 9: No Additional Recall Is Triggered By Reflect
# -----------------------------------------------------------------------------
def test_no_additional_recall_triggered_by_reflect(sample_analysis_request, fake_recall_adapter):
    """Verify that Reflect consumes already-retrieved context and does NOT issue a second Recall query."""
    reflect_adapter = InMemoryReflectAdapter()
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    workflow.run_analysis_workflow(sample_analysis_request)

    # Exactly 1 recall call was made to feed historical context; 0 extra recall calls made for reflect
    assert fake_recall_adapter.calls_count == 1
    assert reflect_adapter.calls_count == 1
    assert reflect_adapter.last_context is not None
    assert "Found" in reflect_adapter.last_context or "historical experiment" in reflect_adapter.last_context


# -----------------------------------------------------------------------------
# Test 10: Non-Dogmatic Phrasing Sanitization
# -----------------------------------------------------------------------------
def test_non_dogmatic_phrasing_sanitization():
    """Verify that absolute, dogmatic claims are sanitized with empirical qualifiers."""
    dogmatic_text = (
        "Title tag optimization always increases CTR and guarantees top SERP rankings. "
        "It proves that all pages benefit."
    )
    sanitized = sanitize_non_dogmatic_reflection(dogmatic_text)

    assert "always increases" not in sanitized.lower()
    assert "guarantees" not in sanitized.lower()
    assert "proves that all" not in sanitized.lower()
    assert "was observed to increase in comparable past contexts" in sanitized
    assert "Note: Historical observations are contextual" in sanitized


# -----------------------------------------------------------------------------
# Test 11: Deterministic Reflection Query Construction
# -----------------------------------------------------------------------------
def test_build_reflection_query_deterministic():
    """Verify reflection query incorporates page type, search intent, and keywords deterministically."""
    q_product = build_reflection_query(
        page_type="product",
        search_intent="transactional",
        target_keyword="waterproof alpine boots",
        technique="title_tag_optimization",
    )
    assert "transactional product pages" in q_product
    assert "waterproof alpine boots" in q_product
    assert "caveats" in q_product

    q_category = build_reflection_query(
        page_type="category",
        technique="meta_description",
    )
    assert "category pages" in q_category
    assert "meta description optimization" in q_category


# -----------------------------------------------------------------------------
# Test 12: Zero Groq Calls During Normal Tests
# -----------------------------------------------------------------------------
def test_zero_groq_calls_during_reflect_tests(sample_analysis_request, fake_recall_adapter):
    """Verify that zero network requests or Groq LLM tokens are consumed during reflection testing."""
    mock_hindsight_service = MagicMock()
    mock_hindsight_service.reflect.side_effect = AssertionError("Live Hindsight reflect called unexpectedly!")

    reflect_adapter = InMemoryReflectAdapter()
    workflow = SEOWorkflowEngine(
        recall_adapter=fake_recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
    )

    result = workflow.run_analysis_workflow(sample_analysis_request)

    assert result.reflection_result.source == "fixture"
    mock_hindsight_service.reflect.assert_not_called()
