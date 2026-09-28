"""Memory retrieval, retention, reflection, and provenance package for SearchMind."""

from app.memory.query_builder import build_memory_query, build_reflection_query
from app.memory.recall_adapter import (
    BaseRecallAdapter,
    HindsightRecallAdapter,
    InMemoryRecallAdapter,
    RecalledMemoryItem,
    extract_experiment_id,
    extract_outcome,
)
from app.memory.reflect_adapter import (
    BaseReflectAdapter,
    HindsightReflectAdapter,
    InMemoryReflectAdapter,
    ReflectResult,
    parse_reflection_sections,
    sanitize_non_dogmatic_reflection,
)
from app.memory.retain_adapter import (
    BaseRetainAdapter,
    HindsightRetainAdapter,
    InMemoryRetainAdapter,
    RetainResult,
)

__all__ = [
    "BaseRecallAdapter",
    "HindsightRecallAdapter",
    "InMemoryRecallAdapter",
    "RecalledMemoryItem",
    "extract_experiment_id",
    "extract_outcome",
    "build_memory_query",
    "build_reflection_query",
    "BaseReflectAdapter",
    "HindsightReflectAdapter",
    "InMemoryReflectAdapter",
    "ReflectResult",
    "parse_reflection_sections",
    "sanitize_non_dogmatic_reflection",
    "BaseRetainAdapter",
    "HindsightRetainAdapter",
    "InMemoryRetainAdapter",
    "RetainResult",
]
