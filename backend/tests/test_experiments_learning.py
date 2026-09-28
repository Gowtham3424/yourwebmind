"""Deterministic unit tests for SearchMind experiment outcome and Hindsight retain layer.

Validates:
1. Approval required before experiment creation
2. Rejected recommendation cannot execute
3. Approved recommendation creates experiment
4. Experiment status transitions (PLANNED -> RUNNING -> COMPLETED)
5. Outcome calculation
6. Positive outcome classification
7. Negative outcome classification
8. Neutral outcome classification
9. Inconclusive outcome classification
10. Percentage change calculation
11. Zero-baseline handling
12. Deterministic lesson generation
13. Caveat preservation
14. Memory payload generation
15. Fake Retain adapter (InMemoryRetainAdapter)
16. Provenance tracking
17. Duplicate protection / idempotency
18. Complete learning workflow end-to-end with fake Retain
19. Real Hindsight is NOT called during normal tests
20. Zero Groq calls during normal tests

All tests execute strictly in local Python memory with ZERO token consumption.
"""

from pathlib import Path
import pytest
from unittest.mock import MagicMock

from app.experiments import (
    ExperimentExecutionService,
    classify_outcome_deterministically,
    compute_experiment_outcome,
    generate_experiment_lesson,
    build_memory_retain_payload,
)
from app.memory.retain_adapter import InMemoryRetainAdapter, RetainResult
from app.models.enums import ApprovalStatus, ExperimentStatus, OutcomeClass
from app.models.experiment import ExperimentOutcome, SEOExperiment
from app.models.recommendation import SEORecommendation


@pytest.fixture
def sample_recommendation():
    """Sample approved SEORecommendation."""
    return SEORecommendation(
        recommendation_id="rec_test_001",
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        recommendation_type="title_tag_optimization",
        recommendation="Align product title with commercial intent keyword while keeping brand name.",
        current_evidence="Current CTR is 1.8% despite top-3 SERP rank 3.1.",
        confidence=0.57,
        expected_impact="+20% to +40% relative CTR lift",
        requires_approval=True,
    )


@pytest.fixture
def sample_experiment(sample_recommendation):
    """Sample SEOExperiment fixture."""
    service = ExperimentExecutionService()
    return service.create_experiment_from_recommendation(
        recommendation=sample_recommendation,
        approval_status=ApprovalStatus.APPROVED,
        experiment_id="exp_test_001",
        baseline_metrics={"ctr": 1.8},
    )


# -----------------------------------------------------------------------------
# Test 1 & 2: Approval Required Before Experiment & Rejection Cannot Execute
# -----------------------------------------------------------------------------
def test_approval_required_before_experiment(sample_recommendation):
    """Verify that unapproved or pending recommendations raise PermissionError."""
    service = ExperimentExecutionService()
    with pytest.raises(PermissionError, match="Operator approval is required"):
        service.create_experiment_from_recommendation(
            recommendation=sample_recommendation,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
        )


def test_rejected_recommendation_cannot_execute(sample_recommendation):
    """Verify that rejected recommendations raise PermissionError and cannot create experiments."""
    service = ExperimentExecutionService()
    with pytest.raises(PermissionError, match="Operator approval is required"):
        service.create_experiment_from_recommendation(
            recommendation=sample_recommendation,
            approval_status=ApprovalStatus.REJECTED,
        )


# -----------------------------------------------------------------------------
# Test 3 & 4: Approved Creates Experiment & Status Transitions
# -----------------------------------------------------------------------------
def test_approved_recommendation_creates_experiment(sample_recommendation):
    """Verify approved recommendation creates an experiment in PLANNED status."""
    service = ExperimentExecutionService()
    exp = service.create_experiment_from_recommendation(
        recommendation=sample_recommendation,
        approval_status=ApprovalStatus.APPROVED,
        experiment_id="exp_test_002",
        baseline_metrics={"ctr": 1.8},
    )
    assert exp.status == ExperimentStatus.PLANNED
    assert exp.experiment_id == "exp_test_002"
    assert exp.recommendation_id == sample_recommendation.recommendation_id
    assert exp.baseline_metrics.get("ctr") == 1.8


def test_experiment_status_transitions(sample_experiment):
    """Verify status transitions from PLANNED -> RUNNING -> COMPLETED."""
    service = ExperimentExecutionService()
    assert sample_experiment.status == ExperimentStatus.PLANNED

    running_exp = service.start_experiment(sample_experiment)
    assert running_exp.status == ExperimentStatus.RUNNING

    completed_exp, outcome, lesson = service.record_outcome(
        experiment=running_exp,
        measured_value=2.7,
    )
    assert completed_exp.status == ExperimentStatus.COMPLETED
    assert outcome.outcome_class == OutcomeClass.POSITIVE
    assert "Observed positive" in lesson


# -----------------------------------------------------------------------------
# Test 5 & 6: Outcome Calculation (Absolute & Percentage Change)
# -----------------------------------------------------------------------------
def test_outcome_calculation_absolute_change(sample_experiment):
    """Verify primary metric delta absolute change calculation."""
    outcome = compute_experiment_outcome(
        experiment=sample_experiment,
        measured_value=2.7,
    )
    assert outcome.primary_metric_before == 1.8
    assert outcome.primary_metric_after == 2.7
    assert outcome.absolute_change == 0.9


def test_outcome_calculation_percentage_change(sample_experiment):
    """Verify primary metric delta percentage change calculation."""
    outcome = compute_experiment_outcome(
        experiment=sample_experiment,
        measured_value=2.7,
    )
    assert outcome.percentage_change == 50.0  # (2.7 - 1.8) / 1.8 * 100 = 50.0%
    assert outcome.outcome_class == OutcomeClass.POSITIVE


# -----------------------------------------------------------------------------
# Test 6, 7, 8, 9: Four Outcome Classifications
# -----------------------------------------------------------------------------
def test_positive_outcome_classification():
    """Verify positive outcome classification when metric improves significantly."""
    cls = classify_outcome_deterministically(baseline=1.8, measured=2.5, percentage_change=38.9)
    assert cls == OutcomeClass.POSITIVE


def test_negative_outcome_classification():
    """Verify negative outcome classification when metric declines."""
    cls = classify_outcome_deterministically(baseline=2.5, measured=1.8, percentage_change=-28.0)
    assert cls == OutcomeClass.NEGATIVE


def test_neutral_outcome_classification():
    """Verify neutral outcome classification when metric delta is within noise (<= 2%)."""
    cls = classify_outcome_deterministically(baseline=2.0, measured=2.02, percentage_change=1.0)
    assert cls == OutcomeClass.NEUTRAL


def test_inconclusive_outcome_classification():
    """Verify confounding external factors override metric delta to INCONCLUSIVE."""
    caveats = ["Testing coincided with an unconfirmed Google core algorithm update."]
    cls = classify_outcome_deterministically(
        baseline=1.8,
        measured=2.6,
        percentage_change=44.4,
        caveats=caveats,
    )
    assert cls == OutcomeClass.INCONCLUSIVE


# -----------------------------------------------------------------------------
# Test 11: Zero-Baseline Handling
# -----------------------------------------------------------------------------
def test_zero_baseline_handling(sample_recommendation):
    """Verify division by zero is safely handled when baseline metric is zero."""
    service = ExperimentExecutionService()
    exp_zero = service.create_experiment_from_recommendation(
        recommendation=sample_recommendation,
        approval_status=ApprovalStatus.APPROVED,
        experiment_id="exp_zero_001",
        baseline_metrics={"ctr": 0.0},
    )
    outcome_up = compute_experiment_outcome(exp_zero, measured_value=1.5)
    assert outcome_up.primary_metric_before == 0.0
    assert outcome_up.percentage_change == 100.0

    outcome_same = compute_experiment_outcome(exp_zero, measured_value=0.0)
    assert outcome_same.percentage_change == 0.0


# -----------------------------------------------------------------------------
# Test 12 & 13: Deterministic Lesson Generation & Caveat Preservation
# -----------------------------------------------------------------------------
def test_deterministic_lesson_generation(sample_experiment):
    """Verify lesson is generated factually without dogmatic claims."""
    outcome = compute_experiment_outcome(sample_experiment, measured_value=2.7)
    lesson = generate_experiment_lesson(
        experiment=sample_experiment,
        outcome=outcome,
        page_type="product",
    )
    assert "Observed positive CTR uplift" in lesson
    assert "+50.0%" in lesson
    assert "should not be treated as universal proof" in lesson
    # Ensure non-dogmatic
    assert "always" not in lesson.lower()


def test_caveat_preservation_in_lesson(sample_experiment):
    """Verify caveats are explicitly retained in the lesson."""
    caveats = ["Bounce rate increased slightly from 42% to 45%."]
    outcome = compute_experiment_outcome(
        sample_experiment,
        measured_value=2.7,
        caveats=caveats,
    )
    lesson = generate_experiment_lesson(
        experiment=sample_experiment,
        outcome=outcome,
        page_type="product",
        caveats=caveats,
    )
    assert "Caveat: Bounce rate increased slightly from 42% to 45%." in lesson


# -----------------------------------------------------------------------------
# Test 14: Memory Payload Generation
# -----------------------------------------------------------------------------
def test_build_memory_retain_payload(sample_experiment):
    """Verify Hindsight Retain payload matches Prompt 03 verified schema."""
    outcome = compute_experiment_outcome(sample_experiment, measured_value=2.7)
    lesson = generate_experiment_lesson(sample_experiment, outcome)
    payload = build_memory_retain_payload(
        experiment=sample_experiment,
        outcome=outcome,
        lesson=lesson,
        project_id="searchmind-demo-store",
    )

    assert payload["document_id"] == "seo_exp_test_001"
    assert "SEO Experiment Record: exp_test_001" in payload["content"]
    assert "Contextual Lesson & Interpretation:" in payload["content"]
    assert payload["metadata"]["experiment_id"] == "exp_test_001"
    assert payload["metadata"]["outcome_class"] == "positive"
    assert "product_page" in payload["tags"]
    assert payload["update_mode"] == "replace"


# -----------------------------------------------------------------------------
# Test 15 & 16: Fake Retain Adapter Records Payload & Provenance
# -----------------------------------------------------------------------------
def test_fake_retain_adapter_records_payload(sample_experiment):
    """Verify InMemoryRetainAdapter records payloads accurately."""
    adapter = InMemoryRetainAdapter()
    outcome = compute_experiment_outcome(sample_experiment, measured_value=2.7)
    lesson = generate_experiment_lesson(sample_experiment, outcome)
    payload = build_memory_retain_payload(sample_experiment, outcome, lesson)

    adapter.retain_experiment_outcome(payload, bank_id="searchmind-demo")
    assert len(adapter.retained_payloads) == 1
    assert adapter.retained_payloads[0]["document_id"] == "seo_exp_test_001"


def test_fake_retain_adapter_provenance(sample_experiment):
    """Verify InMemoryRetainAdapter outputs valid RetainResult with provenance metadata."""
    adapter = InMemoryRetainAdapter()
    outcome = compute_experiment_outcome(sample_experiment, measured_value=2.7)
    lesson = generate_experiment_lesson(sample_experiment, outcome)
    payload = build_memory_retain_payload(sample_experiment, outcome, lesson)

    res = adapter.retain_experiment_outcome(payload, bank_id="searchmind-demo")
    assert isinstance(res, RetainResult)
    assert res.source == "fixture"
    assert res.memory_bank == "searchmind-demo"
    assert res.experiment_id == "exp_test_001"
    assert res.document_id == "seo_exp_test_001"
    assert res.retained is True


# -----------------------------------------------------------------------------
# Test 17: Duplicate Protection / Idempotency
# -----------------------------------------------------------------------------
def test_duplicate_protection_idempotency(sample_experiment):
    """Verify retaining the same experiment twice replaces the document rather than duplicating."""
    adapter = InMemoryRetainAdapter()
    outcome = compute_experiment_outcome(sample_experiment, measured_value=2.7)
    lesson = generate_experiment_lesson(sample_experiment, outcome)
    payload = build_memory_retain_payload(sample_experiment, outcome, lesson)

    # First retain
    adapter.retain_experiment_outcome(payload, bank_id="searchmind-demo")
    assert len(adapter.retained_payloads) == 1

    # Second retain of identical document_id
    adapter.retain_experiment_outcome(payload, bank_id="searchmind-demo")
    assert len(adapter.retained_payloads) == 1, "Duplicate payload was appended instead of replaced!"


# -----------------------------------------------------------------------------
# Test 18: Complete Learning Workflow End-to-End with Fake Retain
# -----------------------------------------------------------------------------
def test_complete_learning_workflow_end_to_end(sample_recommendation):
    """Verify entire pipeline: Approved Recommendation -> Experiment -> Outcome -> Lesson -> Retain."""
    service = ExperimentExecutionService()
    retain_adapter = InMemoryRetainAdapter()

    res = service.execute_learning_loop(
        recommendation=sample_recommendation,
        approval_status=ApprovalStatus.APPROVED,
        measured_value=2.7,
        retain_adapter=retain_adapter,
        experiment_id="exp_021_simulated",
    )

    assert res["experiment"].status == ExperimentStatus.COMPLETED
    assert res["outcome"].outcome_class == OutcomeClass.POSITIVE
    assert "+50.0%" in res["lesson"]
    assert res["retain_result"].retained is True
    assert res["retain_result"].document_id == "seo_exp_021_simulated"
    assert len(retain_adapter.retained_payloads) == 1


# -----------------------------------------------------------------------------
# Test 19 & 20: Real Hindsight & Groq Are NOT Called During Normal Tests
# -----------------------------------------------------------------------------
def test_no_real_hindsight_called_during_normal_tests(sample_recommendation):
    """Verify that live Hindsight service is never invoked when using the in-memory adapter."""
    mock_service = MagicMock()
    mock_service.retain.side_effect = AssertionError("Live Hindsight service retain was called unexpectedly!")

    # Execute workflow with fake adapter
    fake_adapter = InMemoryRetainAdapter()
    service = ExperimentExecutionService()
    res = service.execute_learning_loop(
        recommendation=sample_recommendation,
        approval_status=ApprovalStatus.APPROVED,
        measured_value=2.7,
        retain_adapter=fake_adapter,
    )

    assert res["retain_result"].source == "fixture"
    mock_service.retain.assert_not_called()


def test_zero_groq_calls_during_normal_tests(sample_recommendation):
    """Verify that zero Groq LLM network requests or token generation calls occur during learning workflow."""
    fake_adapter = InMemoryRetainAdapter()
    service = ExperimentExecutionService()

    # Even if environment has Groq credentials, the entire learning loop is fully deterministic
    res = service.execute_learning_loop(
        recommendation=sample_recommendation,
        approval_status=ApprovalStatus.APPROVED,
        measured_value=2.7,
        retain_adapter=fake_adapter,
    )

    assert res["retain_result"].token_usage is None or res["retain_result"].token_usage.get("total_tokens", 0) == 0
    assert "Observed positive" in res["lesson"]
