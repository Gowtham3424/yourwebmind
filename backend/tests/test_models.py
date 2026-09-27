"""Unit tests for SearchMind SEO domain models and validation rules."""

from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from app.models import (
    ExperimentOutcome,
    ExperimentStatus,
    ObservationSeverity,
    OptimizationDecision,
    OutcomeClass,
    SEOExperiment,
    SEOObservation,
    SEORecommendation,
    SearchIntent,
    WebsiteFact,
)


# ------------------------------------------------------------------------------
# WebsiteFact Tests
# ------------------------------------------------------------------------------


def test_valid_website_fact_creation():
    """Verify valid creation of WebsiteFact model with all expected types."""
    fact = WebsiteFact(
        project_id="proj_ecommerce_01",
        url="https://example.com/products/hiking-boots",
        page_type="product",
        title="Best Waterproof Hiking Boots 2026 | Example Store",
        meta_description="Discover top-rated waterproof hiking boots built for tough trails.",
        primary_keyword="waterproof hiking boots",
        secondary_keywords=["trail footwear", "leather hiking shoes"],
        search_intent=SearchIntent.COMMERCIAL,
        word_count=1450,
        canonical_url="https://example.com/products/hiking-boots",
        indexable=True,
        status_code=200,
    )
    assert fact.project_id == "proj_ecommerce_01"
    assert str(fact.url) == "https://example.com/products/hiking-boots"
    assert fact.search_intent == SearchIntent.COMMERCIAL
    assert fact.word_count == 1450
    assert fact.status_code == 200
    assert isinstance(fact.observed_at, datetime)


def test_invalid_website_fact_url_rejected():
    """Ensure invalid URLs are rejected by Pydantic validation."""
    with pytest.raises(ValidationError) as exc_info:
        WebsiteFact(
            project_id="proj_01",
            url="not-a-valid-url",
            title="Hiking Boots",
        )
    assert "url" in str(exc_info.value).lower()


def test_invalid_negative_word_count_rejected():
    """Ensure negative word counts are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        WebsiteFact(
            project_id="proj_01",
            url="https://example.com/page",
            title="Example Title",
            word_count=-50,
        )
    assert "word_count" in str(exc_info.value).lower()


def test_empty_project_id_rejected():
    """Ensure whitespace-only or empty project IDs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        WebsiteFact(
            project_id="   ",
            url="https://example.com/page",
            title="Example Title",
        )
    assert "project_id" in str(exc_info.value).lower()


# ------------------------------------------------------------------------------
# SEOObservation Tests
# ------------------------------------------------------------------------------


def test_valid_seo_observation_creation():
    """Verify creation of SEOObservation with auto-calculated delta."""
    obs = SEOObservation(
        observation_id="obs_101",
        project_id="proj_01",
        url="https://example.com/products/boots",
        keyword="waterproof hiking boots",
        observation_type="low_ctr",
        metric_name="ctr",
        current_value=1.8,
        previous_value=3.2,
        unit="%",
        severity=ObservationSeverity.HIGH,
        evidence={"position": 3.1, "impressions": 12500, "clicks": 225},
    )
    assert obs.observation_id == "obs_101"
    assert obs.severity == ObservationSeverity.HIGH
    assert obs.delta == -1.4
    assert obs.evidence["impressions"] == 12500


def test_invalid_severity_rejected():
    """Ensure invalid severity strings outside controlled enum are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        SEOObservation(
            observation_id="obs_102",
            project_id="proj_01",
            url="https://example.com/page",
            observation_type="low_ctr",
            metric_name="ctr",
            current_value=1.5,
            severity="extreme_danger",  # Invalid enum value
        )
    assert "severity" in str(exc_info.value).lower()


# ------------------------------------------------------------------------------
# OptimizationDecision Tests
# ------------------------------------------------------------------------------


def test_valid_optimization_decision_creation():
    """Verify valid creation of an OptimizationDecision model."""
    decision = OptimizationDecision(
        decision_id="dec_201",
        project_id="proj_01",
        url="https://example.com/products/boots",
        observation_ids=["obs_101"],
        decision_type="title_update",
        hypothesis="Aligning title tag with commercial intent will increase SERP CTR.",
        rationale="Page ranks position 3 for commercial query, but title reads like an informational blog post.",
        expected_effect="+1.0% CTR increase within 14 days",
        proposed_changes={
            "field": "title",
            "from": "Hiking Boots: A Deep Dive Guide",
            "to": "Buy Waterproof Hiking Boots | Free Shipping & Returns",
        },
    )
    assert decision.decision_id == "dec_201"
    assert decision.decision_type == "title_update"
    assert "Aligning title tag" in decision.hypothesis
    assert decision.proposed_changes["field"] == "title"


# ------------------------------------------------------------------------------
# SEOExperiment Tests
# ------------------------------------------------------------------------------


def test_valid_seo_experiment_creation():
    """Verify valid SEOExperiment model instantiation."""
    now = datetime.now(timezone.utc)
    experiment = SEOExperiment(
        experiment_id="exp_301",
        project_id="proj_01",
        url="https://example.com/products/boots",
        experiment_type="title_tag_test",
        hypothesis="Commercial title tag increases CTR from 1.8% to over 3.0%.",
        control_description="Hiking Boots: A Deep Dive Guide",
        treatment_description="Buy Waterproof Hiking Boots | Free Shipping & Returns",
        primary_metric="ctr",
        secondary_metrics=["clicks", "impressions", "position"],
        baseline_metrics={"ctr": 1.8, "position": 3.1, "clicks": 225},
        start_date=now,
        end_date=now + timedelta(days=14),
        status=ExperimentStatus.RUNNING,
    )
    assert experiment.experiment_id == "exp_301"
    assert experiment.status == ExperimentStatus.RUNNING
    assert experiment.primary_metric == "ctr"
    assert experiment.end_date > experiment.start_date


def test_experiment_end_date_before_start_date_rejected():
    """Ensure end_date prior to start_date triggers a validation error."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        SEOExperiment(
            experiment_id="exp_302",
            project_id="proj_01",
            url="https://example.com/products/boots",
            experiment_type="title_tag_test",
            hypothesis="Test hypothesis",
            control_description="Control",
            treatment_description="Treatment",
            primary_metric="ctr",
            start_date=now,
            end_date=now - timedelta(days=2),  # Invalid: in the past relative to start
        )
    assert "end_date cannot be before start_date" in str(exc_info.value)


# ------------------------------------------------------------------------------
# ExperimentOutcome Tests
# ------------------------------------------------------------------------------


def test_valid_experiment_outcome_creation():
    """Verify valid ExperimentOutcome creation and automated calculation."""
    outcome = ExperimentOutcome(
        outcome_id="out_401",
        experiment_id="exp_301",
        project_id="proj_01",
        primary_metric_before=1.8,
        primary_metric_after=3.1,
        outcome_class=OutcomeClass.POSITIVE,
        interpretation="Commercial title alignment drove 72% relative CTR improvement without degrading rankings.",
        metric_results={"impressions_after": 13100, "clicks_after": 406, "position_after": 2.9},
    )
    assert outcome.outcome_id == "out_401"
    assert outcome.outcome_class == OutcomeClass.POSITIVE
    assert outcome.absolute_change == 1.3
    assert outcome.percentage_change == 72.22


def test_experiment_outcome_zero_baseline_with_positive_after():
    """Verify that when baseline is 0 and after > 0, percentage_change is None and absolute_change is recorded."""
    outcome = ExperimentOutcome(
        outcome_id="out_zero_01",
        experiment_id="exp_301",
        project_id="proj_01",
        primary_metric_before=0.0,
        primary_metric_after=15.0,
        outcome_class=OutcomeClass.POSITIVE,
        interpretation="Page went from zero clicks to 15 clicks after initial indexation.",
    )
    assert outcome.absolute_change == 15.0
    assert outcome.percentage_change is None  # Undefined mathematically from zero baseline


def test_experiment_outcome_both_before_and_after_zero():
    """Verify that when both baseline and after are 0, percentage_change and absolute_change are 0.0."""
    outcome = ExperimentOutcome(
        outcome_id="out_zero_02",
        experiment_id="exp_301",
        project_id="proj_01",
        primary_metric_before=0.0,
        primary_metric_after=0.0,
        outcome_class=OutcomeClass.NEUTRAL,
        interpretation="No change observed; metric stayed at zero.",
    )
    assert outcome.absolute_change == 0.0
    assert outcome.percentage_change == 0.0


def test_experiment_outcome_negative_baseline():
    """Verify directional percentage change when baseline is negative (e.g., negative ranking delta)."""
    outcome = ExperimentOutcome(
        outcome_id="out_neg_01",
        experiment_id="exp_301",
        project_id="proj_01",
        primary_metric_before=-5.0,
        primary_metric_after=-2.0,
        outcome_class=OutcomeClass.POSITIVE,
        interpretation="Deficit reduced from -5 to -2.",
    )
    assert outcome.absolute_change == 3.0
    assert outcome.percentage_change == 60.0  # ((-2 - (-5)) / 5) * 100 = 60.0


@pytest.mark.parametrize(
    "outcome_class_val",
    [
        OutcomeClass.POSITIVE,
        OutcomeClass.NEGATIVE,
        OutcomeClass.NEUTRAL,
        OutcomeClass.INCONCLUSIVE,
    ],
)
def test_all_four_outcome_classes_accepted(outcome_class_val):
    """Ensure all four empirical outcome classifications are valid."""
    outcome = ExperimentOutcome(
        outcome_id=f"out_{outcome_class_val.value}",
        experiment_id="exp_301",
        project_id="proj_01",
        primary_metric_before=2.0,
        primary_metric_after=2.1,
        outcome_class=outcome_class_val,
        interpretation=f"Test outcome for {outcome_class_val.value}",
    )
    assert outcome.outcome_class == outcome_class_val


# ------------------------------------------------------------------------------
# SEORecommendation Tests
# ------------------------------------------------------------------------------


def test_valid_seo_recommendation_creation():
    """Verify creation of complete SEORecommendation with evidence separation."""
    rec = SEORecommendation(
        recommendation_id="rec_501",
        project_id="proj_01",
        url="https://example.com/products/boots",
        observation_ids=["obs_101"],
        recommendation_type="commercial_title_alignment",
        recommendation="Update title to emphasize commercial value propositions.",
        current_evidence="CTR is 1.8% despite top-3 average position.",
        historical_evidence="Previous title test exp_301 on similar commercial page was correlated with CTR improvement from 1.8% to 3.1%.",
        reflection="Prior test exp_301 suggests commercial title alignment may improve CTR for this intent, though results depend on SERP competition.",
        supporting_experiment_ids=["exp_301"],
        confidence=0.88,
        expected_impact="High (+50-70% CTR lift)",
        requires_approval=True,
    )
    assert rec.recommendation_id == "rec_501"
    assert rec.confidence == 0.88
    assert rec.requires_approval is True
    assert "exp_301" in rec.supporting_experiment_ids


def test_recommendation_can_exist_without_historical_evidence():
    """Ensure a new project without historical memory can create recommendations."""
    rec = SEORecommendation(
        recommendation_id="rec_502",
        project_id="new_project_zero_history",
        url="https://newbrand.com/products/widget",
        observation_ids=["obs_999"],
        recommendation_type="initial_title_fix",
        recommendation="Draft title matching primary keyword.",
        current_evidence="Page has default template title 'Home Page'.",
        historical_evidence=None,  # No historical memory yet
        reflection=None,  # No reflection yet
        confidence=0.4,
    )
    assert rec.historical_evidence is None
    assert rec.reflection is None
    assert rec.confidence == 0.4


# ------------------------------------------------------------------------------
# Serialization Tests
# ------------------------------------------------------------------------------


def test_to_hindsight_dict_serialization():
    """Verify models serialize to clean, JSON-compatible primitive dictionaries."""
    now = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    fact = WebsiteFact(
        project_id="proj_01",
        url="https://example.com/page",
        title="Example Page",
        search_intent=SearchIntent.INFORMATIONAL,
        word_count=500,
        observed_at=now,
    )
    payload = fact.to_hindsight_dict()

    assert isinstance(payload, dict)
    assert payload["project_id"] == "proj_01"
    # HttpUrl converted to string
    assert payload["url"] == "https://example.com/page"
    # Enum converted to string value
    assert payload["search_intent"] == "informational"
    # Datetime converted to ISO string
    assert "2026-09-27" in payload["observed_at"]
