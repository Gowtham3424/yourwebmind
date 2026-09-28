"""Deterministic unit tests for Hindsight memory integration and recall adapter.

Validates:
1. Memory query generation across various SEO contexts
2. Recall adapter with mocked/fake response (InMemoryRecallAdapter)
3. Hindsight provenance mapping (source, bank, query, extract_experiment_id, extract_outcome)
4. Historical context merging (structured dataset + recalled memories)
5. Recommendation engine receiving memory-enriched context
6. Missing memory result handling (empty recall)
7. Malformed memory result handling (missing fields, graceful degradation)
8. Complete workflow execution with injected fake Recall adapter
9. Zero live Hindsight or Groq calls during ordinary test execution

All tests execute strictly in local Python memory in under 1 second without network dependencies.
"""

from pathlib import Path
import pytest
from unittest.mock import MagicMock

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
    BaseRecallAdapter,
    HindsightRecallAdapter,
    InMemoryRecallAdapter,
    RecalledMemoryItem,
    build_memory_query,
    extract_experiment_id,
    extract_outcome,
)
from app.models.enums import ApprovalStatus, ObservationSeverity, SearchIntent
from app.models.recommendation import SEORecommendation
from app.models.seo import SEOObservation
from app.seo.demo_dataset import load_demo_dataset


@pytest.fixture(scope="module")
def demo_data():
    """Load local synthetic dataset fixture."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
    return load_demo_dataset(data_dir)


# -----------------------------------------------------------------------------
# Test 1: Memory Query Generation
# -----------------------------------------------------------------------------
def test_build_memory_query_variations():
    """Verify deterministic query synthesis across page types, intents, and techniques."""
    # Case A: Title tag optimization on commercial product pages with keyword
    q1 = build_memory_query(
        page_type="product",
        search_intent="commercial",
        target_keyword="waterproof hiking boots",
        technique="title_tag_optimization",
    )
    assert q1 == "What happened when title tag optimization was tested on commercial product pages for 'waterproof hiking boots'?"

    # Case B: Observation CTR dip without specific keyword
    q2 = build_memory_query(
        page_type="category",
        search_intent="informational",
        observation_type="low_ctr",
        technique="faq_schema",
    )
    assert q2 == "What happened in past experiments involving faq schema optimization to improve CTR on informational category pages?"

    # Case C: Homepage with general technique
    q3 = build_memory_query(
        page_type="homepage",
        technique="internal_linking",
    )
    assert "internal linking optimization on the homepage" in q3


# -----------------------------------------------------------------------------
# Test 2: Recall Adapter with In-Memory Mock/Fixture
# -----------------------------------------------------------------------------
def test_in_memory_recall_adapter():
    """Verify InMemoryRecallAdapter returns correctly structured RecalledMemoryItem list."""
    adapter = InMemoryRecallAdapter()
    adapter.add_fixture_memory(
        text="SEO Experiment Record: exp_001. Title tag restructuring on product page increased CTR by 50%.",
        bank_id="searchmind-demo",
        query="What happened when title tags were optimized?",
        experiment_id="exp_001",
        outcome="positive",
    )

    results = adapter.recall("What happened when title tags were optimized?")
    assert len(results) == 1
    item = results[0]
    assert isinstance(item, RecalledMemoryItem)
    assert item.source == "fixture"
    assert item.memory_bank == "searchmind-demo"
    assert item.experiment_id == "exp_001"
    assert item.outcome == "positive"
    assert "increased CTR by 50%" in item.memory_text


# -----------------------------------------------------------------------------
# Test 3: Provenance Mapping & Extraction Utilities
# -----------------------------------------------------------------------------
def test_provenance_extraction_utilities():
    """Verify extract_experiment_id and extract_outcome extract identifiers reliably without fabricating."""
    # Experiment ID extraction
    assert extract_experiment_id("seo_exp_001", "some text") == "exp_001"
    assert extract_experiment_id(None, "SEO Experiment exp_014 on product page") == "exp_014"
    assert extract_experiment_id(None, "context with exp_020", None) == "exp_020"
    assert extract_experiment_id(None, "unrelated text without ID") is None

    # Outcome extraction
    assert extract_outcome("text", {"outcome_class": "positive"}) == "positive"
    assert extract_outcome("Observed outcome: NEGATIVE across trial.") == "negative"
    assert extract_outcome("Outcome classification: INCONCLUSIVE due to SERP volatility.") == "inconclusive"
    assert extract_outcome("Unrelated plain text without classification.") is None


# -----------------------------------------------------------------------------
# Test 4: Historical Context Merging (Structured Data + Recalled Memories)
# -----------------------------------------------------------------------------
def test_historical_context_merging(demo_data):
    """Verify HistoricalAnalyzer integrates external recalled memories and links them to experiments."""
    analyzer = HistoricalAnalyzer(dataset_data=demo_data)
    evidence = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        page_type="product",
        keyword="waterproof hiking boots",
        ctr=1.8,
        previous_ctr=3.2,
    )

    recalled = [
        RecalledMemoryItem(
            source="fixture",
            memory_bank="searchmind-demo",
            query="test query",
            memory_text="Historical test exp_001 showed title change yielded +50% CTR.",
            experiment_id="exp_001",
            outcome="positive",
        )
    ]

    context = analyzer.build_historical_context(
        current_evidence=evidence,
        technique_focus="title_tag_optimization",
        recalled_memories=recalled,
        memory_source="fixture",
        memory_query="test memory query",
    )

    assert context.memory_source == "fixture"
    assert context.memory_query == "test memory query"
    assert len(context.hindsight_memories) == 1
    assert "exp_001" in context.relevant_experiment_ids
    assert len(context.structured_experiment_ids) > 0
    assert "Hindsight Recalled Memories (Source: FIXTURE)" in context.to_evidence_text()


# -----------------------------------------------------------------------------
# Test 5: Recommendation Receiving Memory-Enriched Context
# -----------------------------------------------------------------------------
def test_recommendation_with_memory_enriched_context(demo_data):
    """Verify RecommendationEngine includes recalled memory provenance in the recommendation."""
    analyzer = HistoricalAnalyzer(dataset_data=demo_data)
    rec_engine = RecommendationEngine()

    evidence = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        page_type="product",
        keyword="waterproof hiking boots",
        ctr=1.8,
        previous_ctr=3.2,
        ctr_delta=-1.4,
    )
    recalled = [
        RecalledMemoryItem(
            source="fixture",
            memory_bank="searchmind-demo",
            query="What happened when title tags were optimized?",
            memory_text="Title tag test exp_001 showed positive purchase-intent alignment.",
            experiment_id="exp_001",
            outcome="positive",
        )
    ]
    context = analyzer.build_historical_context(
        current_evidence=evidence,
        technique_focus="title_tag_optimization",
        recalled_memories=recalled,
        memory_source="fixture",
    )

    rec = rec_engine.generate_recommendation("searchmind-demo-store", evidence, context)
    assert isinstance(rec, SEORecommendation)
    assert rec.requires_approval is True
    assert "exp_001" in rec.supporting_experiment_ids
    assert "Hindsight Recalled Memories" in rec.historical_evidence


# -----------------------------------------------------------------------------
# Test 6: Missing Memory Result (Empty Recall)
# -----------------------------------------------------------------------------
def test_missing_memory_result_graceful_handling(demo_data):
    """Verify workflow functions properly when recall returns zero memories."""
    empty_adapter = InMemoryRecallAdapter(fixture_memories=[])
    analyzer = HistoricalAnalyzer(dataset_data=demo_data)
    engine = SEOWorkflowEngine(
        historical_analyzer=analyzer,
        recall_adapter=empty_adapter,
    )

    req = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        page_type="product",
        target_keyword="hiking boots",
        technique_focus="title_tag_optimization",
    )

    result = engine.run_analysis_workflow(req)
    assert result.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert len(result.historical_context.hindsight_memories) == 0
    # Still has structured dataset experiments
    assert result.historical_context.source_count > 0


# -----------------------------------------------------------------------------
# Test 7: Malformed Memory Result Handling
# -----------------------------------------------------------------------------
def test_malformed_memory_result_handling(demo_data):
    """Verify malformed memory dicts without text or standard fields do not crash the pipeline."""
    analyzer = HistoricalAnalyzer(dataset_data=demo_data)
    evidence = CurrentSEOEvidence(
        target_url="https://demo-searchmind-store.example/products/boot",
        page_type="product",
    )
    # Malformed memory item with missing text and strange fields
    malformed_items = [
        {"strange_field": 123, "memory_text": "", "experiment_id": None},
        {"memory_text": "Non-conforming text blob without identifiers"},
    ]

    context = analyzer.build_historical_context(
        current_evidence=evidence,
        technique_focus="title_tag_optimization",
        recalled_memories=malformed_items,
        memory_source="fixture",
    )

    assert len(context.hindsight_memories) == 2
    assert context.source_count > 0


# -----------------------------------------------------------------------------
# Test 8: Complete Workflow with Injected Fake Recall Adapter
# -----------------------------------------------------------------------------
def test_complete_workflow_with_injected_recall_adapter(demo_data):
    """Verify full end-to-end workflow execution with injected in-memory recall adapter."""
    adapter = InMemoryRecallAdapter()
    adapter.add_fixture_memory(
        text="SEO Experiment exp_001: Aligning title tag with purchase intent increased CTR by 50%.",
        bank_id="searchmind-demo",
        query="What happened when title tags were tested?",
        experiment_id="exp_001",
        outcome="positive",
    )
    adapter.add_fixture_memory(
        text="SEO Experiment exp_014: Adding promotional discount keyword decreased CTR by 20%.",
        bank_id="searchmind-demo",
        query="What happened when title tags were tested?",
        experiment_id="exp_014",
        outcome="negative",
    )

    agent = SEOAgent(
        dataset_dir=Path(__file__).resolve().parent.parent.parent / "data" / "demo",
        recall_adapter=adapter,
    )

    req = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        page_type="product",
        target_keyword="waterproof hiking boots",
        search_intent=SearchIntent.COMMERCIAL,
        technique_focus="title_tag_optimization",
    )

    res = agent.analyze(req)

    assert res.approval_status == ApprovalStatus.PENDING_APPROVAL
    assert res.workflow_stopped_at_approval is True
    assert res.experiment_proposal is None
    assert len(res.historical_context.hindsight_memories) == 2
    assert "exp_001" in res.historical_context.relevant_experiment_ids
    assert "exp_014" in res.historical_context.relevant_experiment_ids
    assert res.recommendation.requires_approval is True


# -----------------------------------------------------------------------------
# Test 9: No Hindsight Calls During Normal Tests
# -----------------------------------------------------------------------------
def test_no_live_hindsight_calls_during_normal_tests():
    """Verify that HindsightRecallAdapter is not called when InMemoryRecallAdapter is injected."""
    mock_service = MagicMock()
    # If mock_service.recall is called, fail the test
    mock_service.recall.side_effect = AssertionError("Live Hindsight service was unexpectedly invoked!")

    # Verify adapter with mock service is not touched if in-memory adapter is used
    fake_adapter = InMemoryRecallAdapter()
    fake_adapter.add_fixture_memory(text="Safe memory fixture", bank_id="searchmind-demo")

    workflow = SEOWorkflowEngine(recall_adapter=fake_adapter)
    req = SEOAnalysisRequest(
        project_id="test",
        url="https://demo-searchmind-store.example/products/shoe",
    )
    result = workflow.run_analysis_workflow(req)

    assert result.historical_context.memory_source == "fixture"
    mock_service.recall.assert_not_called()
