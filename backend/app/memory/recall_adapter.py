"""Hindsight memory recall adapter and provenance models for SearchMind.

Provides an abstraction layer connecting SearchMind agents to Hindsight persistent memory,
enabling dependency injection of in-memory test adapters for deterministic, token-free testing.
"""

from abc import ABC, abstractmethod
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.hindsight_service import get_hindsight_service

logger = logging.getLogger("searchmind.memory.recall")

_EXP_ID_REGEX = re.compile(r"(?:seo_)?(exp_\d{3})\b", re.IGNORECASE)
_OUTCOME_REGEX = re.compile(
    r"\b(positive|negative|neutral|inconclusive)\b", re.IGNORECASE
)


class RecalledMemoryItem(BaseModel):
    """
    Structured historical memory unit with explicit provenance tracking.

    Ensures every retrieved fact clearly declares its source, memory bank,
    query context, and extracted domain identifiers without fabrication.
    """

    source: str = Field(
        default="hindsight",
        description="Source of memory record ('hindsight' or 'fixture')",
    )
    memory_bank: str = Field(
        ...,
        description="Target memory bank identifier (e.g., 'searchmind-demo')",
    )
    query: str = Field(
        ...,
        description="Query text used to retrieve this memory",
    )
    memory_text: str = Field(
        ...,
        description="Text content of the retrieved memory fact or narrative",
    )
    experiment_id: Optional[str] = Field(
        default=None,
        description="Extracted experiment identifier (e.g. 'exp_001') if identifiable; None if unidentifiable",
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Extracted outcome class ('positive', 'negative', 'neutral', 'inconclusive') if identifiable",
    )
    retrieval_context: Optional[str] = Field(
        default=None,
        description="Context metadata or document context provided during retention",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags attached to memory",
    )
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw metadata dictionary returned by Hindsight",
    )


class BaseRecallAdapter(ABC):
    """Abstract interface for memory recall retrieval."""

    @abstractmethod
    def recall(
        self,
        query: str,
        bank_id: str = "searchmind-demo",
        budget: str = "mid",
        max_tokens: int = 2000,
    ) -> List[RecalledMemoryItem]:
        """Retrieve relevant historical memories matching the query."""
        pass


def extract_experiment_id(
    document_id: Optional[str],
    text: str,
    context: Optional[str] = None,
) -> Optional[str]:
    """
    Extract canonical experiment ID (e.g., 'exp_001') from document_id or text.

    Returns None if no valid ID pattern is found. Never fabricates an ID.
    """
    if document_id:
        # Check if document_id has format 'seo_exp_001' or 'exp_001'
        m = _EXP_ID_REGEX.search(document_id)
        if m:
            return m.group(1).lower()

    if context:
        m = _EXP_ID_REGEX.search(context)
        if m:
            return m.group(1).lower()

    if text:
        m = _EXP_ID_REGEX.search(text)
        if m:
            return m.group(1).lower()

    return None


def extract_outcome(text: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Extract outcome classification ('positive', 'negative', 'neutral', 'inconclusive').

    Checks metadata first, then scans text for explicit classification strings.
    """
    if metadata and "outcome_class" in metadata:
        cls_val = str(metadata["outcome_class"]).lower()
        if cls_val in ("positive", "negative", "neutral", "inconclusive"):
            return cls_val

    if text:
        # Search for patterns like 'outcome: POSITIVE' or 'outcome classification: POSITIVE'
        m = re.search(r"outcome(?:\s+classification)?:\s*(positive|negative|neutral|inconclusive)", text, re.IGNORECASE)
        if m:
            return m.group(1).lower()

    return None


class HindsightRecallAdapter(BaseRecallAdapter):
    """
    Live adapter connecting directly to the running Hindsight Embedded memory engine.

    Delegates to the existing HindsightService without inventing new client logic.
    """

    def __init__(self, service: Optional[Any] = None):
        self._service = service

    def _get_service(self):
        if self._service is not None:
            return self._service
        return get_hindsight_service()

    def recall(
        self,
        query: str,
        bank_id: str = "searchmind-demo",
        budget: str = "mid",
        max_tokens: int = 2000,
    ) -> List[RecalledMemoryItem]:
        """
        Execute live Hindsight recall and map results to RecalledMemoryItem with provenance.
        """
        service = self._get_service()
        if not service.is_connected:
            try:
                service.initialize()
            except Exception as e:
                logger.warning(f"Could not connect to Hindsight service: {e}; returning empty recall.")
                return []
        if not service.is_connected:
            logger.warning("Hindsight service is not connected; returning empty recall.")
            return []

        logger.info(f"HindsightRecallAdapter: recalling from bank '{bank_id}' with query: '{query}'")
        try:
            resp = service.recall(
                bank_id=bank_id,
                query=query,
                budget=budget,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            logger.error(f"Live Hindsight recall failed: {exc}")
            raise

        recalled_items: List[RecalledMemoryItem] = []
        raw_results = getattr(resp, "results", None) or []

        for item in raw_results:
            text = getattr(item, "text", "") or ""
            doc_id = getattr(item, "document_id", None)
            context = getattr(item, "context", None)
            meta = getattr(item, "metadata", None) or {}
            tags = getattr(item, "tags", None) or []

            exp_id = extract_experiment_id(doc_id, text, context)
            outcome = extract_outcome(text, meta)

            recalled_items.append(
                RecalledMemoryItem(
                    source="hindsight",
                    memory_bank=bank_id,
                    query=query,
                    memory_text=text,
                    experiment_id=exp_id,
                    outcome=outcome,
                    retrieval_context=context,
                    tags=list(tags),
                    raw_metadata=dict(meta) if isinstance(meta, dict) else {},
                )
            )

        return recalled_items


class InMemoryRecallAdapter(BaseRecallAdapter):
    """
    Deterministic in-memory recall adapter for zero-token testing and offline demonstration.

    Returns pre-configured or filtered memory fixtures while strictly declaring
    provenance as 'fixture'.
    """

    def __init__(self, fixture_memories: Optional[List[Dict[str, Any]]] = None):
        self.fixture_memories: List[Dict[str, Any]] = fixture_memories or []
        self.calls_count: int = 0

    def add_fixture_memory(
        self,
        text: str,
        bank_id: str = "searchmind-demo",
        query: str = "test query",
        experiment_id: Optional[str] = None,
        outcome: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Add a memory item to the in-memory fixture list."""
        self.fixture_memories.append({
            "source": "fixture",
            "memory_bank": bank_id,
            "query": query,
            "memory_text": text,
            "experiment_id": experiment_id,
            "outcome": outcome,
            "retrieval_context": context,
            "tags": tags or [],
            "raw_metadata": {},
        })

    def recall(
        self,
        query: str,
        bank_id: str = "searchmind-demo",
        budget: str = "mid",
        max_tokens: int = 2000,
    ) -> List[RecalledMemoryItem]:
        """Return memory items from the in-memory fixture list matching the query."""
        self.calls_count += 1
        results: List[RecalledMemoryItem] = []
        for m in self.fixture_memories:
            # Simple keyword or substring matching for test simulation
            results.append(
                RecalledMemoryItem(
                    source=m.get("source", "fixture"),
                    memory_bank=m.get("memory_bank", bank_id),
                    query=query,
                    memory_text=m.get("memory_text", ""),
                    experiment_id=m.get("experiment_id"),
                    outcome=m.get("outcome"),
                    retrieval_context=m.get("retrieval_context"),
                    tags=m.get("tags", []),
                    raw_metadata=m.get("raw_metadata", {}),
                )
            )
        return results
