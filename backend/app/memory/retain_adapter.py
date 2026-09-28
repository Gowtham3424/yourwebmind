"""Hindsight memory retain adapter and outcome persistence models for SearchMind.

Connects the Experiment Execution Service to persistent Hindsight memory,
providing structured results and dependency-injected test adapters.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import time
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.models.base import utc_now
from app.services.hindsight_service import get_hindsight_service

logger = logging.getLogger("searchmind.memory.retain")


class RetainResult(BaseModel):
    """
    Structured outcome of a memory retain operation.

    Declares explicit provenance, target bank, duration, and runtime identifiers.
    """

    source: str = Field(
        default="hindsight",
        description="Origin of retain operation ('hindsight' or 'fixture')",
    )
    memory_bank: str = Field(..., description="Target Hindsight memory bank")
    experiment_id: str = Field(..., description="Experiment identifier retained")
    retained: bool = Field(default=True, description="Whether retain succeeded")
    document_id: Optional[str] = Field(default=None, description="Hindsight document identifier")
    latency_seconds: float = Field(default=0.0, description="Retain operation latency in seconds")
    items_count: int = Field(default=1, description="Number of items retained")
    token_usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage details if exposed by runtime")
    timestamp: datetime = Field(default_factory=utc_now, description="Timestamp of retain execution")


class BaseRetainAdapter(ABC):
    """Abstract interface for retaining experiment lessons into memory."""

    @abstractmethod
    def retain_experiment_outcome(
        self,
        payload: Dict[str, Any],
        bank_id: str = "searchmind-demo",
    ) -> RetainResult:
        """Persist structured memory payload into target memory bank."""
        pass


class HindsightRetainAdapter(BaseRetainAdapter):
    """
    Live adapter delegating to HindsightService for persistent memory retention.

    Enforces:
    - Automatic connection verification and initialization
    - Idempotent document replacement (update_mode='replace')
    - Explicit provenance and latency tracking
    """

    def __init__(self, service: Optional[Any] = None):
        self._service = service
        self.retained_doc_ids: Set[str] = set()

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

    def retain_experiment_outcome(
        self,
        payload: Dict[str, Any],
        bank_id: str = "searchmind-demo",
    ) -> RetainResult:
        """Execute real Hindsight retain operation using Prompt 03 verified schema."""
        service = self._get_service()
        doc_id = payload.get("document_id")
        exp_id = payload.get("metadata", {}).get("experiment_id") or doc_id or "unknown"

        logger.info(f"HindsightRetainAdapter: retaining document '{doc_id}' into bank '{bank_id}'...")
        t0 = time.time()
        try:
            resp = service.retain(
                bank_id=bank_id,
                content=payload["content"],
                context=payload.get("context"),
                metadata=payload.get("metadata"),
                tags=payload.get("tags"),
                document_id=doc_id,
                timestamp=payload.get("timestamp"),
                update_mode=payload.get("update_mode", "replace"),
            )
            latency = round(time.time() - t0, 3)
            logger.info(f"  -> Successfully retained '{doc_id}' in {latency}s")
            if doc_id:
                self.retained_doc_ids.add(doc_id)

            usage_info = None
            if hasattr(resp, "usage") and resp.usage is not None:
                usage_info = resp.usage.to_dict() if hasattr(resp.usage, "to_dict") else dict(resp.usage)

            items_cnt = getattr(resp, "items_count", 1) or 1

            return RetainResult(
                source="hindsight",
                memory_bank=bank_id,
                experiment_id=exp_id,
                retained=True,
                document_id=doc_id,
                latency_seconds=latency,
                items_count=items_cnt,
                token_usage=usage_info,
                timestamp=utc_now(),
            )
        except Exception as exc:
            logger.error(f"Hindsight retain failed for '{doc_id}': {exc}")
            raise


class InMemoryRetainAdapter(BaseRetainAdapter):
    """
    Deterministic in-memory retain adapter for zero-token testing.

    Stores retain payloads locally in memory and enforces duplicate protection.
    """

    def __init__(self):
        self.retained_payloads: List[Dict[str, Any]] = []
        self.retained_doc_ids: Set[str] = set()

    def retain_experiment_outcome(
        self,
        payload: Dict[str, Any],
        bank_id: str = "searchmind-demo",
    ) -> RetainResult:
        """Store payload in memory with duplicate protection."""
        doc_id = payload.get("document_id")
        exp_id = payload.get("metadata", {}).get("experiment_id") or doc_id or "unknown"

        # Duplicate protection (replace if existing)
        if doc_id and doc_id in self.retained_doc_ids:
            # Replace existing payload
            self.retained_payloads = [p for p in self.retained_payloads if p.get("document_id") != doc_id]

        self.retained_payloads.append(dict(payload))
        if doc_id:
            self.retained_doc_ids.add(doc_id)

        return RetainResult(
            source="fixture",
            memory_bank=bank_id,
            experiment_id=exp_id,
            retained=True,
            document_id=doc_id,
            latency_seconds=0.001,
            items_count=1,
            token_usage=None,
            timestamp=utc_now(),
        )
