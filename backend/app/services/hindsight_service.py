"""Hindsight memory service layer.

Encapsulates all interaction with the Vectorize Hindsight memory engine,
supporting lifecycle management, Retain, Recall, and Reflect operations.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from hindsight import HindsightEmbedded
from hindsight_client_api.models.recall_response import RecallResponse
from hindsight_client_api.models.reflect_response import ReflectResponse
from hindsight_client_api.models.retain_response import RetainResponse

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class HindsightService:
    """Service layer managing the Hindsight embedded daemon and memory operations."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._embedded: Optional[HindsightEmbedded] = None
        self._initialized: bool = False
        self._last_error: Optional[str] = None

    def initialize(self) -> bool:
        """
        Initialize the Hindsight embedded runtime.

        Sets up the daemon with configured LLM and database settings.
        Returns True if initialization succeeded, False otherwise.
        """
        if self.settings.SEARCHMIND_DEMO_MODE:
            logger.info("Hindsight initialization skipped: SEARCHMIND_DEMO_MODE is enabled.")
            self._last_error = "Demo mode active (live Hindsight disabled)"
            return False

        if not self.settings.is_llm_configured:
            logger.warning(
                "Hindsight initialization skipped: LLM API key not configured. "
                "Set HINDSIGHT_API_LLM_API_KEY in .env to activate memory engine."
            )
            self._last_error = "LLM API key not configured"
            return False

        try:
            # Propagate configuration to environment variables for subprocess inheritance
            os.environ["HINDSIGHT_API_LLM_PROVIDER"] = self.settings.HINDSIGHT_API_LLM_PROVIDER
            os.environ["HINDSIGHT_API_LLM_API_KEY"] = self.settings.HINDSIGHT_API_LLM_API_KEY
            os.environ["HINDSIGHT_API_LLM_MODEL"] = self.settings.HINDSIGHT_API_LLM_MODEL
            if self.settings.HINDSIGHT_API_LLM_PROVIDER.lower() == "gemini":
                os.environ["GEMINI_API_KEY"] = self.settings.HINDSIGHT_API_LLM_API_KEY
            if self.settings.HINDSIGHT_API_LLM_BASE_URL:
                os.environ["HINDSIGHT_API_LLM_BASE_URL"] = self.settings.HINDSIGHT_API_LLM_BASE_URL
            if self.settings.HINDSIGHT_API_LLM_GROQ_SERVICE_TIER:
                os.environ["HINDSIGHT_API_LLM_GROQ_SERVICE_TIER"] = self.settings.HINDSIGHT_API_LLM_GROQ_SERVICE_TIER
            os.environ["HINDSIGHT_API_LLM_MAX_BACKOFF"] = str(self.settings.HINDSIGHT_API_LLM_MAX_BACKOFF)
            os.environ["HINDSIGHT_API_WORKER_ENABLED"] = "true" if self.settings.HINDSIGHT_API_WORKER_ENABLED else "false"
            if self.settings.HINDSIGHT_API_DATABASE_URL:
                os.environ["HINDSIGHT_API_DATABASE_URL"] = self.settings.HINDSIGHT_API_DATABASE_URL
            os.environ["HINDSIGHT_API_REFLECT_MAX_CONTEXT_TOKENS"] = str(self.settings.HINDSIGHT_API_REFLECT_MAX_CONTEXT_TOKENS)
            os.environ["HINDSIGHT_API_RECALL_MAX_TOKENS"] = str(self.settings.HINDSIGHT_API_RECALL_MAX_TOKENS)
            os.environ["HINDSIGHT_API_RECALL_CHUNKS_MAX_TOKENS"] = str(self.settings.HINDSIGHT_API_RECALL_CHUNKS_MAX_TOKENS)
            os.environ["HINDSIGHT_API_REFLECT_SOURCE_FACTS_MAX_TOKENS"] = str(self.settings.HINDSIGHT_API_REFLECT_SOURCE_FACTS_MAX_TOKENS)
            os.environ["HINDSIGHT_API_REFLECT_LLM_MAX_RETRIES"] = str(self.settings.HINDSIGHT_API_REFLECT_LLM_MAX_RETRIES)
            os.environ["HINDSIGHT_API_REFLECT_LLM_INITIAL_BACKOFF"] = str(self.settings.HINDSIGHT_API_REFLECT_LLM_INITIAL_BACKOFF)
            os.environ["HINDSIGHT_API_REFLECT_LLM_MAX_BACKOFF"] = str(self.settings.HINDSIGHT_API_REFLECT_LLM_MAX_BACKOFF)
            os.environ.pop("HINDSIGHT_API_REFLECT_MAX_COMPLETION_TOKENS", None)

            logger.info(
                f"Initializing Hindsight Embedded runtime (Profile: {self.settings.HINDSIGHT_PROFILE}, "
                f"Provider: {self.settings.HINDSIGHT_API_LLM_PROVIDER}, "
                f"Model: {self.settings.HINDSIGHT_API_LLM_MODEL})..."
            )

            self._embedded = HindsightEmbedded(
                profile=self.settings.HINDSIGHT_PROFILE,
                llm_provider=self.settings.HINDSIGHT_API_LLM_PROVIDER,
                llm_api_key=self.settings.HINDSIGHT_API_LLM_API_KEY,
                llm_model=self.settings.HINDSIGHT_API_LLM_MODEL,
                llm_base_url=self.settings.HINDSIGHT_API_LLM_BASE_URL,
                database_url=self.settings.HINDSIGHT_API_DATABASE_URL,
            )

            # Ensure the daemon starts and verify reachability
            daemon_url = self._embedded.url
            logger.info(f"Hindsight Embedded daemon successfully running at {daemon_url}")
            self._initialized = True
            self._last_error = None
            return True

        except Exception as exc:
            self._last_error = str(exc)
            logger.error(f"Failed to initialize Hindsight Embedded runtime: {exc}", exc_info=True)
            return False

    def shutdown(self) -> None:
        """Gracefully close the Hindsight runtime during application shutdown."""
        if self._embedded is not None:
            try:
                logger.info("Closing Hindsight runtime...")
                self._embedded.close(stop_daemon=False)
            except Exception as exc:
                logger.debug(f"Error while closing Hindsight runtime: {exc}")
            finally:
                self._embedded = None
                self._initialized = False

    @property
    def is_connected(self) -> bool:
        """Return True if Hindsight embedded daemon is active and responsive."""
        if not self._initialized or self._embedded is None:
            return False
        try:
            return bool(self._embedded.is_running)
        except Exception:
            return False

    @property
    def last_error(self) -> Optional[str]:
        """Return the last error message encountered during initialization, if any."""
        return self._last_error

    def get_client(self) -> HindsightEmbedded:
        """
        Return the initialized Hindsight client instance.

        Raises RuntimeError if the service has not been initialized.
        """
        if not self.is_connected or self._embedded is None:
            raise RuntimeError(
                f"Hindsight memory engine is not connected. "
                f"Status: {self._last_error or 'Not initialized'}. "
                f"Please ensure HINDSIGHT_API_LLM_API_KEY is configured."
            )
        return self._embedded

    def retain(
        self,
        bank_id: str,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        document_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        update_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> RetainResponse:
        """
        Retain an observation or experience in Hindsight persistent memory.

        Args:
            bank_id: The target memory bank identifier.
            content: The text content of the memory to retain.
            context: Optional contextual information.
            metadata: Optional key-value metadata dict.
            tags: Optional list of categorization tags.
            document_id: Optional document identifier for idempotent tracking.
            timestamp: Optional event timestamp.
            update_mode: Mode for updating existing document ('replace' or 'append').
            **kwargs: Extra parameters passed to the Hindsight client.
        """
        client = self.get_client()
        logger.info(f"Retaining memory in bank '{bank_id}': {content[:60]}...")
        return client.retain(
            bank_id=bank_id,
            content=content,
            context=context,
            metadata=metadata,
            tags=tags,
            document_id=document_id,
            timestamp=timestamp,
            update_mode=update_mode,
            **kwargs,
        )

    def recall(
        self,
        bank_id: str,
        query: str,
        types: Optional[List[str]] = None,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[List[str]] = None,
    ) -> RecallResponse:
        """
        Recall relevant historical memories from Hindsight.

        Args:
            bank_id: The target memory bank identifier.
            query: Natural language query to search for relevant memories.
            types: Optional memory types filter (e.g. ['world', 'experience']).
            max_tokens: Maximum token budget for returned memories.
            budget: Recall search budget ('low', 'mid', 'high').
            tags: Optional tags to filter by.
        """
        client = self.get_client()
        logger.info(f"Recalling from bank '{bank_id}' with query: '{query}'")
        return client.recall(
            bank_id=bank_id,
            query=query,
            types=types,
            max_tokens=max_tokens,
            budget=budget,
            tags=tags,
        )

    def reflect(
        self,
        bank_id: str,
        query: str,
        context: Optional[str] = None,
        budget: str = "low",
        include_facts: bool = False,
        **kwargs: Any,
    ) -> ReflectResponse:
        """
        Reflect over stored memories to synthesize insights and conclusions.

        Args:
            bank_id: The target memory bank identifier.
            query: The reasoning query or question to reflect upon.
            context: Optional additional context for reflection.
            budget: Reflection budget ('low', 'mid', 'high').
            include_facts: Whether to include supporting facts in the response.
            **kwargs: Extra parameters passed to Hindsight client.
        """
        client = self.get_client()
        logger.info(f"Reflecting on bank '{bank_id}' with query: '{query}'")
        return client.reflect(
            bank_id=bank_id,
            query=query,
            context=context,
            budget=budget,
            include_facts=include_facts,
            **kwargs,
        )


# Global service singleton instance
_hindsight_service: Optional[HindsightService] = None


def get_hindsight_service(settings: Optional[Settings] = None) -> HindsightService:
    """Return the application-wide HindsightService singleton."""
    global _hindsight_service
    if _hindsight_service is None:
        _hindsight_service = HindsightService(settings)
    elif settings is not None:
        _hindsight_service.settings = settings
    return _hindsight_service
