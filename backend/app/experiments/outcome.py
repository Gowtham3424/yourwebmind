"""Deterministic outcome calculation and empirical classification for SEO experiments.

Converts measured post-experiment performance into an ExperimentOutcome model
without requiring LLM evaluation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.models.base import utc_now
from app.models.enums import OutcomeClass
from app.models.experiment import ExperimentOutcome, SEOExperiment

CONFOUNDING_KEYWORDS = [
    "algorithm update",
    "google update",
    "seasonal demand",
    "seasonal shift",
    "confounding",
    "insufficient sample",
    "tracking anomaly",
    "serp volatility",
]


def classify_outcome_deterministically(
    baseline: float,
    measured: float,
    percentage_change: float,
    primary_metric: str = "ctr",
    caveats: Optional[List[str]] = None,
) -> OutcomeClass:
    """
    Empirically classify outcome into positive, negative, neutral, or inconclusive.

    Rules:
    - Confounding external factors -> INCONCLUSIVE
    - Metric movement within normal noise (abs(pct) <= 2.0%) -> NEUTRAL
    - Positive metric movement -> POSITIVE
    - Negative metric movement -> NEGATIVE
    """
    # 1. Check for confounding factors
    if caveats:
        combined_caveats = " ".join(caveats).lower()
        if any(keyword in combined_caveats for keyword in CONFOUNDING_KEYWORDS):
            return OutcomeClass.INCONCLUSIVE

    # 2. Check for neutral variance
    # For ranking/position, lower is better; for ctr/clicks/impressions, higher is better
    is_rank_metric = primary_metric.lower() in ("position", "rank", "average_position")

    if abs(percentage_change) <= 2.0:
        return OutcomeClass.NEUTRAL

    if is_rank_metric:
        # Ranking improved (position number decreased: e.g. 5.0 -> 3.0)
        return OutcomeClass.POSITIVE if measured < baseline else OutcomeClass.NEGATIVE
    else:
        # CTR or clicks improved
        return OutcomeClass.POSITIVE if measured > baseline else OutcomeClass.NEGATIVE


def compute_experiment_outcome(
    experiment: SEOExperiment,
    measured_value: float,
    secondary_results: Optional[Dict[str, Any]] = None,
    caveats: Optional[List[str]] = None,
    confidence_note: Optional[str] = None,
    outcome_id: Optional[str] = None,
    measured_at: Optional[datetime] = None,
) -> ExperimentOutcome:
    """
    Deterministically calculate metric deltas and generate an ExperimentOutcome record.

    Guarantees:
    - Zero division safety on zero-baseline metrics
    - Factual delta and percentage calculations
    - Contextual qualification via caveats
    """
    baseline_value = experiment.baseline_metrics.get(experiment.primary_metric, 0.0)
    abs_change = round(measured_value - baseline_value, 4)

    # Zero-baseline calculation
    if baseline_value == 0.0:
        if measured_value > 0.0:
            pct_change = 100.0
        elif measured_value < 0.0:
            pct_change = -100.0
        else:
            pct_change = 0.0
    else:
        pct_change = round((measured_value - baseline_value) / abs(baseline_value) * 100.0, 2)

    outcome_cls = classify_outcome_deterministically(
        baseline=baseline_value,
        measured=measured_value,
        percentage_change=pct_change,
        primary_metric=experiment.primary_metric,
        caveats=caveats,
    )

    # Build factual interpretation
    interp_parts = [
        f"Primary metric '{experiment.primary_metric}' changed from {baseline_value} to {measured_value} "
        f"({pct_change:+.1f}% relative change) during the trial."
    ]

    if outcome_cls == OutcomeClass.POSITIVE:
        interp_parts.append(
            f"Observed positive outcome for {experiment.experiment_type} on {experiment.url}. "
            "Optimization coincided with target performance lift."
        )
    elif outcome_cls == OutcomeClass.NEGATIVE:
        interp_parts.append(
            f"Observed negative performance decline for {experiment.experiment_type} on {experiment.url}. "
            "Treatment underperformed baseline control."
        )
    elif outcome_cls == OutcomeClass.NEUTRAL:
        interp_parts.append(
            f"Observed neutral metric movement ({pct_change:+.1f}%) within natural SERP volatility boundaries."
        )
    elif outcome_cls == OutcomeClass.INCONCLUSIVE:
        interp_parts.append(
            "Outcome classified as inconclusive due to concurrent external confounding factors."
        )

    if caveats:
        for c in caveats:
            interp_parts.append(f"Caveat: {c.strip()}")

    interpretation_text = " ".join(interp_parts)

    all_metric_results = {
        experiment.primary_metric: {
            "before": baseline_value,
            "after": measured_value,
            "abs_change": abs_change,
            "pct_change": pct_change,
        }
    }
    if secondary_results:
        all_metric_results.update(secondary_results)

    oid = outcome_id or f"out_{uuid.uuid4().hex[:8]}"

    return ExperimentOutcome(
        outcome_id=oid,
        experiment_id=experiment.experiment_id,
        project_id=experiment.project_id,
        metric_results=all_metric_results,
        primary_metric_before=baseline_value,
        primary_metric_after=measured_value,
        absolute_change=abs_change,
        percentage_change=pct_change,
        outcome_class=outcome_cls,
        confidence_note=confidence_note or (
            "Empirical observation over 28-day window." if not caveats else "Observed with recorded caveats."
        ),
        interpretation=interpretation_text,
        measured_at=measured_at or utc_now(),
    )
