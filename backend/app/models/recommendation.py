"""SEO recommendation domain model separating current evidence, historical evidence, reflection, and action."""

from datetime import datetime
from typing import List, Optional
from pydantic import Field, HttpUrl, field_validator

from app.models.base import BaseDomainModel, utc_now


class SEORecommendation(BaseDomainModel):
    """
    Structured output produced by the SearchMind recommendation agent.

    Explicitly separates current SEO data signals, retrieved historical experiment
    evidence, Hindsight reflection reasoning, and the proposed optimization action.
    """

    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    project_id: str = Field(..., description="Project identifier")
    url: HttpUrl = Field(..., description="Target webpage URL")
    observation_ids: List[str] = Field(
        default_factory=list,
        description="Associated observation IDs motivating this recommendation",
    )
    recommendation_type: str = Field(
        ...,
        description="Category of proposed optimization (e.g., commercial_title_alignment, meta_refresh)",
    )
    # 1. Action proposed
    recommendation: str = Field(..., description="Concrete, actionable optimization proposed")
    # 2. What is happening now?
    current_evidence: str = Field(
        ...,
        description="Present-state data and diagnostic findings (e.g., low CTR despite top-3 ranking)",
    )
    # 3. What happened previously in relevant contexts? (Optional for projects without memory)
    historical_evidence: Optional[str] = Field(
        default=None,
        description="Summary of historical experiment outcomes recalled from Hindsight on similar pages",
    )
    # 4. What does Hindsight infer/synthesize from those memories? (Optional)
    reflection: Optional[str] = Field(
        default=None,
        description="Synthesized reasoning produced by Hindsight Reflect evaluating historical evidence against current context",
    )
    supporting_experiment_ids: List[str] = Field(
        default_factory=list,
        description="IDs of previous experiments recalled from Hindsight that support this recommendation",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0 based on evidence strength",
    )
    expected_impact: Optional[str] = Field(
        default=None,
        description="Expected business/traffic impact (e.g., high, medium, +15% CTR)",
    )
    requires_approval: bool = Field(
        default=True,
        description="Human-in-the-loop flag ensuring recommendations require operator approval before execution",
    )
    created_at: datetime = Field(default_factory=utc_now, description="Timestamp when recommendation was generated")

    @field_validator("recommendation_id", "project_id", "recommendation_type", "recommendation", "current_evidence")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        """Ensure critical strings are non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or blank")
        return stripped
