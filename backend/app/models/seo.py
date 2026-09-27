"""SEO observation and optimization decision domain models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field, HttpUrl, field_validator, model_validator

from app.models.base import BaseDomainModel, utc_now
from app.models.enums import ObservationSeverity


class SEOObservation(BaseDomainModel):
    """
    Represents an empirical, measurable SEO signal or diagnostic finding.

    SearchMind preserves the underlying evidence behind each observation rather than
    collapsing observations into arbitrary universal scores.
    """

    observation_id: str = Field(..., description="Unique identifier for this observation")
    project_id: str = Field(..., description="Project identifier")
    url: HttpUrl = Field(..., description="Target page URL")
    keyword: Optional[str] = Field(default=None, description="Associated search keyword or query")
    observation_type: str = Field(
        ...,
        description="Type of signal (e.g., low_ctr, ranking_opportunity, content_gap, intent_mismatch)",
    )
    metric_name: str = Field(..., description="Primary metric tracked (e.g., ctr, impressions, position, clicks)")
    current_value: float = Field(..., description="Current measured value of the metric")
    previous_value: Optional[float] = Field(default=None, description="Baseline or previous value of the metric")
    delta: Optional[float] = Field(default=None, description="Calculated difference (current - previous)")
    unit: Optional[str] = Field(default=None, description="Metric unit (e.g., '%', 'pos', 'count')")
    severity: ObservationSeverity = Field(
        default=ObservationSeverity.INFO,
        description="Controlled severity level: info, low, medium, high, critical",
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Underlying diagnostic data, search console queries, or SERP facts supporting this finding",
    )
    observed_at: datetime = Field(default_factory=utc_now, description="Timestamp of observation")

    @field_validator("observation_id", "project_id", "observation_type", "metric_name")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        """Ensure critical strings are non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or blank")
        return stripped

    @model_validator(mode="before")
    @classmethod
    def compute_delta(cls, data: Any) -> Any:
        """Automatically calculate delta if previous_value is set and delta is not explicitly provided."""
        if isinstance(data, dict):
            curr = data.get("current_value")
            prev = data.get("previous_value")
            if curr is not None and prev is not None and data.get("delta") is None:
                data["delta"] = round(curr - prev, 4)
        return data


class OptimizationDecision(BaseDomainModel):
    """
    Represents a concrete decision made in response to one or more SEO observations.

    Captures the rationale, hypothesis, and proposed modifications to ensure
    decisions can be converted into tracked experiments.
    """

    decision_id: str = Field(..., description="Unique identifier for this decision")
    project_id: str = Field(..., description="Project identifier")
    url: HttpUrl = Field(..., description="Target webpage URL")
    observation_ids: List[str] = Field(
        default_factory=list,
        description="List of observation IDs that informed or triggered this decision",
    )
    decision_type: str = Field(
        ...,
        description="Category of decision (e.g., title_update, meta_update, content_update, schema_update, technical_fix)",
    )
    hypothesis: str = Field(..., description="The falsifiable hypothesis behind the proposed change")
    rationale: str = Field(..., description="Explanation of why this optimization is expected to succeed")
    expected_effect: Optional[str] = Field(default=None, description="Expected directional or quantitative impact")
    proposed_changes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-value definition of changes (e.g., {'title': {'from': '...', 'to': '...'}})",
    )
    decided_at: datetime = Field(default_factory=utc_now, description="Timestamp when decision was made")

    @field_validator("decision_id", "project_id", "decision_type", "hypothesis", "rationale")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        """Ensure critical strings are non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or blank")
        return stripped
