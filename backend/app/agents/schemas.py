"""Structured request, evidence, and context schemas for SearchMind SEO Agent."""

from typing import Any, Dict, List, Optional
from pydantic import Field, HttpUrl

from app.models.base import BaseDomainModel
from app.models.enums import ApprovalStatus, ObservationSeverity, SearchIntent
from app.models.experiment import SEOExperiment
from app.models.recommendation import SEORecommendation
from app.models.seo import SEOObservation
from app.models.website import WebsiteFact


class SEOAnalysisRequest(BaseDomainModel):
    """
    Input request submitted to the SearchMind SEO Agent for diagnostic analysis.

    Orchestrates current page facts, diagnostic observations, metrics,
    and analysis scope without arbitrary unvalidated prompts.
    """

    project_id: str = Field(..., description="Project identifier (e.g. searchmind-demo-store)")
    url: HttpUrl = Field(..., description="Target webpage URL being analyzed")
    current_page: Optional[WebsiteFact] = Field(default=None, description="Current page structural and factual state")
    current_observations: List[SEOObservation] = Field(
        default_factory=list,
        description="Empirical observations or diagnostic signals detected for this page",
    )
    current_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current performance metrics (e.g., {'ctr': 1.4, 'position': 3.8, 'impressions': 1200})",
    )
    target_keyword: Optional[str] = Field(default=None, description="Primary focus keyword")
    search_intent: Optional[SearchIntent] = Field(default=None, description="Search intent classification")
    page_type: Optional[str] = Field(default=None, description="Page template/type (product, category, guide)")
    technique_focus: Optional[str] = Field(
        default=None,
        description="Optional technique to explore (e.g. title_tag_optimization, faq_schema, content_expansion)",
    )
    analysis_question: Optional[str] = Field(
        default=None,
        description="Specific question or issue operator is investigating",
    )


class CurrentSEOEvidence(BaseDomainModel):
    """
    Structured, empirical summary of current SEO performance and diagnostic findings.

    Explicitly separates confirmed measurements from unavailable metrics.
    Never fabricates values.
    """

    target_url: HttpUrl = Field(..., description="Target page URL")
    keyword: Optional[str] = Field(default=None, description="Target search keyword if available")
    search_intent: Optional[str] = Field(default=None, description="Search intent if classified")
    page_type: Optional[str] = Field(default=None, description="Page category/type if known")
    current_ranking: Optional[float] = Field(default=None, description="Current average SERP rank position")
    previous_ranking: Optional[float] = Field(default=None, description="Previous baseline SERP rank position")
    ranking_delta: Optional[float] = Field(default=None, description="SERP position delta (current - previous)")
    ctr: Optional[float] = Field(default=None, description="Current organic click-through rate percentage")
    previous_ctr: Optional[float] = Field(default=None, description="Previous organic click-through rate percentage")
    ctr_delta: Optional[float] = Field(default=None, description="CTR delta percentage points")
    impressions: Optional[int] = Field(default=None, description="Current search impressions count")
    clicks: Optional[int] = Field(default=None, description="Current search clicks count")
    observations: List[str] = Field(default_factory=list, description="Descriptive observation notes")
    observation_ids: List[str] = Field(default_factory=list, description="Associated observation identifiers")
    highest_severity: Optional[ObservationSeverity] = Field(
        default=None,
        description="Highest severity among current observations",
    )

    def to_evidence_text(self) -> str:
        """Format current SEO evidence into clean, structured narrative text."""
        lines = []
        if self.current_ranking is not None:
            prev_str = f" from {self.previous_ranking}" if self.previous_ranking is not None else ""
            delta_str = f" (delta: {self.ranking_delta:+.2f})" if self.ranking_delta is not None else ""
            lines.append(f"- SERP Position: currently {self.current_ranking}{prev_str}{delta_str}")
        else:
            lines.append("- SERP Position: unavailable / not tracked")

        if self.ctr is not None:
            prev_ctr = f" from {self.previous_ctr:.2f}%" if self.previous_ctr is not None else ""
            delta_ctr = f" (delta: {self.ctr_delta:+.2f} pp)" if self.ctr_delta is not None else ""
            lines.append(f"- Organic CTR: {self.ctr:.2f}%{prev_ctr}{delta_ctr}")
        else:
            lines.append("- Organic CTR: unavailable / not tracked")

        if self.impressions is not None:
            lines.append(f"- Impressions: {self.impressions:,}")
        if self.clicks is not None:
            lines.append(f"- Clicks: {self.clicks:,}")

        if self.observations:
            lines.append("- Diagnostic Findings:")
            for obs in self.observations:
                lines.append(f"  * {obs}")
        return "\n".join(lines)


class HistoricalSEOContext(BaseDomainModel):
    """
    Internal structured representation of recalled historical memory.

    Clearly separates positive, negative, neutral, and inconclusive precedent,
    contextual caveats, and synthesized reflection.
    """

    query: str = Field(..., description="Query or criteria used to identify historical precedents")
    recalled_memories: List[Dict[str, Any]] = Field(default_factory=list, description="Raw memory units or experiment dicts")
    relevant_experiment_ids: List[str] = Field(default_factory=list, description="List of matched experiment IDs")
    structured_experiment_ids: List[str] = Field(default_factory=list, description="IDs of structured experiments from domain dataset")
    hindsight_memories: List[Dict[str, Any]] = Field(default_factory=list, description="Recalled memory units with provenance from Hindsight")
    memory_source: str = Field(default="local_dataset", description="Origin of recalled memories: 'hindsight', 'fixture', or 'local_dataset'")
    memory_query: Optional[str] = Field(default=None, description="Exact query string sent to Hindsight Recall")
    positive_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Precedents with positive outcomes")
    negative_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Precedents with negative outcomes")
    neutral_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Precedents with neutral outcomes")
    inconclusive_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Precedents with inconclusive outcomes")
    contextual_caveats: List[str] = Field(default_factory=list, description="Caveats and external factors observed in past tests")
    reflection: Optional[str] = Field(default=None, description="Synthesized reasoning evaluating precedent against current context")
    source_count: int = Field(default=0, description="Total number of historical experiment sources analyzed")
    has_contextual_mismatch: bool = Field(default=False, description="Whether historical precedents diverged in page type or intent")
    mismatch_reason: Optional[str] = Field(default=None, description="Explanation of contextual difference if any")

    def to_evidence_text(self) -> str:
        """Format historical precedent into clean, structured narrative text."""
        if self.source_count == 0 and not self.hindsight_memories:
            return "No relevant historical experiments found in memory bank for this page type and technique."

        lines = [
            f"Found {self.source_count} relevant historical experiment(s) "
            f"({len(self.positive_examples)} positive, {len(self.negative_examples)} negative, "
            f"{len(self.neutral_examples)} neutral, {len(self.inconclusive_examples)} inconclusive):"
        ]

        for exp in self.positive_examples:
            eid = exp.get("experiment_id", "unknown")
            desc = exp.get("hypothesis") or exp.get("treatment_description", "")
            metric_info = exp.get("outcome_summary", "")
            lines.append(f"- [POSITIVE] {eid}: {desc} ({metric_info})")

        for exp in self.negative_examples:
            eid = exp.get("experiment_id", "unknown")
            desc = exp.get("hypothesis") or exp.get("treatment_description", "")
            metric_info = exp.get("outcome_summary", "")
            lines.append(f"- [NEGATIVE] {eid}: {desc} ({metric_info})")

        for exp in self.neutral_examples:
            eid = exp.get("experiment_id", "unknown")
            desc = exp.get("hypothesis") or exp.get("treatment_description", "")
            lines.append(f"- [NEUTRAL] {eid}: {desc}")

        for exp in self.inconclusive_examples:
            eid = exp.get("experiment_id", "unknown")
            desc = exp.get("hypothesis") or exp.get("treatment_description", "")
            lines.append(f"- [INCONCLUSIVE] {eid}: {desc}")

        if self.contextual_caveats:
            lines.append("Contextual Caveats from Precedents:")
            for caveat in self.contextual_caveats:
                lines.append(f"  * {caveat}")

        if self.hindsight_memories:
            lines.append(f"\nHindsight Recalled Memories (Source: {self.memory_source.upper()}):")
            for m in self.hindsight_memories[:3]:
                t = m.get("memory_text", "")
                eid_str = f" [Linked: {m.get('experiment_id')}]" if m.get("experiment_id") else ""
                out_str = f" [Outcome: {m.get('outcome').upper()}]" if m.get("outcome") else ""
                lines.append(f"  * {t[:120]}...{eid_str}{out_str}")

        return "\n".join(lines)


class SEOWorkflowResult(BaseDomainModel):
    """
    Complete output produced by the SearchMind SEO Workflow Engine.

    Encapsulates input request, current evidence, historical context,
    recommendation, approval state, and optional experiment proposal.
    """

    request: SEOAnalysisRequest = Field(..., description="Original input request")
    current_evidence: CurrentSEOEvidence = Field(..., description="Distilled current SEO evidence")
    historical_context: HistoricalSEOContext = Field(..., description="Structured historical memory context")
    recommendation: SEORecommendation = Field(..., description="Generated context-aware recommendation")
    approval_status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING_APPROVAL,
        description="Human approval state (PENDING_APPROVAL, APPROVED, REJECTED)",
    )
    workflow_stopped_at_approval: bool = Field(
        default=True,
        description="Guarantees workflow execution halted at approval gateway before executing experiments",
    )
    experiment_proposal: Optional[SEOExperiment] = Field(
        default=None,
        description="Experiment proposal generated only upon explicit approval",
    )
