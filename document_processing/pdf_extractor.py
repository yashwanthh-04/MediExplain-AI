"""
pdf_extractor.py – Feature 1 & 2
Handles PDF validation and text extraction for MediExplain AI Phase 1.
"""

import logging
from pathlib import Path
from typing import Any

import pypdf
from pypdf.errors import PdfReadError

from .config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    PDF_MAGIC_BYTES,
)

logger = logging.getLogger(__name__)


class PDFValidationError(Exception):
    """Raised when a PDF file fails validation checks."""


class PDFExtractionError(Exception):
    """Raised when text extraction from a PDF fails."""


class PDFExtractor:
    """
    Validates and extracts text from medical PDF reports.

    Usage
    -----
    extractor = PDFExtractor()
    result = extractor.extract("path/to/report.pdf")
    """

    # ── Validation ──────────────────────────────────────────────────────────

    def validate(self, file_path: str | Path) -> Path:
        """
        Validate a PDF file before extraction.

        Checks performed:
        - File exists on disk.
        - Extension is .pdf.
        - File size is within the configured limit.
        - File starts with the PDF magic bytes (%PDF).
        - File can be opened by pypdf (catches corrupted / password-protected files).

        Parameters
        ----------
        file_path : str | Path
            Path to the PDF file.

        Returns
        -------
        Path
            Resolved Path object if all checks pass.

        Raises
        ------
        PDFValidationError
            On any validation failure with a descriptive (non-sensitive) message.
        """
        path = Path(file_path).resolve()

        # 1. Existence
        if not path.exists():
            raise PDFValidationError(f"File not found: {path.name}")

        # 2. Is a file (not a directory)
        if not path.is_file():
            raise PDFValidationError(f"Path does not point to a file: {path.name}")

        # 3. Extension check
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise PDFValidationError(
                f"Unsupported file type '{path.suffix}'. Only PDF files are accepted."
            )

        # 4. File size
        size = path.stat().st_size
        if size == 0:
            raise PDFValidationError("The file is empty (0 bytes).")
        if size > MAX_FILE_SIZE_BYTES:
            raise PDFValidationError(
                f"File exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB."
            )

        # 5. Magic bytes – confirm it really is a PDF
        with path.open("rb") as fh:
            header = fh.read(4)
        if header != PDF_MAGIC_BYTES:
            raise PDFValidationError(
                "File does not appear to be a valid PDF (invalid header)."
            )

        # 6. Structural integrity via pypdf
        try:
            with path.open("rb") as fh:
                reader = pypdf.PdfReader(fh)
                if reader.is_encrypted:
                    raise PDFValidationError(
                        "Password-protected PDFs are not supported."
                    )
                # Accessing pages triggers structural parsing
                _ = len(reader.pages)
        except PdfReadError as exc:
            raise PDFValidationError(
                f"PDF appears to be corrupted and cannot be read: {path.name}"
            ) from exc

        return path

    # ── Extraction ──────────────────────────────────────────────────────────

    def extract(self, file_path: str | Path) -> dict[str, Any]:
        """
        Validate and extract text from every page of a PDF.

        Text from scanned (image-only) pages cannot be extracted; those pages
        are flagged with ``"ocr_required": True`` so downstream consumers can
        handle them appropriately.

        Parameters
        ----------
        file_path : str | Path
            Path to the PDF file.

        Returns
        -------
        dict
            ``{
                "filename": str,
                "total_pages": int,
                "pages": [
                    {
                        "page_number": int,   # 1-based
                        "text": str,
                        "ocr_required": bool
                    },
                    ...
                ]
            }``

        Raises
        ------
        PDFValidationError
            If the file fails any validation check.
        PDFExtractionError
            If extraction fails unexpectedly after validation.
        """
        path = self.validate(file_path)

        pages: list[dict[str, Any]] = []

        try:
            with path.open("rb") as fh:
                reader = pypdf.PdfReader(fh)
                total_pages = len(reader.pages)

                if total_pages == 0:
                    raise PDFExtractionError(
                        "The PDF contains no pages."
                    )

                for idx, page in enumerate(reader.pages, start=1):
                    try:
                        text: str = page.extract_text() or ""
                    except Exception:
                        # Extraction failed for this page; flag it
                        text = ""

                    ocr_required = len(text.strip()) == 0
                    if ocr_required:
                        logger.warning(
                            "Page %d of '%s' yielded no extractable text. "
                            "OCR may be required for scanned content.",
                            idx,
                            path.name,
                        )

                    pages.append(
                        {
                            "page_number": idx,
                            "text": text,
                            "ocr_required": ocr_required,
                        }
                    )

        except PDFExtractionError:
            raise
        except Exception as exc:
            raise PDFExtractionError(
                f"Unexpected error while extracting text from '{path.name}'."
            ) from exc

        return {
            "filename": path.name,
            "total_pages": total_pages,
            "pages": pages,
        }
