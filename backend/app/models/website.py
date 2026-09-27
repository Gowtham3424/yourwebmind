"""Website fact domain model representing factual page-level SEO state."""

from datetime import datetime
from typing import List, Optional
from pydantic import Field, HttpUrl, field_validator

from app.models.base import BaseDomainModel, utc_now
from app.models.enums import SearchIntent


class WebsiteFact(BaseDomainModel):
    """
    Factual snapshot of a website page's SEO attributes and technical characteristics.

    Used by SearchMind to store objective facts about target URLs into Hindsight memory.
    """

    project_id: str = Field(..., description="Unique identifier for the project or site")
    url: HttpUrl = Field(..., description="Target webpage URL (must be valid HTTP/HTTPS)")
    page_type: str = Field(default="page", description="Classification of page (e.g., product, blog, landing)")
    title: str = Field(..., description="Current title tag content")
    meta_description: Optional[str] = Field(default=None, description="Current meta description text")
    primary_keyword: Optional[str] = Field(default=None, description="Main target keyword for this page")
    secondary_keywords: List[str] = Field(default_factory=list, description="Supporting keywords or topics")
    search_intent: Optional[SearchIntent] = Field(default=None, description="Detected or intended search intent")
    word_count: int = Field(default=0, ge=0, description="Word count of the main body content (cannot be negative)")
    canonical_url: Optional[HttpUrl] = Field(default=None, description="Declared canonical URL if specified")
    indexable: bool = Field(default=True, description="Whether the page is indexable (robots / meta-robots)")
    status_code: int = Field(default=200, ge=100, le=599, description="HTTP response status code (100-599)")
    observed_at: datetime = Field(default_factory=utc_now, description="Timestamp when this fact state was recorded")

    @field_validator("project_id", "title")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:
        """Ensure critical string identifiers are not empty or blank."""
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"Field '{info.field_name}' cannot be empty or blank")
        return stripped
