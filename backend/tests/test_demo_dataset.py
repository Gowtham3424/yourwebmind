"""Unit tests for SearchMind synthetic SEO dataset and validation.

These tests are strictly deterministic and make NO external API or LLM calls.
"""

import json
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models import (
    ExperimentOutcome,
    OptimizationDecision,
    SEOObservation,
    SEOExperiment,
    WebsiteFact,
)
from app.seo.demo_dataset import (
    build_hindsight_memory_documents,
    load_demo_dataset,
    validate_demo_dataset,
)


def test_load_demo_dataset_all_files():
    """Verify all 7 dataset files exist and load as non-empty dictionaries/lists."""
    data = load_demo_dataset()
    expected_keys = [
        "pages",
        "keywords",
        "rankings",
        "observations",
        "decisions",
        "experiments",
        "outcomes",
    ]
    for key in expected_keys:
        assert key in data, f"Missing key '{key}' in loaded dataset"
        assert len(data[key]) > 0, f"Dataset file for '{key}' is empty"


def test_dataset_minimum_record_counts():
    """Verify dataset meets or exceeds all minimum record count thresholds."""
    data = load_demo_dataset()
    assert len(data["pages"]) >= 30, f"Expected >= 30 pages, got {len(data['pages'])}"
    assert len(data["keywords"]) >= 100, f"Expected >= 100 keywords, got {len(data['keywords'])}"
    assert len(data["rankings"]) >= 60, f"Expected >= 60 rankings, got {len(data['rankings'])}"
    assert len(data["observations"]) >= 40, f"Expected >= 40 observations, got {len(data['observations'])}"
    assert len(data["decisions"]) >= 20, f"Expected >= 20 decisions, got {len(data['decisions'])}"
    assert len(data["experiments"]) == 20, f"Expected exactly 20 experiments, got {len(data['experiments'])}"
    assert len(data["outcomes"]) == 20, f"Expected exactly 20 outcomes, got {len(data['outcomes'])}"


def test_dataset_validation_passes_cleanly():
    """Verify validate_demo_dataset() returns valid=True and no errors."""
    report = validate_demo_dataset()
    assert report["valid"] is True, f"Dataset validation failed: {report['errors']}"
    assert len(report["errors"]) == 0


def test_pydantic_validation_pages():
    """Verify every page in the dataset parses strictly as a WebsiteFact model."""
    data = load_demo_dataset()
    for page_dict in data["pages"]:
        page = WebsiteFact.model_validate(page_dict)
        assert page.project_id == "searchmind-demo-store"
        assert str(page.url).startswith("https://demo-searchmind-store.example")
        assert page.word_count > 0


def test_pydantic_validation_observations():
    """Verify every observation in the dataset parses strictly as an SEOObservation model."""
    data = load_demo_dataset()
    for obs_dict in data["observations"]:
        obs = SEOObservation.model_validate(obs_dict)
        assert obs.project_id == "searchmind-demo-store"
        assert obs.severity in ["info", "low", "medium", "high", "critical"]


def test_pydantic_validation_decisions():
    """Verify every decision in the dataset parses strictly as an OptimizationDecision model."""
    data = load_demo_dataset()
    for dec_dict in data["decisions"]:
        dec = OptimizationDecision.model_validate(dec_dict)
        assert dec.project_id == "searchmind-demo-store"
        assert dec.decision_type in [
            "title_update",
            "meta_description_test",
            "content_refresh",
            "internal_linking",
            "schema_update",
            "keyword_alignment",
            "FAQ_content",
            "category_copy_update",
        ]


def test_pydantic_validation_experiments_and_outcomes():
    """Verify all experiments and outcomes parse strictly as Pydantic models."""
    data = load_demo_dataset()
    for exp_dict in data["experiments"]:
        exp = SEOExperiment.model_validate(exp_dict)
        assert exp.project_id == "searchmind-demo-store"
        assert exp.end_date >= exp.start_date

    for out_dict in data["outcomes"]:
        out = ExperimentOutcome.model_validate(out_dict)
        assert out.project_id == "searchmind-demo-store"
        assert out.outcome_class in ["positive", "negative", "neutral", "inconclusive"]
        assert out.absolute_change is not None


def test_outcome_distribution_balance():
    """Verify the outcome classes represent realistic balanced experimentation."""
    data = load_demo_dataset()
    classes = [out["outcome_class"] for out in data["outcomes"]]
    assert classes.count("positive") >= 5
    assert classes.count("negative") >= 4
    assert classes.count("neutral") >= 4
    assert classes.count("inconclusive") >= 3


def test_temporal_coherence():
    """Verify start_date <= end_date <= measured_at across all experiments and outcomes."""
    data = load_demo_dataset()
    exp_by_id = {e["experiment_id"]: e for e in data["experiments"]}
    for outcome in data["outcomes"]:
        exp = exp_by_id[outcome["experiment_id"]]
        start = datetime.fromisoformat(exp["start_date"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(exp["end_date"].replace("Z", "+00:00"))
        measured = datetime.fromisoformat(outcome["measured_at"].replace("Z", "+00:00"))
        assert start <= end, f"Experiment {exp['experiment_id']} has start > end"
        assert end <= measured, f"Experiment {exp['experiment_id']} has end > measured_at"


def test_relational_cross_references():
    """Verify foreign keys and relational integrity across the entire dataset."""
    data = load_demo_dataset()
    page_urls = {p["url"] for p in data["pages"]}
    kw_set = {k["keyword"] for k in data["keywords"]}
    obs_ids = {o["observation_id"] for o in data["observations"]}
    dec_ids = {d["decision_id"] for d in data["decisions"]}
    exp_ids = {e["experiment_id"] for e in data["experiments"]}

    for obs in data["observations"]:
        assert obs["url"] in page_urls, f"Observation {obs['observation_id']} references missing URL"

    for r in data["rankings"]:
        assert r["target_url"] in page_urls, f"Ranking {r.get('keyword', 'unknown')} references missing URL"
        assert r["keyword"] in kw_set, f"Ranking {r.get('keyword', 'unknown')} references missing keyword"

    for dec in data["decisions"]:
        for obs_id in dec.get("observation_ids", []):
            assert obs_id in obs_ids, f"Decision {dec['decision_id']} references missing observation {obs_id}"

    for exp in data["experiments"]:
        assert exp["url"] in page_urls, f"Experiment {exp['experiment_id']} references missing URL"

    for out in data["outcomes"]:
        assert out["experiment_id"] in exp_ids, f"Outcome {out['outcome_id']} references missing experiment"


def test_validation_fails_on_broken_reference():
    """Verify validate_demo_dataset detects and reports broken relational links."""
    data = load_demo_dataset()
    # Inject an invalid reference in an outcome
    data["outcomes"][0]["experiment_id"] = "nonexistent_exp_999"
    report = validate_demo_dataset(data)
    assert report["valid"] is False
    assert any("references non-existent experiment" in err for err in report["errors"])


def test_build_hindsight_memory_documents():
    """Verify memory document builder formats high-signal narrative documents."""
    docs = build_hindsight_memory_documents()
    assert len(docs) == 20
    for doc in docs:
        assert doc["document_id"].startswith("seo_exp_")
        assert "SEO Experiment Record:" in doc["content"]
        assert "Context & Baseline:" in doc["content"]
        assert "Tested Optimization:" in doc["content"]
        assert "Observed Results:" in doc["content"]
        assert "Contextual Lesson & Interpretation:" in doc["content"]
        assert doc["context"].startswith("SearchMind historical SEO experiment")
        assert "experiment_id" in doc["metadata"]
        assert "outcome_class" in doc["metadata"]
        assert "seo_experiment" in doc["tags"]
        assert isinstance(doc["timestamp"], datetime)
