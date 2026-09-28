"""Deterministic SEO workflow engine enforcing human-in-the-loop approval.

Coordinates:
Current State -> Historical Memory -> Recommendation -> Human Approval Gateway -> Experiment Proposal

Enforces that workflow execution strictly halts at the approval gateway before any
experiment can be created or executed.
"""

from datetime import timedelta
import logging
from typing import Optional
import uuid

from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import (
    CurrentSEOEvidence,
    HistoricalSEOContext,
    SEOAnalysisRequest,
    SEOWorkflowResult,
)
from app.models.base import utc_now
from app.models.enums import ApprovalStatus, ExperimentStatus, ObservationSeverity
from app.models.experiment import SEOExperiment
from app.models.recommendation import SEORecommendation

from app.memory import (
    BaseRecallAdapter,
    InMemoryRecallAdapter,
    build_memory_query,
)

logger = logging.getLogger("searchmind.agents.workflow")


class SEOWorkflowEngine:
    """
    Lightweight, deterministic workflow orchestrator for SearchMind SEO Agent.

    Enforces:
    1. Distillation of current SEO data into structured evidence
    2. Deterministic memory query generation and Hindsight Recall retrieval
    3. Context-aware synthesis of historical memory and domain precedents
    4. Generation of qualified, non-dogmatic recommendations
    5. Mandatory halt at Human-in-the-loop Approval Gateway (requires_approval = True)
    6. Controlled generation of experiment proposals ONLY upon explicit human approval
    """

    def __init__(
        self,
        historical_analyzer: Optional[HistoricalAnalyzer] = None,
        recommendation_engine: Optional[RecommendationEngine] = None,
        recall_adapter: Optional[BaseRecallAdapter] = None,
        default_bank_id: str = "searchmind-demo",
    ):
        self.analyzer = historical_analyzer or HistoricalAnalyzer()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.recall_adapter = recall_adapter
        self.default_bank_id = default_bank_id

    def extract_current_evidence(self, request: SEOAnalysisRequest) -> CurrentSEOEvidence:
        """Distill raw SEO request facts, observations, and metrics into structured evidence."""
        url = request.url
        keyword = request.target_keyword
        intent = (
            request.search_intent.value
            if hasattr(request.search_intent, "value")
            else str(request.search_intent)
        ) if request.search_intent else None
        page_type = request.page_type

        # If page_type or keyword is in request.current_page, extract them
        if request.current_page:
            if not page_type:
                page_type = request.current_page.page_type
            if not keyword:
                keyword = request.current_page.primary_keyword
            if not intent and request.current_page.search_intent:
                intent = (
                    request.current_page.search_intent.value
                    if hasattr(request.current_page.search_intent, "value")
                    else str(request.current_page.search_intent)
                )

        # Distill metrics
        metrics = request.current_metrics or {}
        curr_rank = metrics.get("position") or metrics.get("current_ranking")
        prev_rank = metrics.get("previous_position") or metrics.get("previous_ranking")
        rank_delta = (
            round(curr_rank - prev_rank, 2)
            if curr_rank is not None and prev_rank is not None
            else metrics.get("ranking_delta")
        )

        curr_ctr = metrics.get("ctr") or metrics.get("current_ctr")
        prev_ctr = metrics.get("previous_ctr")
        ctr_delta = (
            round(curr_ctr - prev_ctr, 2)
            if curr_ctr is not None and prev_ctr is not None
            else metrics.get("ctr_delta")
        )

        impressions = metrics.get("impressions")
        clicks = metrics.get("clicks")

        # Distill observations
        obs_texts = []
        obs_ids = []
        highest_sev = None

        severity_ranks = {
            "info": 1,
            "low": 2,
            "medium": 3,
            "high": 4,
            "critical": 5,
        }

        for obs in request.current_observations:
            obs_ids.append(obs.observation_id)
            delta_str = f" (delta: {obs.delta:+.2f})" if obs.delta is not None else ""
            sev_str = obs.severity.value if hasattr(obs.severity, "value") else str(obs.severity)
            obs_texts.append(
                f"[{sev_str.upper()}] {obs.observation_type} ({obs.metric_name}: "
                f"{obs.current_value}{obs.unit or ''}{delta_str})"
            )
            curr_rank_val = severity_ranks.get(sev_str.lower(), 0)
            high_rank_val = severity_ranks.get(
                (highest_sev.value if hasattr(highest_sev, "value") else str(highest_sev)).lower()
                if highest_sev else "",
                0,
            )
            if highest_sev is None or curr_rank_val > high_rank_val:
                highest_sev = obs.severity

        # If metrics were empty, check if observations have metrics
        if curr_ctr is None:
            for obs in request.current_observations:
                if obs.metric_name.lower() == "ctr":
                    curr_ctr = obs.current_value
                    prev_ctr = obs.previous_value
                    ctr_delta = obs.delta

        if curr_rank is None:
            for obs in request.current_observations:
                if obs.metric_name.lower() in ("position", "rank", "average_position"):
                    curr_rank = obs.current_value
                    prev_rank = obs.previous_value
                    rank_delta = obs.delta

        return CurrentSEOEvidence(
            target_url=url,
            keyword=keyword,
            search_intent=intent,
            page_type=page_type,
            current_ranking=curr_rank,
            previous_ranking=prev_rank,
            ranking_delta=rank_delta,
            ctr=curr_ctr,
            previous_ctr=prev_ctr,
            ctr_delta=ctr_delta,
            impressions=impressions,
            clicks=clicks,
            observations=obs_texts,
            observation_ids=obs_ids,
            highest_severity=highest_sev,
        )

    def run_analysis_workflow(
        self,
        request: SEOAnalysisRequest,
        memory_bank: Optional[str] = None,
    ) -> SEOWorkflowResult:
        """
        Execute the analysis workflow up to the Human Approval Gateway.

        Stages:
        1. Extract current SEO evidence
        2. Formulate deterministic memory query and retrieve historical memories via recall adapter
        3. Retrieve and synthesize historical context from memory and domain dataset
        4. Generate context-aware recommendation
        5. HALT at Human Approval Gateway (status = PENDING_APPROVAL, proposal = None)
        """
        # Step 1: Current SEO state
        current_evidence = self.extract_current_evidence(request)

        # Step 2: Formulate deterministic memory query
        obs_type = (
            request.current_observations[0].observation_type
            if request.current_observations
            else None
        )
        tech_focus = request.technique_focus or "title_tag_optimization"
        memory_query = build_memory_query(
            page_type=current_evidence.page_type,
            search_intent=current_evidence.search_intent,
            target_keyword=current_evidence.keyword,
            observation_type=obs_type,
            technique=tech_focus,
        )

        # Step 3: Recall memories if adapter configured
        recalled_items = None
        memory_source = "local_dataset"
        if self.recall_adapter is not None:
            target_bank = memory_bank or self.default_bank_id
            memory_source = (
                "fixture"
                if isinstance(self.recall_adapter, InMemoryRecallAdapter)
                else "hindsight"
            )
            try:
                recalled_items = self.recall_adapter.recall(
                    query=memory_query,
                    bank_id=target_bank,
                )
            except Exception as exc:
                logger.warning(f"Recall retrieval encountered error: {exc}; proceeding with local dataset.")
                recalled_items = []

        # Step 4: Historical context synthesis
        historical_context = self.analyzer.build_historical_context(
            current_evidence=current_evidence,
            technique_focus=tech_focus,
            recalled_memories=recalled_items,
            memory_source=memory_source,
            memory_query=memory_query,
        )

        # Step 5: Recommendation generation
        recommendation = self.recommendation_engine.generate_recommendation(
            project_id=request.project_id,
            current_evidence=current_evidence,
            historical_context=historical_context,
        )

        # Step 6: Strict halt at approval gateway
        return SEOWorkflowResult(
            request=request,
            current_evidence=current_evidence,
            historical_context=historical_context,
            recommendation=recommendation,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
            workflow_stopped_at_approval=True,
            experiment_proposal=None,
        )

    def process_human_approval(
        self,
        workflow_result: SEOWorkflowResult,
        approved: bool,
        operator_note: Optional[str] = None,
    ) -> SEOWorkflowResult:
        """
        Process human operator approval or rejection.

        If APPROVED: generates a formal SEOExperiment proposal (status=PLANNED).
        If REJECTED: marks status as REJECTED without generating an experiment.
        """
        if not approved:
            return SEOWorkflowResult(
                request=workflow_result.request,
                current_evidence=workflow_result.current_evidence,
                historical_context=workflow_result.historical_context,
                recommendation=workflow_result.recommendation,
                approval_status=ApprovalStatus.REJECTED,
                workflow_stopped_at_approval=True,
                experiment_proposal=None,
            )

        # Build formal experiment proposal upon operator approval
        rec = workflow_result.recommendation
        now = utc_now()
        exp_id = f"exp_prop_{uuid.uuid4().hex[:8]}"

        ctrl_desc = "Current title and meta snippet in production."
        if workflow_result.request.current_page:
            ctrl_desc = f"Title: '{workflow_result.request.current_page.title}'"

        treat_desc = f"Modified implementation per recommendation: {rec.recommendation}"

        proposal = SEOExperiment(
            experiment_id=exp_id,
            project_id=rec.project_id,
            url=rec.url,
            experiment_type=rec.recommendation_type,
            hypothesis=f"Proposed optimization ({rec.recommendation[:90]}...) will produce expected impact: {rec.expected_impact or 'CTR improvement'}.",
            control_description=ctrl_desc,
            treatment_description=treat_desc,
            primary_metric="ctr",
            secondary_metrics=["position", "clicks", "impressions"],
            baseline_metrics={
                "ctr": workflow_result.current_evidence.ctr or 0.0,
                "position": workflow_result.current_evidence.current_ranking or 0.0,
            },
            start_date=now,
            end_date=now + timedelta(days=28),
            status=ExperimentStatus.PLANNED,
            created_at=now,
        )

        return SEOWorkflowResult(
            request=workflow_result.request,
            current_evidence=workflow_result.current_evidence,
            historical_context=workflow_result.historical_context,
            recommendation=workflow_result.recommendation,
            approval_status=ApprovalStatus.APPROVED,
            workflow_stopped_at_approval=False,
            experiment_proposal=proposal,
        )
