"""Deterministic unit tests for SearchMind SEO Agent Core and Workflow Engine.

Validates:
1. Current SEO evidence extraction
2. Historical experiment matching
3. Positive historical evidence
4. Negative historical evidence
5. Mixed evidence
6. Inconclusive evidence
7. Contextual mismatch
8. No historical evidence
9. Confidence calculation
10. Recommendation generation
11. requires_approval enforcement
12. Workflow stops before experiment execution
13. Human approval transitions (approved vs rejected)

These tests run purely in local memory with ZERO external LLM calls or token consumption.
"""

from pathlib import Path
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
    infer_page_type_from_url,
)
from app.models.enums import ApprovalStatus, ExperimentStatus, ObservationSeverity, SearchIntent
from app.models.recommendation import SEORecommendation
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact
from app.seo.demo_dataset import load_demo_dataset


@pytest.fixture(scope="module")
def demo_data():
    """Load local synthetic dataset fixture without network calls."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
    return load_demo_dataset(data_dir)


@pytest.fixture
def analyzer(demo_data):
    """HistoricalAnalyzer initialized with local dataset."""
    return HistoricalAnalyzer(dataset_data=demo_data)


@pytest.fixture
def recommendation_engine():
    """RecommendationEngine instance."""
    return RecommendationEngine()


@pytest.fixture
def workflow_engine(analyzer, recommendation_engine):
    """SEOWorkflowEngine instance."""
    return SEOWorkflowEngine(
        historical_analyzer=analyzer,
        recommendation_engine=recommendation_engine,
    )


@pytest.fixture
def agent(workflow_engine):
    """SEOAgent instance."""
    return SEOAgent(workflow_engine=workflow_engine)


# -----------------------------------------------------------------------------
# Test 1: Current SEO Evidence Extraction
# -----------------------------------------------------------------------------
def test_current_seo_evidence_extraction(workflow_engine):
    """Verify raw request signals are accurately distilled into CurrentSEOEvidence."""
    obs = SEOObservation(
        observation_id="test_obs_001",
        project_id="test-store",
        url="https://demo-searchmind-store.example/products/trail-blazer-pro",
        metric_name="ctr",
        observation_type="low_ctr",
        current_value=1.5,
        previous_value=2.8,
        unit="%",
        severity=ObservationSeverity.HIGH,
    )
    req = SEOAnalysisRequest(
        project_id="test-store",
        url="https://demo-searchmind-store.example/products/trail-blazer-pro",
        current_observations=[obs],
        current_metrics={
            "position": 4.2,
            "previous_position": 3.8,
            "impressions": 8500,
            "clicks": 128,
        },
        target_keyword="trail shoes",
        search_intent=SearchIntent.TRANSACTIONAL,
        page_type="product",
    )

    evidence = workflow_engine.extract_current_evidence(req)

    assert str(evidence.target_url) == "https://demo-searchmind-store.example/products/trail-blazer-pro"
    assert evidence.keyword == "trail shoes"
    assert evidence.search_intent == "transactional"
    assert evidence.page_type == "product"
    assert evidence.current_ranking == 4.2
    assert evidence.previous_ranking == 3.8
    assert evidence.ranking_delta == 0.40
    assert evidence.ctr == 1.5
    assert evidence.previous_ctr == 2.8
    assert evidence.ctr_delta == -1.30
    assert evidence.impressions == 8500
    assert evidence.clicks == 128
    assert evidence.highest_severity == ObservationSeverity.HIGH
    assert len(evidence.observation_ids) == 1

    summary_text = evidence.to_evidence_text()
    assert "SERP Position: currently 4.2" in summary_text
    assert "Organic CTR: 1.50%" in summary_text


# -----------------------------------------------------------------------------
# Test 2: Historical Experiment Matching
# -----------------------------------------------------------------------------
def test_historical_experiment_matching(analyzer):
    """Verify matching of experiments by page_type and technique."""
    matches, mismatch, reason = analyzer.find_relevant_experiments(
        page_type="product",
        technique="title_tag_test",
    )

    assert len(matches) > 0
    assert mismatch is False
    assert reason is None
    for exp in matches:
        assert exp["inferred_page_type"] == "product"
        assert "outcome" in exp
        assert "outcome_class" in exp


# -----------------------------------------------------------------------------
# Test 3: Positive Historical Evidence Handling
# -----------------------------------------------------------------------------
def test_positive_historical_evidence_handling(analyzer, recommendation_engine):
    """Verify that consistent positive precedent results in positive reflection and uplift confidence."""
    # Synthesize context with only positive precedent
    pos_exp = {
        "experiment_id": "test_exp_pos",
        "hypothesis": "Keyword-first title tags improve CTR",
        "primary_metric": "ctr",
        "inferred_page_type": "product",
        "outcome": {"outcome_class": "positive", "primary_metric_before": 2.0, "primary_metric_after": 3.2, "percentage_change": 60.0},
        "outcome_class": "positive",
        "outcome_summary": "ctr: 2.0 -> 3.2 (+60.0%)",
        "interpretation": "Moving keyword forward yielded strong CTR improvement.",
    }
    context = HistoricalSEOContext(
        query="test query",
        recalled_memories=[pos_exp],
        relevant_experiment_ids=["test_exp_pos"],
        positive_examples=[pos_exp],
        negative_examples=[],
        neutral_examples=[],
        inconclusive_examples=[],
        contextual_caveats=[],
        reflection="Historical precedents showed consistent positive outcomes.",
        source_count=1,
    )
    ev = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/shoe",
        keyword="trail shoe",
        ctr=1.8,
        previous_ctr=2.5,
        ctr_delta=-0.7,
        highest_severity=ObservationSeverity.MEDIUM,
    )

    confidence = recommendation_engine.compute_confidence(ev, context)
    assert confidence >= 0.65, f"Expected elevated confidence for positive evidence, got {confidence}"

    rec = recommendation_engine.generate_recommendation("test-store", ev, context)
    assert rec.recommendation_type == "evidence_backed_title_optimization"
    assert "keyword-first" in rec.recommendation.lower()
    assert rec.requires_approval is True


# -----------------------------------------------------------------------------
# Test 4: Negative Historical Evidence Handling
# -----------------------------------------------------------------------------
def test_negative_historical_evidence_handling(analyzer, recommendation_engine):
    """Verify Rule C: predominantly negative precedent advises caution / alternative."""
    neg_exp = {
        "experiment_id": "test_exp_neg",
        "hypothesis": "Discount tag in title will boost CTR",
        "primary_metric": "ctr",
        "inferred_page_type": "product",
        "outcome": {"outcome_class": "negative", "primary_metric_before": 3.0, "primary_metric_after": 2.2, "percentage_change": -26.7},
        "outcome_class": "negative",
        "outcome_summary": "ctr: 3.0 -> 2.2 (-26.7%)",
        "interpretation": "Discount language degraded brand trust and reduced click-through.",
    }
    context = HistoricalSEOContext(
        query="test query",
        recalled_memories=[neg_exp],
        relevant_experiment_ids=["test_exp_neg"],
        positive_examples=[],
        negative_examples=[neg_exp],
        neutral_examples=[],
        inconclusive_examples=[],
        contextual_caveats=["Discount language degraded brand trust."],
        reflection="Historical precedents in similar contexts were predominantly negative.",
        source_count=1,
    )
    ev = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/boot",
        keyword="hiking boots",
        ctr=2.0,
        highest_severity=ObservationSeverity.HIGH,
    )

    rec = recommendation_engine.generate_recommendation("test-store", ev, context)
    assert rec.recommendation_type == "conservative_content_alternative"
    assert "do not execute" in rec.recommendation.lower() or "alternative" in rec.recommendation.lower()
    assert rec.confidence == 0.67  # 0.62 + 0.05 high severity


# -----------------------------------------------------------------------------
# Test 5: Mixed Evidence Handling
# -----------------------------------------------------------------------------
def test_mixed_evidence_handling(analyzer, recommendation_engine):
    """Verify Rule B: mixed precedents produce cautious, balanced recommendation."""
    pos_exp = {"experiment_id": "exp_pos", "outcome_class": "positive", "hypothesis": "keyword alignment"}
    neg_exp = {"experiment_id": "exp_neg", "outcome_class": "negative", "hypothesis": "promotional discount"}
    context = HistoricalSEOContext(
        query="test query",
        recalled_memories=[pos_exp, neg_exp],
        relevant_experiment_ids=["exp_pos", "exp_neg"],
        positive_examples=[pos_exp],
        negative_examples=[neg_exp],
        source_count=2,
    )
    ev = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/jacket",
        keyword="waterproof jacket",
        ctr=1.9,
    )

    confidence = recommendation_engine.compute_confidence(ev, context)
    assert 0.50 <= confidence <= 0.55

    rec = recommendation_engine.generate_recommendation("test-store", ev, context)
    assert rec.recommendation_type == "balanced_title_tag_test"
    assert "avoiding aggressive promotional discount" in rec.recommendation.lower()


# -----------------------------------------------------------------------------
# Test 6: Inconclusive Evidence Handling
# -----------------------------------------------------------------------------
def test_inconclusive_evidence_handling(analyzer, recommendation_engine):
    """Verify Rule D: inconclusive precedent advises controlled measurement trial."""
    inc_exp = {"experiment_id": "exp_inc", "outcome_class": "inconclusive", "hypothesis": "seasonality overlap"}
    context = HistoricalSEOContext(
        query="test query",
        recalled_memories=[inc_exp],
        relevant_experiment_ids=["exp_inc"],
        positive_examples=[],
        negative_examples=[],
        neutral_examples=[],
        inconclusive_examples=[inc_exp],
        source_count=1,
    )
    ev = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/socks",
        keyword="trail socks",
    )

    rec = recommendation_engine.generate_recommendation("test-store", ev, context)
    assert rec.recommendation_type == "controlled_measurement_trial"
    assert rec.confidence <= 0.45


# -----------------------------------------------------------------------------
# Test 7: Contextual Mismatch Handling
# -----------------------------------------------------------------------------
def test_contextual_mismatch_handling(analyzer, recommendation_engine):
    """Verify Rule E: contextual divergence between page types incurs penalty and caveat."""
    exp = {"experiment_id": "exp_cat", "outcome_class": "positive", "hypothesis": "category test"}
    context = HistoricalSEOContext(
        query="test query",
        recalled_memories=[exp],
        relevant_experiment_ids=["exp_cat"],
        positive_examples=[exp],
        source_count=1,
        has_contextual_mismatch=True,
        mismatch_reason="Precedents were on category pages, current target is a product page.",
    )
    ev = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/pole",
        page_type="product",
    )

    confidence = recommendation_engine.compute_confidence(ev, context)
    rec = recommendation_engine.generate_recommendation("test-store", ev, context)

    assert rec.recommendation_type == "adapted_contextual_title_test"
    assert "adapt" in rec.recommendation.lower()
    assert "category pages" in rec.recommendation.lower()
    # Confidence should have contextual penalty
    assert confidence < 0.60


# -----------------------------------------------------------------------------
# Test 8: No Historical Evidence Handling
# -----------------------------------------------------------------------------
def test_no_historical_evidence_handling(analyzer, recommendation_engine):
    """Verify Rule F: absence of precedent produces explicit absence statement and low confidence."""
    context = HistoricalSEOContext(
        query="technique: 'unknown_schema' on 'product'",
        source_count=0,
    )
    ev = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/stove",
        keyword="camping stove",
    )

    confidence = recommendation_engine.compute_confidence(ev, context)
    assert confidence == 0.35

    rec = recommendation_engine.generate_recommendation("test-store", ev, context)
    assert rec.recommendation_type == "exploratory_title_test"
    assert "no historical experiments exist" in rec.recommendation.lower()


# -----------------------------------------------------------------------------
# Test 9: Confidence Calculation Bounds
# -----------------------------------------------------------------------------
def test_confidence_calculation_bounds(recommendation_engine):
    """Verify confidence is strictly bounded between 0.10 and 0.85 (never 1.0)."""
    ev = CurrentSEOEvidence(target_url="https://demo-searchmind-store.example/page")
    ctx = HistoricalSEOContext(query="test", source_count=0)

    # Empty context
    conf = recommendation_engine.compute_confidence(ev, ctx)
    assert 0.10 <= conf <= 0.85

    # Multi-positive context
    ctx_pos = HistoricalSEOContext(
        query="test",
        source_count=10,
        positive_examples=[{"id": i} for i in range(10)],
    )
    conf_pos = recommendation_engine.compute_confidence(ev, ctx_pos)
    assert 0.10 <= conf_pos <= 0.85
    assert conf_pos < 1.0


# -----------------------------------------------------------------------------
# Test 10: Recommendation Generation Model Compliance
# -----------------------------------------------------------------------------
def test_recommendation_generation_model_compliance(workflow_engine):
    """Verify generated recommendations strictly pass Pydantic SEORecommendation validation."""
    req = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        target_keyword="waterproof hiking boots",
        search_intent=SearchIntent.COMMERCIAL,
        page_type="product",
        technique_focus="title_tag_test",
    )

    result = workflow_engine.run_analysis_workflow(req)
    rec = result.recommendation

    assert isinstance(rec, SEORecommendation)
    assert rec.project_id == "searchmind-demo-store"
    assert str(rec.url) == "https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots"
    assert rec.current_evidence != ""
    assert rec.historical_evidence != ""
    assert rec.reflection is not None
    assert 0.0 <= rec.confidence <= 1.0


# -----------------------------------------------------------------------------
# Test 11: Requires Approval Enforcement
# -----------------------------------------------------------------------------
def test_requires_approval_enforcement(workflow_engine):
    """Verify recommendations strictly enforce requires_approval = True."""
    req = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/trail-blazer-running-shoes",
        page_type="product",
    )

    result = workflow_engine.run_analysis_workflow(req)

    assert result.recommendation.requires_approval is True
    assert result.approval_status == ApprovalStatus.PENDING_APPROVAL


# -----------------------------------------------------------------------------
# Test 12: Workflow Stops Before Experiment Execution
# -----------------------------------------------------------------------------
def test_workflow_stops_before_experiment_execution(workflow_engine):
    """Verify workflow strictly stops before experiment proposal generation until operator approves."""
    req = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/apex-carbon-road-shoes",
        page_type="product",
    )

    # Initial execution
    res = workflow_engine.run_analysis_workflow(req)
    assert res.workflow_stopped_at_approval is True
    assert res.experiment_proposal is None
    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL


# -----------------------------------------------------------------------------
# Test 13: Human Approval Flow (Approved vs Rejected)
# -----------------------------------------------------------------------------
def test_human_approval_flow(agent):
    """Verify operator approval creates planned experiment while rejection creates none."""
    req = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/goretex-weather-jacket",
        page_type="product",
    )

    initial_result = agent.analyze(req)
    assert initial_result.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert initial_result.experiment_proposal is None

    # Case A: Operator rejects
    rejected_result = agent.reject(initial_result, operator_note="Budget constrained")
    assert rejected_result.approval_status == ApprovalStatus.REJECTED
    assert rejected_result.workflow_stopped_at_approval is True
    assert rejected_result.experiment_proposal is None

    # Case B: Operator approves
    approved_result = agent.approve(initial_result, operator_note="Approved for Q3 trial")
    assert approved_result.approval_status == ApprovalStatus.APPROVED
    assert approved_result.workflow_stopped_at_approval is False
    assert approved_result.experiment_proposal is not None
    assert approved_result.experiment_proposal.status == ExperimentStatus.PLANNED
    assert approved_result.experiment_proposal.primary_metric == "ctr"


# -----------------------------------------------------------------------------
# Test 14: URL Page Type Inference Utility
# -----------------------------------------------------------------------------
def test_infer_page_type_from_url():
    """Verify URL path classification."""
    assert infer_page_type_from_url("https://example.com/products/hiking-boot") == "product"
    assert infer_page_type_from_url("https://example.com/collections/shoes") == "category"
    assert infer_page_type_from_url("https://example.com/blog/how-to-run") == "guide"
    assert infer_page_type_from_url("https://example.com/") == "homepage"
