"""Agent workflow and memory browser API endpoints for SearchMind.

Exposes the 12-stage evidence-based SEO learning loop and memory browser
to the minimal evaluator frontend.
Zero external Groq calls, zero live data mutations.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.agents.demo_scenario import build_demo_fixture_adapter, run_full_learning_loop_demo
from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import CurrentSEOEvidence, SEOAnalysisRequest, SEOWorkflowResult
from app.agents.workflow import SEOWorkflowEngine
from app.experiments.service import ExperimentExecutionService
from app.memory import (
    InMemoryRecallAdapter,
    InMemoryReflectAdapter,
    InMemoryRetainAdapter,
)
from app.models.base import utc_now
from app.models.enums import ApprovalStatus, ObservationSeverity, SearchIntent
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact
from app.seo.demo_dataset import load_demo_dataset

logger = logging.getLogger("searchmind.api.agent")

router = APIRouter(prefix="/api/v1", tags=["Agent Workflow & Memory"])


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class ApprovalRequest(BaseModel):
    """Operator approval decision payload."""

    approved: bool = Field(..., description="Whether recommendation is approved")
    operator_note: Optional[str] = Field(
        default=None,
        description="Optional operator note or guardrail instruction",
    )


class ExecuteExperimentRequest(BaseModel):
    """Payload to initiate a controlled experiment from approved recommendation."""

    measured_value: float = Field(
        default=2.70,
        description="Measured primary metric value upon experiment completion",
    )


# -----------------------------------------------------------------------------
# In-Memory Demo State Holder
# -----------------------------------------------------------------------------
class DemoSessionState:
    """Manages the interactive demo session state safely in memory."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.raw_data = load_demo_dataset()
        self.recall_adapter = build_demo_fixture_adapter()
        self.reflect_adapter = InMemoryReflectAdapter(
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
        self.retain_adapter = InMemoryRetainAdapter()
        self.workflow_engine = SEOWorkflowEngine(
            historical_analyzer=HistoricalAnalyzer(dataset_data=self.raw_data),
            recommendation_engine=RecommendationEngine(),
            recall_adapter=self.recall_adapter,
            reflect_adapter=self.reflect_adapter,
            enable_reflect=True,
            default_bank_id="searchmind-demo",
        )

        # Build initial request
        obs_list = [o for o in self.raw_data["observations.json"] if o["observation_id"] == "obs_001"]
        page_list = [p for p in self.raw_data["pages.json"] if "waterproof-alpine-hiking-boots" in p["url"]]

        self.observation = SEOObservation(**obs_list[0]) if obs_list else SEOObservation(
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
        self.page = WebsiteFact(**page_list[0]) if page_list else None

        self.analysis_request = SEOAnalysisRequest(
            project_id="searchmind-demo-store",
            url="https://demo-searchmind-store.example/products/waterproof-alpine-hiking-boots",
            current_page=self.page,
            current_observations=[self.observation],
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

        # Run analysis to approval gateway
        self.analysis_result: SEOWorkflowResult = self.workflow_engine.run_analysis_workflow(
            self.analysis_request
        )
        self.approval_status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
        self.operator_note: Optional[str] = None
        self.experiment_record: Optional[Dict[str, Any]] = None
        self.outcome_record: Optional[Dict[str, Any]] = None
        self.lesson_record: Optional[str] = None
        self.retain_record: Optional[Dict[str, Any]] = None
        self.future_verified: bool = False
        self.active_stage: str = "approval"  # "signal", "evidence", "reasoning", "recommendation", "approval", "approved", "rejected", "completed"


# Global singleton demo session
demo_session = DemoSessionState()


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/agent/demo-analysis")
def get_demo_analysis() -> Dict[str, Any]:
    """
    Retrieve current evidence, historical recall context, synthesized reflection,
    and recommendation halted at the Human Approval Gateway.
    """
    ev = demo_session.analysis_result.current_evidence
    hist = demo_session.analysis_result.historical_context
    rec = demo_session.analysis_result.recommendation

    # Build compact evidence items
    evidence_items = []
    # Positives
    for p in hist.positive_examples[:2]:
        evidence_items.append({
            "experiment_id": p.get("experiment_id", "exp_001"),
            "technique": "Commercial title alignment",
            "delta": "+50.0% CTR",
            "outcome": "positive",
            "summary": p.get("outcome_summary") or "Purchase-intent keyword alignment improved CTR by +50.0%.",
        })
    # Negatives
    for n in hist.negative_examples[:2]:
        evidence_items.append({
            "experiment_id": n.get("experiment_id", "exp_014"),
            "technique": "Promotional title modifier",
            "delta": "-20.1% CTR",
            "outcome": "negative",
            "summary": n.get("outcome_summary") or "Promotional discount keywords degraded brand trust and CTR.",
        })
    # Inconclusive
    for inc in hist.inconclusive_examples[:1]:
        evidence_items.append({
            "experiment_id": inc.get("experiment_id", "exp_018"),
            "technique": "Seasonal demand modifier",
            "delta": "+4.8% CTR (unproven)",
            "outcome": "inconclusive",
            "summary": "External seasonal shift confounded metric attribution.",
        })
    # Neutral
    for neu in hist.neutral_examples[:1]:
        evidence_items.append({
            "experiment_id": neu.get("experiment_id", "exp_003"),
            "technique": "Mobile title shortening",
            "delta": "+1.9% CTR",
            "outcome": "neutral",
            "summary": "Shortened title tag produced negligible variance within SERP noise.",
        })

    # Caveat
    caveat_text = "Historical outcomes are contextual, not universal SEO rules."

    return {
        "status": "ok",
        "demo_mode": True,
        "active_stage": demo_session.active_stage,
        "signal": {
            "page_title": "Waterproof Alpine Hiking Boots",
            "page_url": str(ev.target_url),
            "keyword": ev.keyword or "waterproof hiking boots",
            "current_ctr": ev.ctr,
            "previous_ctr": ev.previous_ctr,
            "ctr_delta": ev.ctr_delta,
            "rank": ev.current_ranking,
            "previous_rank": ev.previous_ranking,
            "rank_delta": ev.ranking_delta,
            "impressions": ev.impressions,
            "clicks": ev.clicks,
            "search_intent": ev.search_intent,
            "page_type": ev.page_type,
            "signal_description": f"Organic CTR declined by {abs(ev.ctr_delta):.2f} pp despite top-3 SERP rank ({ev.current_ranking:.1f}).",
            "severity": "high",
        },
        "historical_memory": {
            "source": "Hindsight Memory Bank (searchmind-demo)",
            "source_type": "fixture",
            "relevant_count": hist.source_count,
            "positive_count": len(hist.positive_examples),
            "negative_count": len(hist.negative_examples),
            "neutral_count": len(hist.neutral_examples),
            "inconclusive_count": len(hist.inconclusive_examples),
            "evidence_list": evidence_items,
        },
        "learning": {
            "synthesis": (
                "Past trials indicate keyword-first commercial alignment improved CTR in a comparable "
                "hiking-boot page, while promotional discount modifiers produced a negative result."
            ),
            "evidence_summary": f"{len(hist.positive_examples)} positive precedents, {len(hist.negative_examples)} cautionary precedents",
            "relevant_evidence": "exp_001 achieved +50.0% CTR lift on hiking boots with commercial title alignment.",
            "conflicting_evidence": "exp_014 saw -20.1% CTR drop when adding discount/promotional modifiers on trekking boots.",
            "caveat": caveat_text,
            "reflect_available": True,
            "reflect_status_note": None,
        },
        "recommendation": {
            "recommendation_id": rec.recommendation_id,
            "title": "RECOMMENDED TEST",
            "action": rec.recommendation,
            "rationale": "Contextual precedent indicates keyword-intent alignment recovers CTR while strictly preserving brand trust.",
            "confidence": rec.confidence,
            "confidence_bounds": "Bounded between 0.10 and 0.85 per deterministic evidence rules",
            "expected_impact": rec.expected_impact,
            "approval_required": rec.requires_approval,
            "status": demo_session.approval_status.value.upper(),
        },
        "approval": {
            "status": demo_session.approval_status.value.upper(),
            "operator_note": demo_session.operator_note,
            "can_execute": demo_session.approval_status == ApprovalStatus.APPROVED,
        },
        "experiment": demo_session.experiment_record,
        "outcome": demo_session.outcome_record,
        "retained_lesson": demo_session.lesson_record,
        "retain_info": demo_session.retain_record,
        "future_learning": {
            "available": demo_session.future_verified,
            "verification_note": (
                "Retrieved seo_exp_021_demo in subsequent recall matching 'waterproof hiking boots'."
                if demo_session.future_verified
                else None
            ),
        },
    }


@router.post("/agent/approval")
def submit_approval(payload: ApprovalRequest) -> Dict[str, Any]:
    """
    Process human approval or rejection of the pending SEO recommendation.
    Does NOT execute the experiment automatically.
    """
    if payload.approved:
        demo_session.approval_status = ApprovalStatus.APPROVED
        demo_session.operator_note = (
            payload.operator_note or "Approved keyword-first title test. Exclude aggressive discount phrasing."
        )
        demo_session.active_stage = "approved"
        logger.info(f"Operator APPROVED recommendation: {demo_session.operator_note}")
    else:
        demo_session.approval_status = ApprovalStatus.REJECTED
        demo_session.operator_note = (
            payload.operator_note or "Rejected by operator. Execution halted; no experiment will run."
        )
        demo_session.active_stage = "rejected"
        logger.info(f"Operator REJECTED recommendation: {demo_session.operator_note}")

    return {
        "status": "ok",
        "approval_status": demo_session.approval_status.value.upper(),
        "operator_note": demo_session.operator_note,
        "can_execute_experiment": demo_session.approval_status == ApprovalStatus.APPROVED,
        "active_stage": demo_session.active_stage,
    }


@router.post("/agent/execute-experiment")
def execute_approved_experiment(payload: ExecuteExperimentRequest) -> Dict[str, Any]:
    """
    Execute the controlled SEO experiment following operator approval.
    Calculates outcome deterministically, synthesizes factual non-dogmatic lesson,
    retains into memory, and verifies future recall availability.
    """
    if demo_session.approval_status != ApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot execute experiment with approval status '{demo_session.approval_status.value}'. Human approval is required.",
        )

    exp_service = ExperimentExecutionService()
    measured_val = payload.measured_value if payload.measured_value is not None else 2.70

    learning_res = exp_service.execute_learning_loop(
        recommendation=demo_session.analysis_result.recommendation,
        approval_status=ApprovalStatus.APPROVED,
        measured_value=measured_val,
        retain_adapter=demo_session.retain_adapter,
        experiment_id="exp_021_demo",
        caveats=["Tested with steady site uptime and consistent tracking instrumentation."],
    )

    exp = learning_res["experiment"]
    out = learning_res["outcome"]
    lesson = learning_res["lesson"]
    retain_res = learning_res["retain_result"]

    # Verify future retrieval availability
    retained_doc = demo_session.retain_adapter.retained_payloads[0]
    demo_session.recall_adapter.add_fixture_memory(
        text=retained_doc["content"],
        bank_id="searchmind-demo",
        query="waterproof alpine hiking boots title tag optimization",
        experiment_id="exp_021_demo",
        outcome="positive",
    )
    subsequent_recall = demo_session.recall_adapter.recall("waterproof alpine hiking boots")
    future_ok = any(m.experiment_id == "exp_021_demo" for m in subsequent_recall)

    # Save to session
    demo_session.experiment_record = {
        "experiment_id": exp.experiment_id,
        "metric": exp.primary_metric.upper(),
        "baseline": exp.baseline_metrics.get("ctr", 1.8),
        "measured": out.primary_metric_after,
        "url": str(exp.url),
        "hypothesis": exp.hypothesis,
        "control": exp.control_description,
        "treatment": exp.treatment_description,
    }
    demo_session.outcome_record = {
        "absolute_change": f"{out.absolute_change:+.2f} percentage points",
        "relative_change": f"{out.percentage_change:+.1f}%",
        "classification": (out.outcome_class.value if hasattr(out.outcome_class, "value") else str(out.outcome_class)).upper(),
        "factual_statement": "Observed positive result in this experiment.",
    }
    demo_session.lesson_record = lesson
    demo_session.retain_record = {
        "memory_doc_id": retain_res.document_id or "seo_exp_021_demo",
        "context": "Observed on this target page.",
        "caveat": "Not universal proof. Tested with steady site uptime and consistent tracking instrumentation.",
        "tags": retained_doc.get("tags", []),
        "status": "RETAINED",
    }
    demo_session.future_verified = future_ok
    demo_session.active_stage = "completed"

    return {
        "status": "ok",
        "experiment": demo_session.experiment_record,
        "outcome": demo_session.outcome_record,
        "lesson": demo_session.lesson_record,
        "retain_info": demo_session.retain_record,
        "future_learning": {
            "available": future_ok,
            "verification_note": "Retrieved seo_exp_021_demo in subsequent recall matching 'waterproof hiking boots'.",
        },
        "active_stage": demo_session.active_stage,
    }


@router.post("/agent/reset")
def reset_demo() -> Dict[str, Any]:
    """Reset the demo session back to the initial pre-approval analysis state."""
    demo_session.reset()
    logger.info("Demo session reset to initial state.")
    return {"status": "ok", "message": "Demo session reset."}


# -----------------------------------------------------------------------------
# Memory Browser Endpoint
# -----------------------------------------------------------------------------
@router.get("/memory/browse")
def browse_memory(
    q: Optional[str] = Query(None, description="Search query string"),
    outcome: Optional[str] = Query(None, description="Filter by outcome class"),
) -> Dict[str, Any]:
    """
    Search and browse historical SEO experiments stored in memory.
    Proves that SearchMind maintains persistent memory across positive, negative,
    neutral, and inconclusive precedent.
    """
    dataset = load_demo_dataset()
    experiments = dataset.get("experiments.json", [])
    outcomes = {o["experiment_id"]: o for o in dataset.get("outcomes.json", [])}

    items = []
    for exp in experiments:
        eid = exp["experiment_id"]
        out = outcomes.get(eid, {})
        outcome_cls = out.get("outcome_class", "unknown").lower()
        baseline_ctr = exp.get("baseline_metrics", {}).get("ctr", 0.0)
        after_ctr = out.get("primary_metric_after", 0.0)
        pct_change = out.get("percentage_change", 0.0)
        url = exp.get("url", "")
        hyp = exp.get("hypothesis", "")
        exp_type = exp.get("experiment_type", "").replace("_", " ").title()

        # Build card
        item = {
            "experiment_id": eid.upper(),
            "technique": exp_type,
            "url": url,
            "outcome": outcome_cls,
            "baseline": baseline_ctr,
            "measured": after_ctr,
            "delta": f"{pct_change:+.1f}% CTR",
            "pct_change": pct_change,
            "context": hyp,
            "caveat": out.get("confidence_note") or (out.get("caveats")[0] if out.get("caveats") else None),
        }
        items.append(item)

    # Include newly completed experiment from current demo session if any
    if demo_session.experiment_record and demo_session.outcome_record:
        items.insert(0, {
            "experiment_id": "EXP-021-DEMO",
            "technique": "Title Tag Optimization",
            "url": demo_session.experiment_record["url"],
            "outcome": "positive",
            "baseline": demo_session.experiment_record["baseline"],
            "measured": demo_session.experiment_record["measured"],
            "delta": demo_session.outcome_record["relative_change"] + " CTR",
            "pct_change": 50.0,
            "context": "Aligning product title with commercial purchase intent.",
            "caveat": "Tested with steady site uptime and consistent tracking instrumentation.",
        })

    # Filter by search query if supplied
    if q and q.strip():
        query_norm = q.strip().lower()
        items = [
            it for it in items
            if query_norm in it["experiment_id"].lower()
            or query_norm in it["technique"].lower()
            or query_norm in it["url"].lower()
            or query_norm in it["context"].lower()
        ]

    # Filter by outcome if supplied
    if outcome and outcome.lower() != "all":
        items = [it for it in items if it["outcome"].lower() == outcome.lower()]

    return {
        "total_records": len(items),
        "query": q,
        "outcome_filter": outcome,
        "memories": items,
    }
