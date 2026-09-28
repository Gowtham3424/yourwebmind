"""Experiment execution and learning service for SearchMind.

Orchestrates:
Approved Recommendation -> Experiment Creation -> Running -> Completed Outcome -> Lesson -> Hindsight Retain
"""

from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.experiments.lesson import build_memory_retain_payload, generate_experiment_lesson
from app.experiments.outcome import compute_experiment_outcome
from app.memory.retain_adapter import BaseRetainAdapter, RetainResult
from app.models.base import utc_now
from app.models.enums import ApprovalStatus, ExperimentStatus
from app.models.experiment import ExperimentOutcome, SEOExperiment
from app.models.recommendation import SEORecommendation

logger = logging.getLogger("searchmind.experiments.service")


class ExperimentExecutionService:
    """
    Manages the lifecycle of SEO experiments and their retention into Hindsight memory.

    Enforces:
    - Human approval requirement before experiment creation
    - Orderly status transitions (PLANNED -> RUNNING -> COMPLETED)
    - Deterministic outcome calculation and non-dogmatic lesson synthesis
    - Idempotent memory retention via BaseRetainAdapter
    """

    def __init__(self, default_bank_id: str = "searchmind-demo"):
        self.default_bank_id = default_bank_id
        self.experiments: Dict[str, SEOExperiment] = {}
        self.outcomes: Dict[str, ExperimentOutcome] = {}
        self.lessons: Dict[str, str] = {}

    def create_experiment_from_recommendation(
        self,
        recommendation: SEORecommendation,
        approval_status: ApprovalStatus,
        experiment_id: Optional[str] = None,
        baseline_metrics: Optional[Dict[str, float]] = None,
        operator_note: Optional[str] = None,
    ) -> SEOExperiment:
        """
        Create a planned SEOExperiment from an approved SEORecommendation.

        Raises:
            PermissionError: If approval_status is not APPROVED.
        """
        # Enforce human approval gateway
        is_approved = (
            approval_status == ApprovalStatus.APPROVED
            or (hasattr(approval_status, "value") and approval_status.value == "approved")
            or str(approval_status).lower() == "approved"
        )
        if not is_approved:
            raise PermissionError(
                f"Cannot create experiment from recommendation '{recommendation.recommendation_id}' "
                f"with status '{approval_status}'. Operator approval is required."
            )

        exp_id = experiment_id or f"exp_{uuid.uuid4().hex[:6]}"
        now = utc_now()

        # Parse baseline metric from recommendation or default
        b_metrics = baseline_metrics or {"ctr": 1.8}
        if "ctr" not in b_metrics:
            b_metrics["ctr"] = 1.8

        ctrl_desc = "Current title and meta snippet in production."
        treat_desc = f"Modified implementation: {recommendation.recommendation}"

        experiment = SEOExperiment(
            experiment_id=exp_id,
            project_id=recommendation.project_id,
            recommendation_id=recommendation.recommendation_id,
            url=recommendation.url,
            experiment_type=recommendation.recommendation_type,
            hypothesis=f"Applying recommendation will produce expected impact: {recommendation.expected_impact or 'CTR improvement'}.",
            control_description=ctrl_desc,
            treatment_description=treat_desc,
            primary_metric="ctr",
            secondary_metrics=["position", "impressions", "clicks"],
            baseline_metrics=b_metrics,
            start_date=now,
            end_date=now + timedelta(days=28),
            status=ExperimentStatus.PLANNED,
            created_at=now,
        )

        self.experiments[exp_id] = experiment
        logger.info(f"Created planned experiment '{exp_id}' for URL: {recommendation.url}")
        return experiment

    def start_experiment(self, experiment: SEOExperiment) -> SEOExperiment:
        """Transition experiment status from PLANNED to RUNNING."""
        if experiment.status != ExperimentStatus.PLANNED:
            logger.warning(f"Experiment '{experiment.experiment_id}' status was '{experiment.status}', transitioning to RUNNING.")

        experiment.status = ExperimentStatus.RUNNING
        self.experiments[experiment.experiment_id] = experiment
        return experiment

    def record_outcome(
        self,
        experiment: SEOExperiment,
        measured_value: float,
        secondary_results: Optional[Dict[str, Any]] = None,
        caveats: Optional[List[str]] = None,
        confidence_note: Optional[str] = None,
        outcome_id: Optional[str] = None,
    ) -> Tuple[SEOExperiment, ExperimentOutcome, str]:
        """
        Record measured results, transition status to COMPLETED, and generate factual lesson.

        Returns:
            Tuple of (completed_experiment, outcome, factual_lesson)
        """
        # Transition status to COMPLETED
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = utc_now()
        self.experiments[experiment.experiment_id] = experiment

        # Deterministic outcome calculation
        outcome = compute_experiment_outcome(
            experiment=experiment,
            measured_value=measured_value,
            secondary_results=secondary_results,
            caveats=caveats,
            confidence_note=confidence_note,
            outcome_id=outcome_id,
            measured_at=experiment.end_date,
        )
        self.outcomes[experiment.experiment_id] = outcome

        # Deterministic lesson generation
        lesson = generate_experiment_lesson(
            experiment=experiment,
            outcome=outcome,
            caveats=caveats,
        )
        self.lessons[experiment.experiment_id] = lesson

        return experiment, outcome, lesson

    def retain_in_memory(
        self,
        experiment: SEOExperiment,
        outcome: ExperimentOutcome,
        lesson: str,
        retain_adapter: BaseRetainAdapter,
        bank_id: Optional[str] = None,
    ) -> RetainResult:
        """
        Format memory document and retain into Hindsight via retain_adapter.
        """
        target_bank = bank_id or self.default_bank_id
        payload = build_memory_retain_payload(
            experiment=experiment,
            outcome=outcome,
            lesson=lesson,
            project_id=experiment.project_id,
        )
        try:
            return retain_adapter.retain_experiment_outcome(payload, bank_id=target_bank)
        except Exception as exc:
            logger.error(f"Retain adapter failed for experiment '{experiment.experiment_id}': {exc}")
            return RetainResult(
                source="error",
                memory_bank=target_bank,
                experiment_id=experiment.experiment_id,
                retained=False,
                document_id=payload.get("document_id"),
                latency_seconds=0.0,
                token_usage={"error": str(exc)},
            )

    def execute_learning_loop(
        self,
        recommendation: SEORecommendation,
        approval_status: ApprovalStatus,
        measured_value: float,
        retain_adapter: BaseRetainAdapter,
        experiment_id: Optional[str] = None,
        secondary_results: Optional[Dict[str, Any]] = None,
        caveats: Optional[List[str]] = None,
        bank_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the complete learning loop:
        Approved Recommendation -> Experiment -> Outcome -> Lesson -> Retain
        """
        target_bank = bank_id or self.default_bank_id

        # 1. Approval gateway & Experiment creation
        experiment = self.create_experiment_from_recommendation(
            recommendation=recommendation,
            approval_status=approval_status,
            experiment_id=experiment_id,
        )

        # 2. Start trial
        self.start_experiment(experiment)

        # 3. Record outcome & lesson
        completed_exp, outcome, lesson = self.record_outcome(
            experiment=experiment,
            measured_value=measured_value,
            secondary_results=secondary_results,
            caveats=caveats,
        )

        # 4. Retain into memory
        retain_result = self.retain_in_memory(
            experiment=completed_exp,
            outcome=outcome,
            lesson=lesson,
            retain_adapter=retain_adapter,
            bank_id=target_bank,
        )

        return {
            "experiment": completed_exp,
            "outcome": outcome,
            "lesson": lesson,
            "retain_result": retain_result,
        }
