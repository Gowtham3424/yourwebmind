"""Hindsight memory reflect adapter and reflection reasoning models for SearchMind.

Provides an optional reasoning layer over retrieved historical SEO experiments,
synthesizing cross-experiment patterns, caveats, and contextual factors without
turning empirical observations into dogmatic rules.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import re
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.base import utc_now
from app.services.hindsight_service import get_hindsight_service

logger = logging.getLogger("searchmind.memory.reflect")


def sanitize_non_dogmatic_reflection(text: str) -> str:
    """
    Ensure reflection output remains contextual, qualified, and non-dogmatic.

    Replaces sweeping absolute assertions ('always', 'never', 'guarantees', 'proves')
    with empirical, context-bounded phrasing.
    """
    if not text:
        return text

    sanitized = text

    # Dogmatic phrase replacements
    replacements = [
        (r"\balways increases\b", "was observed to increase in comparable past contexts"),
        (r"\balways improves\b", "was observed to improve in comparable past contexts"),
        (r"\balways works\b", "showed positive efficacy in specific tested contexts"),
        (r"\balways\b", "consistently in observed trials"),
        (r"\bnever works\b", "consistently underperformed in comparable trials"),
        (r"\bnever\b", "rarely in observed trials"),
        (r"\bguarantees\b", "suggests potential for"),
        (r"\bguaranteed\b", "anticipated"),
        (r"\bproves that all\b", "suggests that tested"),
        (r"\bproves that\b", "indicates that in past tests,"),
        (r"\buniversal rule\b", "contextual pattern"),
    ]

    for pattern, repl in replacements:
        sanitized = re.sub(pattern, repl, sanitized, flags=re.IGNORECASE)

    # Ensure an explicit caveat disclosure is attached if not already present
    advisory = (
        "Note: Historical observations are contextual to tested conditions and do not constitute universal SEO rules."
    )
    if advisory not in sanitized and "universal" not in sanitized.lower():
        sanitized = f"{sanitized.strip()}\n\n{advisory}"

    return sanitized.strip()


def parse_reflection_sections(text: str) -> Dict[str, List[str]]:
    """
    Parse qualitative reflection narrative into categorized thematic observations:
    - patterns
    - supporting_evidence
    - conflicting_evidence
    - caveats
    - contextual_factors
    """
    sections: Dict[str, List[str]] = {
        "patterns": [],
        "supporting_evidence": [],
        "conflicting_evidence": [],
        "caveats": [],
        "contextual_factors": [],
    }

    if not text:
        return sections

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    current_category: Optional[str] = None

    for line in lines:
        lower = line.lower()
        if "pattern" in lower and (":" in lower or "#" in lower):
            current_category = "patterns"
            continue
        elif "support" in lower and (":" in lower or "#" in lower):
            current_category = "supporting_evidence"
            continue
        elif ("conflict" in lower or "negative" in lower or "contradict" in lower) and (":" in lower or "#" in lower):
            current_category = "conflicting_evidence"
            continue
        elif ("caveat" in lower or "confound" in lower or "risk" in lower) and (":" in lower or "#" in lower):
            current_category = "caveats"
            continue
        elif ("context" in lower or "factor" in lower or "page type" in lower) and (":" in lower or "#" in lower):
            current_category = "contextual_factors"
            continue

        clean_bullet = re.sub(r"^[-*•\d.]+\s*", "", line).strip()
        if clean_bullet and len(clean_bullet) > 10:
            if current_category:
                sections[current_category].append(clean_bullet)
            else:
                # Classify line by keyword if no heading active
                if any(w in lower for w in ["caveat", "season", "volatil", "algorithm", "external"]):
                    sections["caveats"].append(clean_bullet)
                elif any(w in lower for w in ["conflict", "decrease", "decline", "drop", "negative"]):
                    sections["conflicting_evidence"].append(clean_bullet)
                elif any(w in lower for w in ["increase", "positive", "lift", "gain", "improve"]):
                    sections["supporting_evidence"].append(clean_bullet)
                elif any(w in lower for w in ["intent", "template", "category", "product", "guide"]):
                    sections["contextual_factors"].append(clean_bullet)
                else:
                    sections["patterns"].append(clean_bullet)

    return sections


class ReflectResult(BaseModel):
    """
    Structured outcome of a Hindsight Reflect reasoning operation.

    Declares explicit provenance, target memory bank, qualitative synthesis,
    thematic evidence breakdowns, latency, and optional token expenditure.
    """

    source: str = Field(
        default="hindsight",
        description="Origin of reflect operation ('hindsight' or 'fixture')",
    )
    memory_bank: str = Field(..., description="Target Hindsight memory bank")
    query: str = Field(..., description="Reflection reasoning query")
    synthesis_text: str = Field(
        default="",
        description="Natural language reflection text produced by Hindsight",
    )
    patterns: List[str] = Field(
        default_factory=list,
        description="Observed patterns across historical experiments",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Historical evidence supporting the proposed tactic",
    )
    conflicting_evidence: List[str] = Field(
        default_factory=list,
        description="Historical evidence conflicting with or contradicting the tactic",
    )
    caveats: List[str] = Field(
        default_factory=list,
        description="Contextual caveats and external confounding factors",
    )
    contextual_factors: List[str] = Field(
        default_factory=list,
        description="Specific page type or search intent dependencies",
    )
    latency_seconds: float = Field(
        default=0.0,
        description="Reflection operation latency in seconds",
    )
    token_usage: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Token usage details if returned by Hindsight",
    )
    success: bool = Field(default=True, description="Whether reflection succeeded")
    error: Optional[str] = Field(
        default=None,
        description="Error message if reflection failed or was quota-blocked",
    )
    timestamp: datetime = Field(default_factory=utc_now, description="Timestamp of reflection")


class BaseReflectAdapter(ABC):
    """Abstract interface for reflecting over stored memories."""

    @abstractmethod
    def reflect(
        self,
        query: str,
        bank_id: str = "searchmind-demo",
        context: Optional[str] = None,
    ) -> ReflectResult:
        """Execute reasoning synthesis over historical memories."""
        pass


class HindsightReflectAdapter(BaseReflectAdapter):
    """
    Live adapter delegating to HindsightService for persistent memory reflection.

    Enforces:
    - Automatic connection verification and initialization
    - Passing existing historical context to prevent redundant recall calls
    - Safe exception handling returning ReflectResult(success=False) without crashing workflows
    - Non-dogmatic sanitization and categorized thematic breakdown
    """

    def __init__(self, service: Optional[Any] = None):
        self._service = service

    def _get_service(self):
        if self._service is not None:
            svc = self._service
        else:
            svc = get_hindsight_service()
        if not svc.is_connected:
            try:
                svc.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize Hindsight service: {e}")
                raise RuntimeError(f"Hindsight service connection unavailable: {e}") from e
        return svc

    def reflect(
        self,
        query: str,
        bank_id: str = "searchmind-demo",
        context: Optional[str] = None,
    ) -> ReflectResult:
        """Execute real Hindsight reflection query."""
        service = self._get_service()
        logger.info(f"HindsightReflectAdapter: reflecting on bank '{bank_id}' with query: '{query[:80]}...'")
        t0 = time.time()
        try:
            resp = service.reflect(
                bank_id=bank_id,
                query=query,
                context=context,
                budget="low",
                include_facts=False,
            )
            latency = round(time.time() - t0, 3)
            raw_text = (
                getattr(resp, "text", None)
                or getattr(resp, "response", None)
                or str(resp)
            )
            sanitized_text = sanitize_non_dogmatic_reflection(raw_text)
            sections = parse_reflection_sections(sanitized_text)

            usage_info = None
            if hasattr(resp, "usage") and resp.usage is not None:
                usage_info = (
                    resp.usage.to_dict()
                    if hasattr(resp.usage, "to_dict")
                    else dict(resp.usage)
                )

            logger.info(f"  -> Successfully reflected on '{bank_id}' in {latency}s")
            return ReflectResult(
                source="hindsight",
                memory_bank=bank_id,
                query=query,
                synthesis_text=sanitized_text,
                patterns=sections.get("patterns", []),
                supporting_evidence=sections.get("supporting_evidence", []),
                conflicting_evidence=sections.get("conflicting_evidence", []),
                caveats=sections.get("caveats", []),
                contextual_factors=sections.get("contextual_factors", []),
                latency_seconds=latency,
                token_usage=usage_info,
                success=True,
                error=None,
                timestamp=utc_now(),
            )
        except Exception as exc:
            latency = round(time.time() - t0, 3)
            logger.warning(f"Hindsight reflection encountered exception or quota block: {exc}")
            return ReflectResult(
                source="hindsight",
                memory_bank=bank_id,
                query=query,
                synthesis_text="",
                latency_seconds=latency,
                token_usage=None,
                success=False,
                error=str(exc),
                timestamp=utc_now(),
            )


class InMemoryReflectAdapter(BaseReflectAdapter):
    """
    Deterministic in-memory reflect adapter for zero-token testing.

    Simulates successful reflection, conflicting evidence, caveats, or provider failures
    strictly in local Python memory.
    """

    def __init__(
        self,
        default_synthesis: Optional[str] = None,
        patterns: Optional[List[str]] = None,
        supporting_evidence: Optional[List[str]] = None,
        conflicting_evidence: Optional[List[str]] = None,
        caveats: Optional[List[str]] = None,
        contextual_factors: Optional[List[str]] = None,
        should_fail: bool = False,
        failure_error: str = "Simulated Reflect quota exceeded / rate limit",
    ):
        self.default_synthesis = default_synthesis
        self.patterns = patterns
        self.supporting_evidence = supporting_evidence
        self.conflicting_evidence = conflicting_evidence
        self.caveats = caveats
        self.contextual_factors = contextual_factors
        self.should_fail = should_fail
        self.failure_error = failure_error
        self.calls_count = 0
        self.last_query: Optional[str] = None
        self.last_context: Optional[str] = None

    def reflect(
        self,
        query: str,
        bank_id: str = "searchmind-demo",
        context: Optional[str] = None,
    ) -> ReflectResult:
        """Return deterministic simulated reflection result."""
        self.calls_count += 1
        self.last_query = query
        self.last_context = context

        if self.should_fail:
            return ReflectResult(
                source="fixture",
                memory_bank=bank_id,
                query=query,
                synthesis_text="",
                latency_seconds=0.01,
                token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                success=False,
                error=self.failure_error,
                timestamp=utc_now(),
            )

        synth = self.default_synthesis or (
            "Within the retrieved SearchMind experiment history, title tag optimization showed positive "
            "results in comparable commercial product pages when keyword-intent was aligned. However, "
            "promotional modifiers showed conflicting or negative results. Results are contextual and "
            "not a universal proof."
        )
        sanitized = sanitize_non_dogmatic_reflection(synth)

        return ReflectResult(
            source="fixture",
            memory_bank=bank_id,
            query=query,
            synthesis_text=sanitized,
            patterns=self.patterns or [
                "Keyword-intent alignment correlates with positive CTR lift on commercial pages.",
                "Promotional modifiers ('best discount') correlate with decreased CTR in past trials.",
            ],
            supporting_evidence=self.supporting_evidence or [
                "Historical experiments on product pages demonstrated up to +35% CTR improvement."
            ],
            conflicting_evidence=self.conflicting_evidence or [
                "Two past tests with promotional discount modifiers saw -12% to -18% CTR declines."
            ],
            caveats=self.caveats or [
                "Seasonal fluctuations and algorithm updates coincided with some test periods."
            ],
            contextual_factors=self.contextual_factors or [
                "Commercial search intent and product page template specificity."
            ],
            latency_seconds=0.01,
            token_usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            success=True,
            error=None,
            timestamp=utc_now(),
        )
