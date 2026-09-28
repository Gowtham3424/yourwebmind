"""Comprehensive fallback, error handling, and security audit tests for SearchMind SEO Agent.

Validates the 10 explicit audit fallback and edge-case guarantees:
1. Fallback: No historical evidence (recall returns 0 items -> graceful baseline recommendation)
2. Fallback: Reflect unavailable (reflect_adapter is None / disabled -> smooth fallback)
3. Fallback: Reflect failure resilience (reflect adapter exception -> fallback to factual recall)
4. Fallback: Recommendation generated regardless (valid recommendation with empty context)
5. Audit: Every generated recommendation enforces human approval (requires_approval = True)
6. Audit: Rejected or unapproved recommendations are strictly blocked from execution
7. Fallback: Zero-baseline metrics handled safely without ZeroDivisionError
8. Audit: Lesson and reflection synthesis sanitizes dogmatic, absolute claims
9. Fallback: Retain adapter failure does not corrupt experiment outcome or crash pipeline
10. Audit: Existing historical dataset files in data/demo/ remain strictly immutable

All tests execute deterministically in local memory with 0 network / Groq calls.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from app.agents.demo_scenario import build_demo_fixture_adapter, run_full_learning_loop_demo
from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import CurrentSEOEvidence, HistoricalSEOContext, SEOAnalysisRequest
from app.agents.workflow import SEOWorkflowEngine
from app.experiments import (
    ExperimentExecutionService,
    compute_experiment_outcome,
)
from app.memory import (
    InMemoryRecallAdapter,
    InMemoryReflectAdapter,
    InMemoryRetainAdapter,
    sanitize_non_dogmatic_reflection,
)
from app.models.base import utc_now
from app.models.enums import ApprovalStatus, ExperimentStatus, ObservationSeverity, OutcomeClass, SearchIntent
from app.models.experiment import SEOExperiment
from app.models.recommendation import SEORecommendation
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact
from app.seo.demo_dataset import DATA_DIR, load_demo_dataset


@pytest.fixture
def sample_analysis_request() -> SEOAnalysisRequest:
    """Fixture providing a realistic diagnostic SEO analysis request."""
    return SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        current_page=WebsiteFact(
            project_id="searchmind-demo-store",
            url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
            page_type="product",
            target_keyword="waterproof hiking boots",
            title="SearchMind Alpine Hiking Boots",
            meta_description="Alpine boots for mountain hiking.",
            search_intent=SearchIntent.COMMERCIAL,
        ),
        current_observations=[
            SEOObservation(
                observation_id="obs_test_001",
                project_id="searchmind-demo-store",
                url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
                observation_type="low_ctr_high_rank",
                severity=ObservationSeverity.HIGH,
                metric_name="ctr",
                current_value=1.8,
                previous_value=3.2,
                delta=-1.4,
                description="Organic CTR dropped despite top-3 ranking.",
            )
        ],
        current_metrics={"ctr": 1.8, "previous_ctr": 3.2, "position": 3.1, "previous_position": 2.9},
        target_keyword="waterproof hiking boots",
        search_intent=SearchIntent.COMMERCIAL,
        page_type="product",
        technique_focus="title_tag_optimization",
    )


# -----------------------------------------------------------------------------
# 1. Fallback: No Historical Evidence
# -----------------------------------------------------------------------------
def test_fallback_no_historical_evidence(sample_analysis_request):
    """Verify that when memory recall returns 0 items, workflow generates a baseline recommendation gracefully."""
    empty_recall_adapter = InMemoryRecallAdapter()  # 0 items
    analyzer = HistoricalAnalyzer(dataset_data={"experiments.json": [], "outcomes.json": []})
    engine = SEOWorkflowEngine(
        historical_analyzer=analyzer,
        recommendation_engine=RecommendationEngine(),
        recall_adapter=empty_recall_adapter,
        enable_reflect=False,
    )

    result = engine.run_analysis_workflow(sample_analysis_request)

    assert result is not None
    assert result.historical_context.source_count == 0
    assert len(result.historical_context.relevant_experiment_ids) == 0
    assert result.recommendation is not None
    assert result.recommendation.recommendation_type == "exploratory_title_test"
    # Unproven confidence capped at baseline
    assert result.recommendation.confidence <= 0.40
    assert result.recommendation.requires_approval is True
    assert result.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert result.workflow_stopped_at_approval is True


# -----------------------------------------------------------------------------
# 2. Fallback: Reflect Unavailable
# -----------------------------------------------------------------------------
def test_fallback_reflect_unavailable(sample_analysis_request):
    """Verify that when Reflect is disabled or adapter is None, workflow executes seamlessly."""
    fixture_recall = build_demo_fixture_adapter()
    engine = SEOWorkflowEngine(
        historical_analyzer=HistoricalAnalyzer(),
        recommendation_engine=RecommendationEngine(),
        recall_adapter=fixture_recall,
        reflect_adapter=None,  # No reflect adapter configured
        enable_reflect=False,
    )

    result = engine.run_analysis_workflow(sample_analysis_request)

    assert result is not None
    assert result.reflection_result is None
    assert result.historical_context.source_count > 0
    assert result.recommendation is not None
    assert result.recommendation.requires_approval is True


# -----------------------------------------------------------------------------
# 3. Fallback: Reflect Failure Resilience
# -----------------------------------------------------------------------------
def test_fallback_reflect_failure_resilience(sample_analysis_request):
    """Verify that if Reflect raises an exception (e.g. timeout), workflow falls back cleanly to recall."""
    failing_reflect = MagicMock()
    failing_reflect.reflect.side_effect = RuntimeError("Simulated upstream LLM/Reflect service timeout")

    engine = SEOWorkflowEngine(
        historical_analyzer=HistoricalAnalyzer(),
        recommendation_engine=RecommendationEngine(),
        recall_adapter=build_demo_fixture_adapter(),
        reflect_adapter=failing_reflect,
        enable_reflect=True,
    )

    # Workflow should catch the reflect failure, log warning, and proceed without raising
    result = engine.run_analysis_workflow(sample_analysis_request)

    assert result is not None
    assert result.historical_context.source_count > 0
    assert result.recommendation is not None
    assert result.recommendation.requires_approval is True


# -----------------------------------------------------------------------------
# 4. Fallback: Recommendation Generated Without Precedent
# -----------------------------------------------------------------------------
def test_fallback_recommendation_generated_without_precedent():
    """Verify that RecommendationEngine produces a valid, bounded recommendation with empty historical context."""
    engine = RecommendationEngine()
    empty_context = HistoricalSEOContext(
        query="empty precedent check",
        source_count=0,
        relevant_experiment_ids=[],
        positive_examples=[],
        negative_examples=[],
        neutral_examples=[],
        inconclusive_examples=[],
    )
    evidence = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/boots",
        keyword="hiking boots",
        search_intent="commercial",
        page_type="product",
        ctr=1.5,
        current_ranking=3.0,
    )

    rec = engine.generate_recommendation(
        project_id="test-store",
        current_evidence=evidence,
        historical_context=empty_context,
    )

    assert rec is not None
    assert rec.recommendation_type == "exploratory_title_test"
    assert rec.confidence == 0.35
    assert "no historical experiments exist" in rec.recommendation.lower()
    assert rec.requires_approval is True


# -----------------------------------------------------------------------------
# 5. Audit: Every Recommendation Enforces Human Approval Gateway
# -----------------------------------------------------------------------------
def test_audit_all_recommendations_enforce_approval():
    """Audit guarantee: No recommendation can bypass the human approval requirement."""
    engine = RecommendationEngine()
    evidence = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/boots",
        keyword="hiking boots",
        search_intent="commercial",
        page_type="product",
        ctr=1.8,
        current_ranking=3.1,
    )

    contexts = [
        # Zero precedent
        HistoricalSEOContext(query="zero precedent", source_count=0, relevant_experiment_ids=[]),
        # Mixed precedent
        HistoricalSEOContext(
            query="mixed precedent",
            source_count=2,
            relevant_experiment_ids=["exp_001", "exp_014"],
            positive_examples=[{"id": "exp_001"}],
            negative_examples=[{"id": "exp_014"}],
        ),
        # Predominantly positive
        HistoricalSEOContext(
            query="positive precedent",
            source_count=3,
            relevant_experiment_ids=["exp_001", "exp_002"],
            positive_examples=[{"id": "exp_001"}, {"id": "exp_002"}],
        ),
        # Predominantly negative
        HistoricalSEOContext(
            query="negative precedent",
            source_count=2,
            relevant_experiment_ids=["exp_014", "exp_015"],
            negative_examples=[{"id": "exp_014"}, {"id": "exp_015"}],
        ),
    ]

    for ctx in contexts:
        rec = engine.generate_recommendation("proj_audit", evidence, ctx)
        assert rec.requires_approval is True, f"Failed for context: {ctx}"


# -----------------------------------------------------------------------------
# 6. Audit: Rejected Recommendation Blocked from Execution
# -----------------------------------------------------------------------------
def test_audit_rejected_recommendation_blocked_from_execution():
    """Audit guarantee: Operator rejection strictly blocks experiment execution via PermissionError."""
    service = ExperimentExecutionService()
    rec = SEORecommendation(
        recommendation_id="rec_reject_001",
        project_id="audit_proj",
        url="https://demo-searchmind-store.example/products/boots",
        recommendation_type="title_tag_optimization",
        recommendation="Test bold promo title.",
        current_evidence="CTR drop",
        confidence=0.50,
        requires_approval=True,
    )

    # Rejection status must raise PermissionError
    with pytest.raises(PermissionError, match="Operator approval is required"):
        service.create_experiment_from_recommendation(
            recommendation=rec,
            approval_status=ApprovalStatus.REJECTED,
        )

    # Pending approval status must also raise PermissionError
    with pytest.raises(PermissionError, match="Operator approval is required"):
        service.create_experiment_from_recommendation(
            recommendation=rec,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
        )

    # Service should contain zero experiments
    assert len(service.experiments) == 0


# -----------------------------------------------------------------------------
# 7. Fallback: Outcome Calculation Handles Zero Baseline Safely
# -----------------------------------------------------------------------------
def test_fallback_outcome_calculation_handles_zero_baseline():
    """Verify that zero-baseline metrics do not cause ZeroDivisionError and calculate valid deltas."""
    exp = SEOExperiment(
        experiment_id="exp_zero_baseline",
        project_id="searchmind-demo-store",
        recommendation_id="rec_001",
        url="https://demo-searchmind-store.example/products/boots",
        experiment_type="new_feature",
        hypothesis="New structured data will generate rich snippet clicks from zero baseline.",
        control_description="No rich snippet markup.",
        treatment_description="Product Schema.org markup.",
        primary_metric="rich_clicks",
        secondary_metrics=["position"],
        baseline_metrics={"rich_clicks": 0.0},
        start_date=utc_now(),
    )

    # Case A: 0.0 baseline -> positive measured value
    outcome_a = compute_experiment_outcome(exp, measured_value=25.0)
    assert outcome_a.absolute_change == 25.0
    assert outcome_a.percentage_change == 100.0
    assert outcome_a.outcome_class == OutcomeClass.POSITIVE

    # Case B: 0.0 baseline -> 0.0 measured value (no change)
    outcome_b = compute_experiment_outcome(exp, measured_value=0.0)
    assert outcome_b.absolute_change == 0.0
    assert outcome_b.percentage_change == 0.0
    assert outcome_b.outcome_class == OutcomeClass.NEUTRAL


# -----------------------------------------------------------------------------
# 8. Audit: Lesson Generation Sanitizes Dogmatic Claims
# -----------------------------------------------------------------------------
def test_audit_lesson_generation_sanitizes_dogmatic_claims():
    """Audit guarantee: Dogmatic, absolute claims ('always', 'guarantees', 'never') are sanitized into contextual claims."""
    dogmatic_input = (
        "Adding brand keywords to product titles always increases CTR by 50% and guarantees top SERP ranking. "
        "This proves that all title modifications succeed and never fail."
    )

    sanitized = sanitize_non_dogmatic_reflection(dogmatic_input)

    assert "always increases" not in sanitized
    assert "guarantees" not in sanitized
    assert "proves that all" not in sanitized
    assert "never" not in sanitized.lower() or "rarely" in sanitized
    assert "Note: Historical observations are contextual" in sanitized


# -----------------------------------------------------------------------------
# 9. Fallback: Retain Adapter Failure Preserves Outcome
# -----------------------------------------------------------------------------
def test_fallback_retain_adapter_failure_preserves_outcome():
    """Verify that a failure in the memory retain adapter does not crash or corrupt the recorded experiment outcome."""
    failing_retain = MagicMock()
    failing_retain.retain_experiment_outcome.side_effect = RuntimeError("Hindsight PostgreSQL storage offline")

    rec = SEORecommendation(
        recommendation_id="rec_audit_009",
        project_id="audit_proj",
        url="https://demo-searchmind-store.example/products/boots",
        recommendation_type="title_tag_optimization",
        recommendation="Test commercial title tag.",
        current_evidence="CTR drop",
        confidence=0.55,
        requires_approval=True,
    )

    service = ExperimentExecutionService()
    result = service.execute_learning_loop(
        recommendation=rec,
        approval_status=ApprovalStatus.APPROVED,
        measured_value=2.8,
        retain_adapter=failing_retain,
        experiment_id="exp_retain_fail_test",
    )

    # Pipeline should complete and record experiment and outcome
    assert result["experiment"].status == ExperimentStatus.COMPLETED
    assert result["experiment"].experiment_id == "exp_retain_fail_test"
    assert result["outcome"].absolute_change == 1.0  # 2.8 - 1.8 default baseline
    assert result["retain_result"].retained is False
    assert result["retain_result"].source == "error"
    # Experiment is safely recorded in service
    assert "exp_retain_fail_test" in service.experiments
    assert "exp_retain_fail_test" in service.outcomes


# -----------------------------------------------------------------------------
# 10. Audit: Existing Historical Dataset Files Remain Strictly Immutable
# -----------------------------------------------------------------------------
def test_audit_historical_dataset_immutability():
    """Audit guarantee: Dataset files in data/demo/ remain completely untouched during workflows and experiments."""
    data_files = list(DATA_DIR.glob("*.json"))
    assert len(data_files) > 0, f"No JSON data files found in {DATA_DIR}"

    # Compute baseline SHA-256 hashes
    initial_hashes = {}
    for f in data_files:
        content = f.read_bytes()
        initial_hashes[f.name] = hashlib.sha256(content).hexdigest()

    # Execute dataset loading, workflow analysis, and end-to-end learning demo
    load_demo_dataset()
    demo_output = run_full_learning_loop_demo()
    assert demo_output["future_available"] is True

    # Verify that all files have identical SHA-256 hashes
    for f in data_files:
        post_content = f.read_bytes()
        post_hash = hashlib.sha256(post_content).hexdigest()
        assert (
            post_hash == initial_hashes[f.name]
        ), f"Historical dataset file '{f.name}' was unexpectedly modified!"
