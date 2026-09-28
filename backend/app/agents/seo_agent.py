"""High-level SEO Agent orchestrator for SearchMind.

Orchestrates deterministic diagnostic analysis, historical precedent retrieval,
qualified recommendation generation, and human approval workflows without arbitrary LLM calls.
"""

from typing import Optional
from pathlib import Path

from app.agents.historical_analyzer import HistoricalAnalyzer
from app.agents.recommendation_engine import RecommendationEngine
from app.agents.schemas import SEOAnalysisRequest, SEOWorkflowResult
from app.agents.workflow import SEOWorkflowEngine


from app.memory import BaseRecallAdapter, BaseReflectAdapter


class SEOAgent:
    """
    SearchMind SEO Agent Core.

    Coordinates evidence-based SEO reasoning across:
    Current SEO Data -> Historical Memory -> Qualified Recommendation -> Human Approval
    """

    def __init__(
        self,
        dataset_dir: Optional[Path] = None,
        workflow_engine: Optional[SEOWorkflowEngine] = None,
        recall_adapter: Optional[BaseRecallAdapter] = None,
        reflect_adapter: Optional[BaseReflectAdapter] = None,
        enable_reflect: bool = False,
        default_bank_id: str = "searchmind-demo",
    ):
        if workflow_engine is not None:
            self.workflow = workflow_engine
        else:
            analyzer = HistoricalAnalyzer(dataset_dir=dataset_dir)
            rec_engine = RecommendationEngine()
            self.workflow = SEOWorkflowEngine(
                historical_analyzer=analyzer,
                recommendation_engine=rec_engine,
                recall_adapter=recall_adapter,
                reflect_adapter=reflect_adapter,
                enable_reflect=enable_reflect,
                default_bank_id=default_bank_id,
            )

    def analyze(
        self,
        request: SEOAnalysisRequest,
        memory_bank: Optional[str] = None,
        enable_reflect: Optional[bool] = None,
    ) -> SEOWorkflowResult:
        """
        Analyze current SEO state and generate a context-aware recommendation.

        Always halts at the Human Approval Gateway (status = PENDING_APPROVAL).
        """
        return self.workflow.run_analysis_workflow(
            request=request,
            memory_bank=memory_bank,
            enable_reflect=enable_reflect,
        )

    def approve(
        self,
        result: SEOWorkflowResult,
        operator_note: Optional[str] = None,
    ) -> SEOWorkflowResult:
        """Approve recommendation and generate planned experiment proposal."""
        return self.workflow.process_human_approval(
            workflow_result=result,
            approved=True,
            operator_note=operator_note,
        )

    def reject(
        self,
        result: SEOWorkflowResult,
        operator_note: Optional[str] = None,
    ) -> SEOWorkflowResult:
        """Reject recommendation without generating experiment proposal."""
        return self.workflow.process_human_approval(
            workflow_result=result,
            approved=False,
            operator_note=operator_note,
        )
