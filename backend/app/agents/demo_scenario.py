"""Deterministic demo scenario for SearchMind SEO Agent with memory integration.

Executes an evidence-first demonstration using exact records from the synthetic SEO dataset
and injected memory fixtures without consuming LLM API tokens.

Usage:
    python -m app.agents.demo_scenario          # Zero-token fixture mode
    python -m app.agents.demo_scenario --live   # Controlled live Hindsight Recall
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import SEOAnalysisRequest, SEOWorkflowResult
from app.agents.workflow import SEOWorkflowEngine
from app.memory import HindsightRecallAdapter, InMemoryRecallAdapter
from app.models.enums import SearchIntent
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact
from app.seo.demo_dataset import load_demo_dataset


def build_default_fixture_adapter() -> InMemoryRecallAdapter:
    """Build an in-memory recall adapter populated with representative experiment memories."""
    adapter = InMemoryRecallAdapter()
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
    adapter.add_fixture_memory(
        text=(
            "SEO Experiment Record: exp_014. Page: https://demo-searchmind-store.example/products/rugged-terrain-trekking-boots. "
            "Hypothesis: Testing promotional discount keyword in title tag on commercial product pages. "
            "Observed Results: Primary metric 'ctr' changed from 2.69 to 2.15 (-20.1%). Outcome: NEGATIVE. "
            "Lesson: Inserting discount and sale keywords into the title tag for a high-end trekking boot degraded perceived brand value."
        ),
        bank_id="searchmind-demo",
        query="What happened when title tags were optimized on commercial product pages?",
        experiment_id="exp_014",
        outcome="negative",
    )
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
    return adapter


def run_demo_scenario(
    dataset_dir: Optional[Path] = None,
    live_memory: bool = False,
) -> SEOWorkflowResult:
    """
    Run deterministic demo analysis on 'waterproof-alpine-hiking-boots'.

    Uses real dataset records:
    - Page: waterproof-alpine-hiking-boots
    - Observation: obs_001 (low_ctr: CTR dropped from 3.2% to 1.8% despite top-3 SERP rank 3.1)
    - Memory: Live Hindsight if live_memory=True, otherwise deterministic fixture adapter.
    """
    raw_data = load_demo_dataset(dataset_dir)
    obs_list = [o for o in raw_data["observations.json"] if o["observation_id"] == "obs_001"]
    page_list = [p for p in raw_data["pages.json"] if "waterproof-alpine-hiking-boots" in p["url"]]

    obs = SEOObservation(**obs_list[0])
    page = WebsiteFact(**page_list[0]) if page_list else None

    # Construct structured SEO analysis request
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

    # Initialize memory adapter
    if live_memory:
        recall_adapter = HindsightRecallAdapter()
    else:
        recall_adapter = build_default_fixture_adapter()

    # Initialize deterministic engine
    analyzer = HistoricalAnalyzer(dataset_data=raw_data)
    rec_engine = RecommendationEngine()
    workflow_engine = SEOWorkflowEngine(
        historical_analyzer=analyzer,
        recommendation_engine=rec_engine,
        recall_adapter=recall_adapter,
        default_bank_id="searchmind-demo",
    )

    # Execute workflow up to approval gateway
    return workflow_engine.run_analysis_workflow(request)


def format_demo_output(result: SEOWorkflowResult) -> str:
    """Format SEOWorkflowResult according to SearchMind demonstration report format."""
    rec = result.recommendation
    ev = result.current_evidence
    hist = result.historical_context

    output = []
    output.append("-" * 50)
    output.append("SEARCHMIND")
    output.append("-" * 50)

    output.append("CURRENT SEO PROBLEM:")
    output.append("Organic CTR declined despite a top-3 ranking.\n")

    output.append("CURRENT EVIDENCE:")
    output.append(f"- URL: {ev.target_url}")
    output.append(f"- SERP Position: {ev.current_ranking} (previous: {ev.previous_ranking}, delta: {ev.ranking_delta:+.2f})")
    output.append(f"- Organic CTR: {ev.ctr:.2f}% (previous: {ev.previous_ctr:.2f}%, delta: {ev.ctr_delta:+.2f} pp)")
    output.append(f"- Search Impressions: {ev.impressions:,} | Clicks: {ev.clicks:,}")
    if ev.observations:
        for obs in ev.observations:
            output.append(f"- Observation: {obs}")
    output.append("")

    output.append("MEMORY QUERY:")
    output.append(f"{hist.memory_query or 'What happened in past experiments involving title tag optimization on commercial product pages?'}\n")

    mem_source_label = (
        "HINDSIGHT" if hist.memory_source.lower() == "hindsight" else "TEST FIXTURE"
    )
    output.append(f"HINDSIGHT MEMORY (MEMORY SOURCE: {mem_source_label}):")
    if hist.hindsight_memories:
        for m in hist.hindsight_memories[:3]:
            t = m.get("memory_text", "")
            eid = m.get("experiment_id")
            out = m.get("outcome")
            eid_str = f" [Linked: {eid}]" if eid else ""
            out_str = f" [Outcome: {out.upper()}]" if out else ""
            output.append(f"* {t[:110]}...{eid_str}{out_str}")
    else:
        output.append("* No memories recalled.")
    output.append("")

    output.append("STRUCTURED HISTORICAL EVIDENCE:")
    for exp in hist.positive_examples[:2]:
        eid = exp.get("experiment_id")
        desc = exp.get("hypothesis", "")[:75]
        out_sum = exp.get("outcome_summary", "")
        output.append(f"- Experiment {eid}: outcome: POSITIVE ({out_sum})")
        output.append(f"  Hypothesis: {desc}...")

    for exp in hist.negative_examples[:2]:
        eid = exp.get("experiment_id")
        desc = exp.get("hypothesis", "")[:75]
        out_sum = exp.get("outcome_summary", "")
        output.append(f"- Experiment {eid}: outcome: NEGATIVE ({out_sum})")
        output.append(f"  Hypothesis: {desc}...")

    for exp in hist.neutral_examples[:1]:
        eid = exp.get("experiment_id")
        output.append(f"- Experiment {eid}: outcome: NEUTRAL")

    if hist.contextual_caveats:
        output.append(f"- Contextual Caveat: {hist.contextual_caveats[0]}")
    output.append("")

    output.append("CONTEXTUAL REFLECTION:")
    output.append(f"{hist.reflection}\n")

    output.append("RECOMMENDATION:")
    output.append(f"{rec.recommendation}\n")

    output.append(f"CONFIDENCE:\n{rec.confidence:.2f}\n")
    output.append(f"REQUIRES APPROVAL:\n{'YES' if rec.requires_approval else 'NO'}\n")
    status_str = (
        result.approval_status.value
        if hasattr(result.approval_status, "value")
        else str(result.approval_status)
    )
    output.append(f"STATUS:\n{status_str.upper()}")
    output.append("-" * 50)

    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SearchMind SEO Agent Demo Scenario")
    parser.add_argument("--live", action="store_true", help="Execute live Hindsight recall against searchmind-demo")
    args = parser.parse_args()

    res = run_demo_scenario(live_memory=args.live)
    print(format_demo_output(res))
