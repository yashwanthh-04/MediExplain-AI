"""
chunking.py – Feature 4
Splits cleaned medical text into overlapping chunks suitable for embedding.
"""

from __future__ import annotations

import re
from typing import Any

from .config import (
    CHUNK_ID_PREFIX,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DOCUMENT_TYPE,
)


class TextChunker:
    """
    Splits cleaned medical text into overlapping, semantically meaningful chunks.

    Each chunk preserves:
    - The source filename.
    - The page number where the chunk starts.
    - A zero-padded unique chunk ID.
    - The document type label used by the RAG pipeline.

    Splitting strategy
    ------------------
    The text is first split at paragraph/section boundaries (double newlines,
    then single newlines, then sentence endings) so that related values – test
    name, result, unit, reference range – stay together wherever possible.
    If a natural segment still exceeds ``chunk_size`` it is split by character
    count with ``overlap`` characters of context carried forward.

    Parameters
    ----------
    chunk_size : int
        Target maximum number of characters per chunk.
    chunk_overlap : int
        Number of characters from the end of one chunk repeated at the start
        of the next, providing context continuity.
    """

    # Ordered list of boundary patterns (most preferred first)
    _BOUNDARIES: list[str] = [
        r"\n\n+",   # paragraph break
        r"\n",      # line break
        r"(?<=[.!?])\s+",  # sentence end
        r"\s+",     # any whitespace
    ]

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be zero or a positive integer.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ── Public API ──────────────────────────────────────────────────────────

    def chunk_pages(
        self,
        pages: list[dict[str, Any]],
        source: str,
    ) -> list[dict[str, Any]]:
        """
        Chunk all pages of an extracted document.

        Parameters
        ----------
        pages : list[dict]
            Page dicts with at least ``"page_number"`` and ``"text"`` keys.
        source : str
            Original filename – stored in every chunk's metadata.

        Returns
        -------
        list[dict]
            List of chunk dicts, each with ``"text"`` and ``"metadata"`` keys.
            Chunks from pages with no text (``ocr_required``) are skipped.
        """
        all_chunks: list[dict[str, Any]] = []
        global_index: int = 0

        for page in pages:
            text: str = page.get("text", "").strip()
            page_number: int = page.get("page_number", 0)

            if not text:
                continue

            raw_segments = self._split_text(text)
            page_chunks = self._merge_segments(raw_segments)

            for chunk_text in page_chunks:
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue

                global_index += 1
                chunk_id = f"{CHUNK_ID_PREFIX}_{global_index:03d}"

                all_chunks.append(
                    {
                        "text": chunk_text,
                        "metadata": {
                            "source": source,
                            "page": page_number,
                            "chunk_id": chunk_id,
                            "document_type": DOCUMENT_TYPE,
                        },
                    }
                )

        return all_chunks

    # ── Internal helpers ────────────────────────────────────────────────────

    def _split_text(self, text: str) -> list[str]:
        """
        Recursively split text at natural boundaries into segments no larger
        than ``chunk_size``.
        """
        if len(text) <= self.chunk_size:
            return [text]

        for boundary in self._BOUNDARIES:
            parts = re.split(boundary, text)
            if len(parts) > 1:
                # Recursively split any part that is still too large
                result: list[str] = []
                for part in parts:
                    result.extend(self._split_text(part))
                return result

        # Absolute fallback: hard character split
        return [
            text[i : i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size)
        ]

    def _merge_segments(self, segments: list[str]) -> list[str]:
        """
        Merge small segments up to ``chunk_size`` and apply ``chunk_overlap``.
        """
        chunks: list[str] = []
        current = ""

        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue

            candidate = (current + " " + seg).strip() if current else seg

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # Start new chunk with overlap from previous
                if chunks and self.chunk_overlap > 0:
                    overlap_text = chunks[-1][-self.chunk_overlap :]
                    current = (overlap_text + " " + seg).strip()
                else:
                    current = seg

        if current:
            chunks.append(current)

        return chunks
