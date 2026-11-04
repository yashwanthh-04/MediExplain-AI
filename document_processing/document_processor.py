"""
document_processor.py – Feature 6 & Integration Contract
Main entry point for Phase 1.  Orchestrates validation, extraction,
cleaning and chunking into a single structured output consumed by Member 2.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .chunking import TextChunker
from .config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from .pdf_extractor import PDFExtractionError, PDFExtractor, PDFValidationError
from .text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

# Shared singletons – instantiated once and reused across calls.
_extractor = PDFExtractor()
_cleaner = TextCleaner()


# ── Primary public function ─────────────────────────────────────────────────


def process_medical_pdf(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict[str, Any]:
    """
    Full Phase 1 pipeline: validate → extract → clean → chunk.

    This is the primary integration point for Member 2 (embeddings & FAISS).

    Parameters
    ----------
    file_path : str | Path
        Absolute or relative path to the PDF medical report.
    chunk_size : int
        Maximum characters per chunk (default from config).
    chunk_overlap : int
        Characters of overlap between consecutive chunks (default from config).

    Returns
    -------
    dict
        ``{
            "filename": str,
            "total_pages": int,
            "total_chunks": int,
            "chunks": [
                {
                    "text": str,
                    "metadata": {
                        "source": str,
                        "page": int,
                        "chunk_id": str,   # e.g. "chunk_001"
                        "document_type": "medical_report"
                    }
                },
                ...
            ]
        }``

    Raises
    ------
    PDFValidationError
        If the file fails any validation check.
    PDFExtractionError
        If text extraction fails.
    ValueError
        If chunking parameters are invalid.

    Notes
    -----
    When a chunk is formed by merging content across page boundaries the
    ``"page"`` metadata field records the page on which the chunk's text
    begins.  Callers that need fine-grained page attribution should use the
    page-level extraction result directly.
    """
    path = Path(file_path)
    logger.info("Processing medical PDF: %s", path.name)

    # 1. Extract
    raw_result = _extractor.extract(path)

    # 2. Clean
    cleaned_pages = _cleaner.clean_pages(raw_result["pages"])

    # 3. Chunk
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk_pages(cleaned_pages, source=raw_result["filename"])

    result: dict[str, Any] = {
        "filename": raw_result["filename"],
        "total_pages": raw_result["total_pages"],
        "total_chunks": len(chunks),
        "chunks": chunks,
    }

    logger.info(
        "Finished processing '%s': %d page(s), %d chunk(s).",
        path.name,
        result["total_pages"],
        result["total_chunks"],
    )
    return result


# ── Integration helper (Integration Contract) ───────────────────────────────


def get_document_chunks(processed_document: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract the list of chunks from a processed document dictionary.

    This helper is part of the agreed integration contract with Member 2.
    It provides a stable, typed interface so that Member 2's embedding module
    does not need to know the internal structure of the full result dict.

    Parameters
    ----------
    processed_document : dict
        The dictionary returned by :func:`process_medical_pdf`.

    Returns
    -------
    list[dict]
        List of chunk dicts, each guaranteed to have ``"text"`` (str) and
        ``"metadata"`` (dict) keys.

    Raises
    ------
    ValueError
        If ``processed_document`` is missing the ``"chunks"`` key or is not
        a dict.
    """
    if not isinstance(processed_document, dict):
        raise ValueError("processed_document must be a dictionary.")
    if "chunks" not in processed_document:
        raise ValueError(
            "processed_document does not contain a 'chunks' key. "
            "Ensure it was produced by process_medical_pdf()."
        )
    return processed_document["chunks"]


# ── Batch helper ────────────────────────────────────────────────────────────


def process_multiple_pdfs(
    file_paths: list[str | Path],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Process multiple PDF reports and return a list of results.

    Files that fail validation or extraction are skipped; errors are logged
    without exposing patient information.

    Parameters
    ----------
    file_paths : list[str | Path]
        Paths to PDF files.
    chunk_size : int
        Chunk size forwarded to :func:`process_medical_pdf`.
    chunk_overlap : int
        Chunk overlap forwarded to :func:`process_medical_pdf`.

    Returns
    -------
    list[dict]
        One result dict per successfully processed file.
    """
    results: list[dict[str, Any]] = []
    for fp in file_paths:
        try:
            results.append(
                process_medical_pdf(fp, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            )
        except (PDFValidationError, PDFExtractionError, ValueError) as exc:
            logger.error(
                "Skipping file '%s': %s", Path(fp).name, exc
            )
    return results
