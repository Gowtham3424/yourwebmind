"""Context-aware recommendation engine for SearchMind SEO Agent.

Translates current SEO evidence and historical memory context into a concrete,
falsifiable SEORecommendation while enforcing transparent decision rules and confidence scoring.
"""

from typing import List, Optional
import uuid

from app.agents.schemas import CurrentSEOEvidence, HistoricalSEOContext
from app.models.enums import ObservationSeverity
from app.models.recommendation import SEORecommendation


class RecommendationEngine:
    """
    Deterministic rule-based reasoning engine implementing context-aware SEO recommendation rules.

    Enforces:
    - Rule A: CTR decline + title precedent -> title experiment proposal
    - Rule B: Mixed precedents -> explicit non-dogmatic, unproven framing
    - Rule C: Predominantly negative precedents -> caution and alternative proposal
    - Rule D: Inconclusive precedents -> exploratory measurement rather than certainty
    - Rule E: Contextual mismatch -> confidence reduction and contextual qualification
    - Rule F: Zero precedent -> explicit absence of memory, no invented certainty
    """

    def compute_confidence(
        self,
        current_evidence: CurrentSEOEvidence,
        historical_context: HistoricalSEOContext,
    ) -> float:
        """
        Calculate an explainable, bounded confidence score (0.10 to 0.85).

        Derived deterministically from:
        - Presence of historical evidence (Rule F)
        - Contextual alignment of page type and search intent (Rule E)
        - Consistency of outcome distribution (Rules B, C, D)
        - Severity and clarity of current diagnostic signals
        """
        # Rule F: No historical evidence in memory
        if historical_context.source_count == 0:
            return 0.35

        score = 0.50  # Balanced baseline

        pos_count = len(historical_context.positive_examples)
        neg_count = len(historical_context.negative_examples)
        neu_count = len(historical_context.neutral_examples)
        inc_count = len(historical_context.inconclusive_examples)

        # Outcome consistency adjustments
        if pos_count > 0 and neg_count == 0 and inc_count == 0:
            # Consistent positive precedent (+0.20 to +0.25 based on sample size)
            score += min(0.25, 0.15 + (pos_count * 0.05))
        elif pos_count > 0 and neg_count > 0:
            # Rule B: Mixed results reduce confidence to near baseline
            score = 0.52
        elif neg_count > 0 and pos_count == 0:
            # Rule C: Confident that caution or alternative is warranted
            score = 0.62
        elif inc_count > 0 and pos_count == 0 and neg_count == 0:
            # Rule D: Inconclusive past data warrants exploratory confidence
            score = 0.42
        elif neu_count == historical_context.source_count:
            score = 0.45

        # Current diagnostic severity signal
        if current_evidence.highest_severity in (ObservationSeverity.HIGH, ObservationSeverity.CRITICAL):
            score += 0.05
        elif current_evidence.highest_severity == ObservationSeverity.INFO:
            score -= 0.05

        # Rule E: Contextual mismatch penalty
        if historical_context.has_contextual_mismatch:
            score -= 0.15

        # Clamp between 0.10 and 0.85 (never 1.0 to preserve non-dogmatism)
        return round(max(0.10, min(0.85, score)), 2)

    def generate_recommendation(
        self,
        project_id: str,
        current_evidence: CurrentSEOEvidence,
        historical_context: HistoricalSEOContext,
        recommendation_id: Optional[str] = None,
    ) -> SEORecommendation:
        """
        Generate an SEORecommendation adhering strictly to SearchMind's separation of:
        - Recommendation action
        - Current evidence
        - Historical evidence
        - Reflection
        - Bounded confidence
        - Human-in-the-loop approval requirement
        """
        rec_id = recommendation_id or f"rec_{uuid.uuid4().hex[:8]}"
        confidence = self.compute_confidence(current_evidence, historical_context)

        pos_count = len(historical_context.positive_examples)
        neg_count = len(historical_context.negative_examples)
        inc_count = len(historical_context.inconclusive_examples)
        source_count = historical_context.source_count

        rec_type = "title_tag_optimization"
        action_text: str
        expected_impact: str

        # Determine recommendation narrative based on deterministic rules
        if source_count == 0:
            # Rule F: No precedent exists
            rec_type = "exploratory_title_test"
            action_text = (
                f"Formulate an exploratory title tag test for '{current_evidence.target_url}' targeting "
                f"'{current_evidence.keyword or 'primary query'}'. Because no historical experiments exist in "
                "the project memory bank, establish a clean 28-day baseline before drawing conclusions."
            )
            expected_impact = "Uncertain (+0% to +10% CTR exploratory range; unproven in this domain)"

        elif historical_context.has_contextual_mismatch:
            # Rule E: Contextual mismatch (e.g. category precedent applied to product page)
            rec_type = "adapted_contextual_title_test"
            action_text = (
                f"Adapt the title tag optimization cautiously for product page '{current_evidence.target_url}'. "
                f"Note: {historical_context.mismatch_reason} Conduct a controlled 21-day trial with brand term preserved."
            )
            expected_impact = "Moderate / Context-dependent (+5% to +15% CTR conditional on intent match)"

        elif pos_count > 0 and neg_count > 0:
            # Rule B: Mixed outcomes (some positive, some negative)
            rec_type = "balanced_title_tag_test"
            action_text = (
                f"Test a revised title tag placing the primary search keyword '{current_evidence.keyword or 'target query'}' "
                "near the front of the snippet, while strictly retaining brand name and avoiding aggressive promotional discount modifiers."
            )
            expected_impact = "Estimated +15% to +30% CTR improvement if promotional discount phrasing is avoided"

        elif neg_count > 0 and pos_count == 0:
            # Rule C: Predominantly negative precedent
            rec_type = "conservative_content_alternative"
            action_text = (
                f"Do NOT execute aggressive title tag modification on '{current_evidence.target_url}'. "
                "Historical precedent demonstrates that altering existing commercial titles in this context decreased CTR and damaged brand trust. "
                "Instead, recommend testing supportive on-page product specifications or FAQ accordion markup."
            )
            expected_impact = "Risk mitigation; prevents anticipated -10% to -15% CTR erosion seen in past trials"

        elif inc_count > 0 and pos_count == 0:
            # Rule D: Inconclusive precedent
            rec_type = "controlled_measurement_trial"
            action_text = (
                f"Run a strictly monitored title tag test on '{current_evidence.target_url}' with daily SERP rank logging. "
                "Past experiments were inconclusive due to algorithm volatility and seasonality. A longer 35-day evaluation window is recommended."
            )
            expected_impact = "Directional clarity (+5% to +15% potential lift under non-volatile SERP conditions)"

        else:
            # Predominantly positive precedent
            rec_type = "evidence_backed_title_optimization"
            action_text = (
                f"Apply keyword-first title tag restructuring on '{current_evidence.target_url}', moving high-volume query "
                f"'{current_evidence.keyword or 'primary query'}' to the front while preserving store branding."
            )
            expected_impact = "Anticipated +20% to +45% relative CTR lift based on positive historical precedents"

        # Format evidence and reflection text
        curr_text = current_evidence.to_evidence_text()
        hist_text = historical_context.to_evidence_text()
        reflection_text = historical_context.reflection or "No synthesized reflection available."

        return SEORecommendation(
            recommendation_id=rec_id,
            project_id=project_id,
            url=current_evidence.target_url,
            observation_ids=current_evidence.observation_ids,
            recommendation_type=rec_type,
            recommendation=action_text,
            current_evidence=curr_text,
            historical_evidence=hist_text,
            reflection=reflection_text,
            supporting_experiment_ids=historical_context.relevant_experiment_ids,
            confidence=confidence,
            expected_impact=expected_impact,
            requires_approval=True,
        )
