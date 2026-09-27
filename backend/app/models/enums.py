"""Domain enums and controlled vocabularies for SearchMind."""

from enum import Enum


class SearchIntent(str, Enum):
    """Search intent classification for queries and target pages."""

    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class ObservationSeverity(str, Enum):
    """Severity levels for measurable SEO signals and observations."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExperimentStatus(str, Enum):
    """Lifecycle statuses for SEO experiments."""

    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutcomeClass(str, Enum):
    """Empirical outcome classification of a completed SEO experiment."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    INCONCLUSIVE = "inconclusive"
