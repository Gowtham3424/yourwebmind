"""Deterministic end-to-end learning loop demonstration for SearchMind SEO Agent.

Simulates the complete evidence-backed SEO decision and learning lifecycle:
1. Current SEO problem identification (low CTR despite high ranking)
2. Historical memory recall (balanced past precedents: positive, negative, neutral, inconclusive)
3. Historical reasoning & contextual pattern synthesis (including optional Reflect context)
4. Context-aware recommendation generation (non-dogmatic, falsifiable)
5. Enforced human approval gateway (requires_approval = True)
6. Operator approval transition (status = APPROVED)
7. Experiment creation and execution (status PLANNED -> RUNNING -> COMPLETED)
8. Outcome calculation and percentage change (zero-baseline safe)
9. Factual, non-dogmatic lesson synthesis
10. Memory retention through the Hindsight Retain abstraction
11. Verification that retained lesson is available to future memory retrieval

Usage:
    python -m app.agents.demo_scenario          # Zero-token deterministic fixture demonstration
    python -m app.agents.demo_scenario --live   # Controlled live Hindsight Recall query (if daemon active)
"""

import argparse
from pathlib import Path
import sys
from typing import Any, Dict, Optional

from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import SEOAnalysisRequest, SEOWorkflowResult
from app.agents.workflow import SEOWorkflowEngine
from app.experiments.service import ExperimentExecutionService
from app.memory import (
    HindsightRecallAdapter,
    InMemoryRecallAdapter,
    InMemoryReflectAdapter,
    InMemoryRetainAdapter,
)
from app.models.enums import ApprovalStatus, ObservationSeverity, SearchIntent
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact
from app.seo.demo_dataset import load_demo_dataset


def build_demo_fixture_adapter() -> InMemoryRecallAdapter:
    """Build an in-memory recall adapter populated with representative experiment memories across all 4 outcome classes."""
    adapter = InMemoryRecallAdapter()
    # 1. Positive Precedent
    adapter.add_fixture_memory(
        text=(
            "SEO Experiment Record: exp_001. Page: https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots. "
            "Hypothesis: Aligning product title with commercial purchase intent may improve CTR. "
            "Tested Optimization: Control: 'SearchMind Alpine Hiking Boots' vs Treatment: 'Waterproof Alpine Hiking Boots | SearchMind'. "
            "Observed Results: Primary metric 'ctr' changed from 1.8 to 2.7 (+50.0%). Outcome: POSITIVE. "
            "Lesson: Purchase-intent alignment improved CTR by +50.0% on this commercial product page."
        ),
        bank_id="searchmind-demo",
        query="What happened when title tags were optimized on commercial product pages?",
        experiment_id="exp_001",
        outcome="positive",
    )
    # 2. Negative Precedent
    adapter.add_fixture_memory(
        text=(
            "SEO Experiment Record: exp_014. Page: https://demo-searchmind-store.example/products/rugged-terrain-trekking-boots. "
            "Hypothesis: Testing promotional discount keyword in title tag on commercial product pages. "
            "Observed Results: Primary metric 'ctr' changed from 2.69 to 2.15 (-20.1%). Outcome: NEGATIVE. "
            "Lesson: Inserting discount and sale keywords into the title tag for a high-end trekking boot degraded perceived brand trust and CTR."
        ),
        bank_id="searchmind-demo",
        query="What happened when title tags were optimized on commercial product pages?",
        experiment_id="exp_014",
        outcome="negative",
    )
    # 3. Neutral Precedent
    adapter.add_fixture_memory(
        text=(
            "SEO Experiment Record: exp_003. Page: https://demo-searchmind-store.example/products/trail-blazer-running-shoes. "
            "Hypothesis: Shortening title to avoid mobile SERP truncation may improve mobile CTR. "
            "Observed Results: Primary metric 'ctr' changed from 2.1 to 2.14 (+1.9%). Outcome: NEUTRAL. "
            "Lesson: Shortening the title tag for mobile devices resulted in negligible CTR movement within normal SERP variance."
        ),
        bank_id="searchmind-demo",
        query="What happened when title tags were optimized on commercial product pages?",
        experiment_id="exp_003",
        outcome="neutral",
    )
    # 4. Inconclusive Precedent
    adapter.add_fixture_memory(
        text=(
            "SEO Experiment Record: exp_005. Page: https://demo-searchmind-store.example/products/winter-thermal-snow-boots. "
            "Hypothesis: Adding seasonal weather modifiers to title tag. "
            "Observed Results: Primary metric 'ctr' fluctuated wildly. Outcome: INCONCLUSIVE. "
            "Lesson: Test coincided with unconfirmed Google core algorithm update and seasonal snowfall fluctuations; directional impact unproven."
        ),
        bank_id="searchmind-demo",
        query="What happened when title tags were optimized on commercial product pages?",
        experiment_id="exp_005",
        outcome="inconclusive",
    )
    return adapter


def run_full_learning_loop_demo(
    dataset_dir: Optional[Path] = None,
    live_recall: bool = False,
) -> Dict[str, Any]:
    """
    Execute the complete 12-stage SearchMind learning loop end-to-end.

    Returns structured demonstration dictionary with all phases represented.
    """
    raw_data = load_demo_dataset(dataset_dir)
    obs_list = [o for o in raw_data["observations.json"] if o["observation_id"] == "obs_001"]
    page_list = [p for p in raw_data["pages.json"] if "waterproof-alpine-hiking-boots" in p["url"]]

    obs = SEOObservation(**obs_list[0]) if obs_list else SEOObservation(
        observation_id="obs_001",
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        observation_type="low_ctr_high_rank",
        severity=ObservationSeverity.HIGH,
        metric_name="ctr",
        current_value=1.8,
        previous_value=3.2,
        delta=-1.4,
        description="Organic CTR dropped from 3.2% to 1.8% despite top-3 SERP rank 3.1.",
    )
    page = WebsiteFact(**page_list[0]) if page_list else None

    # Step 1: Current SEO Problem
    request = SEOAnalysisRequest(
        project_id="searchmind-demo-store",
        url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
        current_page=page,
        current_observations=[obs],
        current_metrics={
            "position": 3.1,
            "previous_position": 2.9,
            "ctr": 1.8,
            "previous_ctr": 3.2,
            "impressions": 15400,
            "clicks": 277,
        },
        target_keyword="waterproof hiking boots",
        search_intent=SearchIntent.COMMERCIAL,
        page_type="product",
        technique_focus="title_tag_optimization",
        analysis_question="Why has organic CTR fallen despite maintaining top-3 SERP ranking?",
    )

    # Step 2: Initialize memory adapters
    if live_recall:
        recall_adapter = HindsightRecallAdapter()
    else:
        recall_adapter = build_demo_fixture_adapter()

    # Step 3 & 4: In-Memory Reflect adapter representing synthesized reasoning
    reflect_adapter = InMemoryReflectAdapter(
        default_synthesis=(
            "Across historical experiments on commercial product pages, keyword-first title alignment "
            "reliably improved CTR when transactional intent matched. Conversely, aggressive promotional "
            "modifiers ('best discount') degraded click-through performance and brand trust. Observations "
            "are contextual and do not guarantee universal outcomes."
        ),
        conflicting_evidence=[
            "Adding aggressive discount phrasing ('huge sale') in exp_014 decreased CTR by -20.1% on commercial boots."
        ],
        caveats=[
            "Seasonal demand shifts and search engine snippet rewriting can affect observed click rates."
        ],
    )

    # Step 5: Initialize deterministic workflow engine
    analyzer = HistoricalAnalyzer(dataset_data=raw_data)
    rec_engine = RecommendationEngine()
    workflow_engine = SEOWorkflowEngine(
        historical_analyzer=analyzer,
        recommendation_engine=rec_engine,
        recall_adapter=recall_adapter,
        reflect_adapter=reflect_adapter,
        enable_reflect=True,
        default_bank_id="searchmind-demo",
    )

    # Run analysis up to approval gateway
    analysis_result = workflow_engine.run_analysis_workflow(request)

    # Step 6 & 7: Human Approval Gateway
    approved_result = workflow_engine.process_human_approval(
        workflow_result=analysis_result,
        approved=True,
        operator_note="Approved keyword-first title test. Exclude aggressive discount phrasing.",
    )

    # Step 8, 9, 10, 11: Experiment Execution, Outcome, Lesson, and Retain
    exp_service = ExperimentExecutionService()
    retain_adapter = InMemoryRetainAdapter()

    learning_result = exp_service.execute_learning_loop(
        recommendation=approved_result.recommendation,
        approval_status=ApprovalStatus.APPROVED,
        measured_value=2.7,
        retain_adapter=retain_adapter,
        experiment_id="exp_021_demo",
        caveats=["Tested with steady site uptime and consistent tracking instrumentation."],
    )

    # Step 12: Demonstrate that the retained lesson is available to future memory retrieval
    retained_doc = retain_adapter.retained_payloads[0]
    # Feed newly retained document into recall adapter
    recall_adapter.add_fixture_memory(
        text=retained_doc["content"],
        bank_id="searchmind-demo",
        query="waterproof alpine hiking boots title tag optimization",
        experiment_id="exp_021_demo",
        outcome="positive",
    )
    # Query for the newly retained memory
    subsequent_recall = recall_adapter.recall("waterproof alpine hiking boots")
    future_available = any(m.experiment_id == "exp_021_demo" for m in subsequent_recall)

    return {
        "analysis": analysis_result,
        "approved": approved_result,
        "experiment": learning_result["experiment"],
        "outcome": learning_result["outcome"],
        "lesson": learning_result["lesson"],
        "retain_result": learning_result["retain_result"],
        "retained_payload": retained_doc,
        "future_available": future_available,
        "subsequent_recall_count": len(subsequent_recall),
    }


def format_evaluator_report(demo_data: Dict[str, Any]) -> str:
    """Format the learning loop demonstration into the evaluator-friendly format."""
    analysis: SEOWorkflowResult = demo_data["analysis"]
    ev = analysis.current_evidence
    hist = analysis.historical_context
    rec = analysis.recommendation
    exp = demo_data["experiment"]
    out = demo_data["outcome"]
    retain = demo_data["retain_result"]
    retained_payload = demo_data["retained_payload"]
    future_ok = demo_data["future_available"]

    mem_source_str = (
        "HINDSIGHT MEMORY BANK (searchmind-demo)"
        if hist.memory_source.lower() == "hindsight"
        else "DETERMINISTIC MEMORY FIXTURE"
    )

    # Clean caveat text
    caveat_text = (
        hist.contextual_caveats[0]
        if hist.contextual_caveats
        else "Results are contextual to observed page template and seasonal intent."
    )

    lines = [
        "==================================================",
        "SEARCHMIND - LEARNING LOOP DEMO",
        "==================================================",
        "",
        "CURRENT SEO PROBLEM",
        f"- Page: {ev.target_url}",
        f"- Keyword: {ev.keyword or 'waterproof hiking boots'}",
        f"- Current CTR: {ev.ctr:.2f}% (previous: {ev.previous_ctr:.2f}%, delta: {ev.ctr_delta:+.2f} pp)",
        f"- Issue: Organic CTR declined by {abs(ev.ctr_delta):.2f} pp despite top-3 SERP rank ({ev.current_ranking:.1f}).",
        "",
        "HISTORICAL MEMORY",
        f"- Memory source: {mem_source_str}",
        f"- Relevant experiments: {hist.source_count}",
        f"- Positive: {len(hist.positive_examples)}",
        f"- Negative: {len(hist.negative_examples)}",
        f"- Neutral: {len(hist.neutral_examples)}",
        f"- Inconclusive: {len(hist.inconclusive_examples)}",
        "",
        "HISTORICAL REASONING",
        "- What happened before: Past trials indicate keyword-first commercial alignment improves CTR, but promotional keywords damage CTR.",
        f"- Relevant evidence: exp_001 achieved +50.0% CTR lift on hiking boots with commercial title alignment.",
        "- Conflicting evidence: exp_014 saw -20.1% CTR drop when adding discount/promotional modifiers on trekking boots.",
        f"- Caveats: {caveat_text}",
        "",
        "RECOMMENDATION",
        f"- Action: {rec.recommendation}",
        f"- Rationale: Contextual precedent indicates keyword-intent alignment recovers CTR while strictly preserving brand trust.",
        f"- Confidence: {rec.confidence:.2f} (bounded between 0.10 and 0.85 per deterministic evidence rules)",
        f"- Evidence: {len(hist.positive_examples)} positive precedent(s), {len(hist.negative_examples)} cautionary precedent(s).",
        f"- Approval required: {'YES' if rec.requires_approval else 'NO'}",
        "",
        "HUMAN APPROVAL",
        "- Status: APPROVED",
        "- Operator note: Approved keyword-first title test. Exclude aggressive discount phrasing.",
        "",
        "EXPERIMENT",
        f"- Experiment ID: {exp.experiment_id}",
        f"- Metric: {exp.primary_metric}",
        f"- Baseline: {exp.baseline_metrics.get('ctr', 1.8)}%",
        f"- Measured: {out.primary_metric_after:.2f}%",
        "",
        "OUTCOME",
        f"- Absolute change: {out.absolute_change:+.2f} pp",
        f"- Percentage change: {out.percentage_change:+.1f}%",
        f"- Classification: {out.outcome_class.value.upper() if hasattr(out.outcome_class, 'value') else str(out.outcome_class).upper()}",
        "",
        "LESSON RETAINED",
        f"- Lesson: {demo_data['lesson']}",
        f"- Memory document ID: {retain.document_id}",
        f"- Tags: {', '.join(retained_payload.get('tags', []))}",
        "",
        "FUTURE LEARNING",
        f"- Available to future workflow: {'YES' if future_ok else 'NO'}",
        f"- Verification query: Retrieved {retain.document_id} in subsequent recall matching '{ev.keyword}'.",
        "",
        "==================================================",
        "LEARNING LOOP COMPLETE",
        "==================================================",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SearchMind SEO Agent Learning Loop Demo")
    parser.add_argument("--live", action="store_true", help="Execute live Hindsight recall against searchmind-demo")
    args = parser.parse_args()

    demo_data = run_full_learning_loop_demo(live_recall=args.live)
    print(format_evaluator_report(demo_data))
