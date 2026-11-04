"""
knowledge_base.py – Feature 5
Loads and provides access to the educational medical glossary.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .config import KNOWLEDGE_BASE_PATH

logger = logging.getLogger(__name__)


class KnowledgeBaseError(Exception):
    """Raised when the knowledge base cannot be loaded or queried."""


class MedicalKnowledgeBase:
    """
    Loads the educational medical glossary and exposes helper methods
    so Member 2 can easily convert entries into embeddings.

    Parameters
    ----------
    glossary_path : str | Path | None
        Path to ``medical_glossary.json``.  Defaults to the value in config.
    """

    def __init__(self, glossary_path: str | Path | None = None) -> None:
        path = Path(glossary_path) if glossary_path else Path(KNOWLEDGE_BASE_PATH)
        self._entries: list[dict[str, Any]] = self._load(path)

    # ── Loading ─────────────────────────────────────────────────────────────

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise KnowledgeBaseError(
                f"Medical glossary not found at: {path}"
            )
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise KnowledgeBaseError(
                "Medical glossary contains invalid JSON."
            ) from exc

        if not isinstance(data, list):
            raise KnowledgeBaseError(
                "Medical glossary must be a JSON array of term objects."
            )
        return data

    # ── Public API ──────────────────────────────────────────────────────────

    def get_all_entries(self) -> list[dict[str, Any]]:
        """Return every entry in the glossary."""
        return list(self._entries)

    def get_entry(self, term: str) -> dict[str, Any] | None:
        """
        Return the glossary entry for a term (case-insensitive).

        Parameters
        ----------
        term : str
            Medical term to look up.

        Returns
        -------
        dict | None
            Matching entry, or ``None`` if not found.
        """
        term_lower = term.strip().lower()
        for entry in self._entries:
            if entry.get("term", "").lower() == term_lower:
                return entry
        return None

    def get_chunks_for_embedding(self) -> list[dict[str, Any]]:
        """
        Return glossary entries formatted as chunks compatible with the
        Phase 1 output contract so Member 2 can embed them directly.

        Returns
        -------
        list[dict]
            Each item has ``"text"`` and ``"metadata"`` keys.
        """
        chunks: list[dict[str, Any]] = []
        for idx, entry in enumerate(self._entries, start=1):
            term = entry.get("term", "")
            explanation = entry.get("simple_explanation", "")
            text = f"{term}: {explanation}".strip()

            chunks.append(
                {
                    "text": text,
                    "metadata": {
                        "source": "medical_glossary",
                        "term": term,
                        "category": entry.get("category", ""),
                        "chunk_id": f"glossary_{idx:03d}",
                        "document_type": "medical_glossary",
                    },
                }
            )
        return chunks
