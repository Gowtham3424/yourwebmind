"""Deterministic historical SEO memory analysis layer.

Extracts, filters, and synthesizes historical experiment precedents and outcomes
from SearchMind demo memory without requiring live LLM calls during ordinary workflow execution.
"""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from app.agents.schemas import CurrentSEOEvidence, HistoricalSEOContext
from app.models.enums import OutcomeClass
from app.seo.demo_dataset import load_demo_dataset


def infer_page_type_from_url(url_str: str) -> str:
    """Infer semantic page template/type from a URL path."""
    u = url_str.lower()
    if "/product/" in u or "/products/" in u or "/item/" in u:
        return "product"
    if "/collections/" in u or "/collection/" in u or "/category/" in u or "/categories/" in u:
        return "category"
    if "/blog/" in u or "/guides/" in u or "/guide/" in u or "/articles/" in u or "/learn/" in u or "/comparisons/" in u:
        return "guide"
    if u.rstrip("/").count("/") <= 2 or u.endswith(".example/") or u.endswith(".example"):
        return "homepage"
    return "page"


class HistoricalAnalyzer:
    """
    Local deterministic analyzer for historical SEO experiments and outcomes.

    Provides context-aware precedent matching across page types, search intents,
    and optimization techniques while strictly preserving empirical uncertainty
    and non-dogmatic reasoning.
    """

    def __init__(self, dataset_dir: Optional[Path] = None, dataset_data: Optional[Dict[str, Any]] = None):
        if dataset_data is not None:
            self._data = dataset_data
        else:
            self._data = load_demo_dataset(dataset_dir)

        # Build experiment and outcome lookup maps
        self.experiments: List[Dict[str, Any]] = self._data.get("experiments.json") or self._data.get("experiments") or []
        self.outcomes: List[Dict[str, Any]] = self._data.get("outcomes.json") or self._data.get("outcomes") or []

        self.outcome_by_exp_id: Dict[str, Dict[str, Any]] = {
            item["experiment_id"]: item for item in self.outcomes
        }
        self.exp_by_id: Dict[str, Dict[str, Any]] = {
            item["experiment_id"]: item for item in self.experiments
        }

    def find_relevant_experiments(
        self,
        page_type: Optional[str] = None,
        search_intent: Optional[str] = None,
        technique: Optional[str] = None,
        target_url: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """
        Identify historical experiments matching technique, page type, or search intent.

        Returns:
            Tuple of (matched_experiments_with_outcomes, has_contextual_mismatch, mismatch_reason)
        """
        norm_technique = (technique or "").lower().strip()
        norm_page_type = (page_type or "").lower().strip()
        norm_intent = (search_intent or "").lower().strip()

        # Step 1: Filter experiments by technique / keywords
        technique_matches: List[Dict[str, Any]] = []
        for exp in self.experiments:
            exp_id = exp["experiment_id"]
            outcome = self.outcome_by_exp_id.get(exp_id)
            if not outcome:
                continue

            exp_type = exp.get("experiment_type", "").lower()
            hyp = exp.get("hypothesis", "").lower()
            ctrl = exp.get("control_description", "").lower()
            treat = exp.get("treatment_description", "").lower()
            combined_text = f"{exp_type} {hyp} {ctrl} {treat}"

            match = False
            if not norm_technique:
                match = True
            elif norm_technique in exp_type or norm_technique in hyp:
                match = True
            elif any(token in combined_text for token in norm_technique.replace("_", " ").split()):
                match = True

            if match:
                exp_copy = dict(exp)
                exp_copy["outcome"] = outcome
                exp_copy["outcome_class"] = outcome.get("outcome_class")
                exp_copy["interpretation"] = outcome.get("interpretation", "")
                exp_copy["outcome_summary"] = (
                    f"{exp.get('primary_metric')}: {outcome.get('primary_metric_before')} -> "
                    f"{outcome.get('primary_metric_after')} ({outcome.get('percentage_change', 0.0):+.1f}%)"
                )
                exp_copy["inferred_page_type"] = infer_page_type_from_url(exp.get("url", ""))
                technique_matches.append(exp_copy)

        if not technique_matches:
            return [], False, None

        # Step 2: Contextual matching (page_type and search_intent)
        exact_context_matches: List[Dict[str, Any]] = []
        partial_matches: List[Dict[str, Any]] = []

        for exp in technique_matches:
            exp_page_type = exp["inferred_page_type"]
            page_type_match = not norm_page_type or exp_page_type == norm_page_type

            if page_type_match:
                exact_context_matches.append(exp)
            else:
                partial_matches.append(exp)

        if exact_context_matches:
            return exact_context_matches, False, None

        # If no exact page-type matches, return partial matches with explicit contextual mismatch flag
        mismatch_reason = (
            f"Precedents evaluated for this technique occurred on '{partial_matches[0]['inferred_page_type']}' "
            f"pages, whereas current target is a '{norm_page_type or 'different'}' page."
        )
        return partial_matches, True, mismatch_reason

    def build_historical_context(
        self,
        current_evidence: CurrentSEOEvidence,
        technique_focus: Optional[str] = None,
        recalled_memories: Optional[List[Any]] = None,
        memory_source: str = "local_dataset",
        memory_query: Optional[str] = None,
    ) -> HistoricalSEOContext:
        """
        Build a comprehensive, structured HistoricalSEOContext for the given current evidence,
        incorporating both structured domain dataset experiments and Hindsight recalled memories.
        """
        page_type = current_evidence.page_type or infer_page_type_from_url(str(current_evidence.target_url))
        query_desc = memory_query or f"Technique: '{technique_focus or 'general'}' on page_type: '{page_type}'"

        matches, has_mismatch, mismatch_reason = self.find_relevant_experiments(
            page_type=page_type,
            search_intent=current_evidence.search_intent,
            technique=technique_focus,
            target_url=str(current_evidence.target_url),
        )

        # Process external recalled memories (from Hindsight or test fixture)
        processed_hindsight_memories: List[Dict[str, Any]] = []
        if recalled_memories:
            for item in recalled_memories:
                m_dict = item.model_dump() if hasattr(item, "model_dump") else (item.dict() if hasattr(item, "dict") else dict(item))
                processed_hindsight_memories.append(m_dict)
                eid = m_dict.get("experiment_id")
                # If memory refers to a known experiment not yet in matches, link it
                if eid and eid in self.exp_by_id and not any(m["experiment_id"] == eid for m in matches):
                    exp_obj = dict(self.exp_by_id[eid])
                    outcome_obj = self.outcome_by_exp_id.get(eid, {})
                    exp_obj["outcome"] = outcome_obj
                    exp_obj["outcome_class"] = outcome_obj.get("outcome_class") or m_dict.get("outcome")
                    exp_obj["interpretation"] = outcome_obj.get("interpretation", "")
                    exp_obj["outcome_summary"] = (
                        f"{exp_obj.get('primary_metric')}: {outcome_obj.get('primary_metric_before')} -> "
                        f"{outcome_obj.get('primary_metric_after')} ({outcome_obj.get('percentage_change', 0.0):+.1f}%)"
                    ) if outcome_obj else ""
                    exp_obj["inferred_page_type"] = infer_page_type_from_url(exp_obj.get("url", ""))
                    matches.append(exp_obj)

        if not matches and not processed_hindsight_memories:
            reflection = (
                f"No historical experiments in memory bank '{self._data.get('bank_id', 'searchmind-demo')}' "
                f"specifically evaluate technique '{technique_focus or 'unspecified'}' on '{page_type}' pages. "
                "Precedent cannot be assumed; empirical testing with strict baseline measurement is required."
            )
            return HistoricalSEOContext(
                query=query_desc,
                recalled_memories=[],
                relevant_experiment_ids=[],
                structured_experiment_ids=[],
                hindsight_memories=[],
                memory_source=memory_source,
                memory_query=query_desc,
                positive_examples=[],
                negative_examples=[],
                neutral_examples=[],
                inconclusive_examples=[],
                contextual_caveats=[],
                reflection=reflection,
                source_count=0,
                has_contextual_mismatch=False,
                mismatch_reason=None,
            )

        pos: List[Dict[str, Any]] = []
        neg: List[Dict[str, Any]] = []
        neu: List[Dict[str, Any]] = []
        inc: List[Dict[str, Any]] = []
        caveats: List[str] = []
        relevant_ids: List[str] = []
        structured_ids: List[str] = []

        for exp in matches:
            eid = exp["experiment_id"]
            relevant_ids.append(eid)
            structured_ids.append(eid)
            ocls = exp.get("outcome_class")
            interp = exp.get("interpretation", "")

            # Extract caveats from interpretation if present
            if "caveat" in interp.lower() or "overlap" in interp.lower() or "season" in interp.lower():
                clauses = [s.strip() for s in interp.split(".") if any(w in s.lower() for w in ["caveat", "however", "overlap", "season", "caution"])]
                if clauses:
                    caveats.append(f"[{eid}] {clauses[0]}.")
                else:
                    caveats.append(f"[{eid}] {interp[:120]}...")

            if ocls == OutcomeClass.POSITIVE or ocls == "positive":
                pos.append(exp)
            elif ocls == OutcomeClass.NEGATIVE or ocls == "negative":
                neg.append(exp)
            elif ocls == OutcomeClass.NEUTRAL or ocls == "neutral":
                neu.append(exp)
            elif ocls == OutcomeClass.INCONCLUSIVE or ocls == "inconclusive":
                inc.append(exp)

        # Also pull any explicit caveats from recalled memories
        for hm in processed_hindsight_memories:
            htext = hm.get("memory_text", "")
            if any(w in htext.lower() for w in ["caveat", "seasonal", "volatility"]) and not any(htext[:40] in c for c in caveats):
                caveats.append(f"[Hindsight] {htext[:140]}...")

        # Synthesize non-dogmatic reflection
        reflection_parts = []
        if has_mismatch:
            reflection_parts.append(f"Contextual note: {mismatch_reason}")

        total_cnt = len(matches)
        if len(pos) > 0 and len(neg) > 0:
            reflection_parts.append(
                f"Historical precedents are mixed across {total_cnt} experiments "
                f"({len(pos)} positive, {len(neg)} negative). "
                "The tactic is sensitive to execution context. Keyword-intent alignment yielded gains, "
                "while aggressive promotional language damaged click performance."
            )
        elif len(pos) > 0 and len(neg) == 0 and len(inc) == 0:
            reflection_parts.append(
                f"Historical precedents showed consistent positive outcomes across {len(pos)} experiment(s). "
                "However, results were qualified by context (e.g. bounce rate trade-offs or seasonal trends), "
                "so continued measurement is warranted."
            )
        elif len(neg) > 0 and len(pos) == 0:
            reflection_parts.append(
                f"Historical precedents in similar contexts were predominantly negative ({len(neg)} negative result(s)). "
                "Applying this technique carries elevated risk. An alternative hypothesis or high-caution control is advised."
            )
        elif len(inc) > 0 and len(pos) == 0 and len(neg) == 0:
            reflection_parts.append(
                f"All {len(inc)} historical precedent(s) were classified as inconclusive due to external confounding factors "
                "(such as Google algorithm updates or seasonal demand shifts). Past data does not establish directional certainty."
            )
        elif len(neu) == total_cnt:
            reflection_parts.append(
                f"Historical trials showed neutral impact (under 2% change) across {total_cnt} test(s). "
                "The optimization produced minimal ranking or CTR lift in past tests."
            )
        else:
            reflection_parts.append(
                f"Historical precedents across {total_cnt} trial(s) show varying empirical results "
                f"({len(pos)} positive, {len(neg)} negative, {len(neu)} neutral, {len(inc)} inconclusive). "
                "Testing must be treated as a controlled trial rather than a guaranteed win."
            )

        reflection = " ".join(reflection_parts)

        return HistoricalSEOContext(
            query=query_desc,
            recalled_memories=matches,
            relevant_experiment_ids=relevant_ids,
            structured_experiment_ids=structured_ids,
            hindsight_memories=processed_hindsight_memories,
            memory_source=memory_source,
            memory_query=query_desc,
            positive_examples=pos,
            negative_examples=neg,
            neutral_examples=neu,
            inconclusive_examples=inc,
            contextual_caveats=caveats,
            reflection=reflection,
            source_count=total_cnt,
            has_contextual_mismatch=has_mismatch,
            mismatch_reason=mismatch_reason,
        )
