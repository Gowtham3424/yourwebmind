"""Deterministic demo scenario for SearchMind SEO Agent.

Executes a live demonstration using exact records from the synthetic SEO dataset
(data/demo/) without requiring any external LLM calls or token consumption.

Can be run directly via:
    python -m app.agents.demo_scenario
"""

import json
from pathlib import Path
from typing import Any, Dict

from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import SEOAnalysisRequest, SEOWorkflowResult
from app.agents.workflow import SEOWorkflowEngine
from app.models.enums import ApprovalStatus, ObservationSeverity, SearchIntent
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact
from app.seo.demo_dataset import load_demo_dataset


def run_demo_scenario(dataset_dir: Path | None = None) -> SEOWorkflowResult:
    """
    Run deterministic demo analysis on 'https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots'.

    Uses real dataset records:
    - Page: waterproof-alpine-hiking-boots
    - Observation: obs_001 (low_ctr: CTR dropped from 3.2% to 1.8% despite top-3 SERP rank 3.1)
    - Historical Precedents:
        * exp_001: positive (+50.0% CTR when aligning title with purchase intent)
        * exp_014: negative (-20.07% CTR when inserting promotional discount keywords)
        * exp_003: neutral (+1.9% CTR within natural variance)
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
        technique_focus="title_tag_test",
        analysis_question="Why has organic CTR fallen despite maintaining top-3 SERP ranking?",
    )

    # Initialize deterministic engine
    analyzer = HistoricalAnalyzer(dataset_data=raw_data)
    rec_engine = RecommendationEngine()
    workflow_engine = SEOWorkflowEngine(
        historical_analyzer=analyzer,
        recommendation_engine=rec_engine,
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
    output.append("SEARCHMIND ANALYSIS")
    output.append("-" * 50)
    output.append(f"URL:\n{ev.target_url}\n")
    output.append("Current Issue:\nOrganic CTR declined despite top-3 SERP rank.\n")

    output.append("CURRENT EVIDENCE:")
    output.append(f"- Ranking: {ev.current_ranking} (previous: {ev.previous_ranking}, delta: {ev.ranking_delta:+.2f})")
    output.append(f"- Organic CTR: {ev.ctr:.2f}% (previous: {ev.previous_ctr:.2f}%, delta: {ev.ctr_delta:+.2f} pp)")
    output.append(f"- Search Impressions: {ev.impressions:,} | Clicks: {ev.clicks:,}")
    if ev.observations:
        for obs in ev.observations:
            output.append(f"- Observation: {obs}")
    output.append("")

    output.append("HISTORICAL EVIDENCE:")
    for exp in hist.positive_examples:
        eid = exp.get("experiment_id")
        desc = exp.get("hypothesis", "")[:75]
        out_sum = exp.get("outcome_summary", "")
        output.append(f"- Experiment {eid}: outcome: POSITIVE ({out_sum})")
        output.append(f"  Hypothesis: {desc}...")

    for exp in hist.negative_examples:
        eid = exp.get("experiment_id")
        desc = exp.get("hypothesis", "")[:75]
        out_sum = exp.get("outcome_summary", "")
        output.append(f"- Experiment {eid}: outcome: NEGATIVE ({out_sum})")
        output.append(f"  Hypothesis: {desc}...")

    for exp in hist.neutral_examples:
        eid = exp.get("experiment_id")
        desc = exp.get("hypothesis", "")[:75]
        output.append(f"- Experiment {eid}: outcome: NEUTRAL")

    if hist.contextual_caveats:
        output.append(f"- Contextual Caveat: {hist.contextual_caveats[0]}")
    output.append("")

    output.append("REFLECTION:")
    output.append(f"{hist.reflection}\n")

    output.append("RECOMMENDATION:")
    output.append(f"{rec.recommendation}\n")

    output.append(f"CONFIDENCE:\n{rec.confidence:.2f}\n")
    output.append(f"REQUIRES APPROVAL:\n{'YES' if rec.requires_approval else 'NO'}\n")
    status_str = result.approval_status.value if hasattr(result.approval_status, "value") else str(result.approval_status)
    output.append(f"STATUS:\n{status_str.upper()}")
    output.append("-" * 50)

    return "\n".join(output)


if __name__ == "__main__":
    res = run_demo_scenario()
    print(format_demo_output(res))
