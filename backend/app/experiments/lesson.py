"""Deterministic factual lesson generator and Hindsight memory payload builder.

Translates empirical experiment outcomes into non-dogmatic knowledge units
suitable for persistent retention in Hindsight memory.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.enums import OutcomeClass
from app.models.experiment import ExperimentOutcome, SEOExperiment


def generate_experiment_lesson(
    experiment: SEOExperiment,
    outcome: ExperimentOutcome,
    page_type: Optional[str] = None,
    technique: Optional[str] = None,
    caveats: Optional[List[str]] = None,
) -> str:
    """
    Generate a deterministic factual lesson from an experiment outcome.

    Strict rules:
    - Never uses absolute claims ("this strategy always works")
    - Explicitly bounds the finding to the tested page type and context
    - Distinguishes observed outcome from universal causal law
    - Integrates contextual caveats
    """
    pt = page_type or "target"
    tech = (technique or experiment.experiment_type).replace("_", " ")
    pct_str = f"{outcome.percentage_change:+.1f}%" if outcome.percentage_change is not None else "measured change"
    metric = experiment.primary_metric

    ocls = outcome.outcome_class
    if hasattr(ocls, "value"):
        ocls_val = ocls.value
    else:
        ocls_val = str(ocls).lower()

    if ocls_val == "positive":
        lesson = (
            f"Observed positive {metric.upper()} uplift ({pct_str}, {outcome.primary_metric_before} to {outcome.primary_metric_after}) "
            f"after testing {tech} on this {pt} page. "
            f"Result is contextual to the observed page and should not be treated as universal proof."
        )
    elif ocls_val == "negative":
        lesson = (
            f"Observed negative {metric.upper()} decline ({pct_str}, {outcome.primary_metric_before} to {outcome.primary_metric_after}) "
            f"after applying {tech} on this {pt} page. "
            f"This tactic degraded performance in this specific context and warrants caution or alternative testing."
        )
    elif ocls_val == "neutral":
        lesson = (
            f"Observed neutral impact ({pct_str}) within natural SERP variance after testing {tech} on this {pt} page. "
            f"No statistically meaningful {metric.upper()} movement was detected."
        )
    else:  # inconclusive
        lesson = (
            f"Observed metric movement for {tech} on this {pt} page, but concurrent external factors "
            f"prevent confident causal attribution. Controlled re-testing under stable SERP conditions is advised."
        )

    if caveats:
        for c in caveats:
            lesson += f" Caveat: {c.strip()}"

    return lesson


def build_memory_retain_payload(
    experiment: SEOExperiment,
    outcome: ExperimentOutcome,
    lesson: str,
    project_id: str = "searchmind-demo-store",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Construct the complete Hindsight Retain payload for persistent storage.

    Formatted according to SearchMind's verified natural language memory document structure:
    - Experiment ID and Page URL
    - Baseline and Hypothesis
    - Control vs Treatment
    - Measured results and percentage change
    - Contextual lesson and non-dogmatic interpretation
    """
    doc_id = f"seo_{experiment.experiment_id}"
    exp_type = experiment.experiment_type
    metric = experiment.primary_metric
    before = outcome.primary_metric_before
    after = outcome.primary_metric_after
    pct = outcome.percentage_change
    pct_str = f" ({pct:+.2f}%)" if pct is not None else ""
    ocls_str = (
        outcome.outcome_class.value
        if hasattr(outcome.outcome_class, "value")
        else str(outcome.outcome_class)
    ).upper()

    measured_date = outcome.measured_at.strftime("%Y-%m-%d")

    # High-signal natural language synthesis document matching Prompt 03 verified schema
    content = (
        f"SEO Experiment Record: {experiment.experiment_id}\n"
        f"Page: {experiment.url}\n"
        f"Experiment Type: {exp_type}\n"
        f"Date Concluded: {measured_date}\n\n"
        f"Context & Baseline:\n"
        f"Before this test, the primary metric '{metric}' was measured at {before}.\n"
        f"Hypothesis: {experiment.hypothesis}\n\n"
        f"Tested Optimization:\n"
        f"- Control: {experiment.control_description}\n"
        f"- Treatment: {experiment.treatment_description}\n\n"
        f"Observed Results:\n"
        f"Primary metric '{metric}' changed from {before} to {after}{pct_str}.\n"
        f"Outcome Classification: {ocls_str}\n\n"
        f"Contextual Lesson & Interpretation:\n"
        f"{lesson}\n"
    )

    combined_tags = [
        "seo_experiment",
        exp_type,
        ocls_str.lower(),
        "searchmind_learning_loop",
    ]
    if tags:
        combined_tags.extend(tags)

    u_str = str(experiment.url).lower()
    if "/product/" in u_str or "/products/" in u_str:
        combined_tags.append("product_page")
    elif "/collections/" in u_str or "/category/" in u_str:
        combined_tags.append("category_page")

    return {
        "document_id": doc_id,
        "content": content,
        "context": f"SearchMind experiment {experiment.experiment_id} outcome on {experiment.url}",
        "metadata": {
            "experiment_id": experiment.experiment_id,
            "project_id": project_id,
            "url": str(experiment.url),
            "experiment_type": exp_type,
            "outcome_class": ocls_str.lower(),
            "primary_metric": metric,
        },
        "tags": combined_tags,
        "timestamp": outcome.measured_at,
        "update_mode": "replace",
    }
