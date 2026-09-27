"""Base domain model configuration and serialization helpers."""

from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class BaseDomainModel(BaseModel):
    """Base class for all SearchMind SEO domain models."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore",
    )

    def to_hindsight_dict(self) -> Dict[str, Any]:
        """
        Serialize the domain model into a clean, JSON-compatible dictionary.

        Ensures HttpUrl objects are converted to strings, datetimes to ISO 8601 strings,
        and enums to their primitive values for seamless Hindsight ingestion.
        """
        return self.model_dump(mode="json")
