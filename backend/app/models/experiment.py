"""SEO experiment and experiment outcome domain models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field, HttpUrl, field_validator, model_validator

from app.models.base import BaseDomainModel, utc_now
from app.models.enums import ExperimentStatus, OutcomeClass


class SEOExperiment(BaseDomainModel):
    """
    Represents a controlled SEO test or optimization trial.

    SearchMind tracks experiments over time so Hindsight can learn which changes
    produce positive or negative results across different page contexts.
    """

    experiment_id: str = Field(..., description="Unique experiment identifier")
    project_id: str = Field(..., description="Project identifier")
    url: HttpUrl = Field(..., description="Target webpage URL being tested")
    experiment_type: str = Field(
        ...,
        description="Type of test (e.g., title_tag_test, meta_description_test, content_expansion)",
    )
    hypothesis: str = Field(..., description="Hypothesis being evaluated")
    control_description: str = Field(..., description="Baseline/control version description")
    treatment_description: str = Field(..., description="Modified/treatment version description")
    primary_metric: str = Field(..., description="Key performance indicator (e.g., ctr, clicks, position)")
    secondary_metrics: List[str] = Field(default_factory=list, description="Supporting metrics tracked")
    baseline_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Pre-experiment baseline measurements (e.g., {'ctr': 1.8, 'position': 4.2})",
    )
    start_date: datetime = Field(..., description="Scheduled or actual start datetime")
    end_date: Optional[datetime] = Field(default=None, description="Scheduled or actual completion datetime")
    status: ExperimentStatus = Field(
        default=ExperimentStatus.PLANNED,
        description="Current experiment status: planned, running, completed, cancelled",
    )
    created_at: datetime = Field(default_factory=utc_now, description="Record creation timestamp")

    @field_validator(
        "experiment_id",
        "project_id",
        "experiment_type",
        "hypothesis",
        "control_description",
        "treatment_description",
        "primary_metric",
    )
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        """Ensure critical strings are non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or blank")
        return stripped

    @model_validator(mode="after")
    def validate_dates(self) -> "SEOExperiment":
        """Verify that experiment end_date is not earlier than start_date."""
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("Experiment end_date cannot be before start_date")
        return self


class ExperimentOutcome(BaseDomainModel):
    """
    Represents the observed, measured results of an SEO experiment.

    Retained in Hindsight memory to provide historical evidence for future recommendations.
    """

    outcome_id: str = Field(..., description="Unique outcome identifier")
    experiment_id: str = Field(..., description="Reference to the associated SEOExperiment")
    project_id: str = Field(..., description="Project identifier")
    metric_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed post-experiment metric measurements",
    )
    primary_metric_before: float = Field(..., description="Metric value prior to experiment")
    primary_metric_after: float = Field(..., description="Metric value after experiment conclusion")
    absolute_change: Optional[float] = Field(default=None, description="Absolute change (after - before)")
    percentage_change: Optional[float] = Field(
        default=None,
        description="Percentage change ((after - before) / before * 100)",
    )
    outcome_class: OutcomeClass = Field(
        ...,
        description="Empirical classification: positive, negative, neutral, or inconclusive",
    )
    confidence_note: Optional[str] = Field(default=None, description="Statistical or observational confidence notes")
    interpretation: str = Field(..., description="Human or agent interpretation of why the outcome occurred")
    measured_at: datetime = Field(default_factory=utc_now, description="Timestamp when outcome was evaluated")

    @field_validator("outcome_id", "experiment_id", "project_id", "interpretation")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        """Ensure critical strings are non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or blank")
        return stripped

    @model_validator(mode="after")
    def compute_changes(self) -> "ExperimentOutcome":
        """Automatically calculate absolute and percentage changes if not provided."""
        if self.absolute_change is None:
            self.absolute_change = round(self.primary_metric_after - self.primary_metric_before, 4)
        if self.percentage_change is None and self.primary_metric_before != 0:
            self.percentage_change = round(
                ((self.primary_metric_after - self.primary_metric_before) / abs(self.primary_metric_before)) * 100,
                2,
            )
        return self
