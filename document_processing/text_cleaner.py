"""
text_cleaner.py – Feature 3
Cleans extracted PDF text while preserving all medically important information.
"""

import re
from typing import Any


class TextCleaner:
    """
    Cleans raw text extracted from medical PDF reports.

    Design principle
    ----------------
    The cleaner is intentionally conservative.  Medical reports contain
    numerical values, units, reference ranges, decimal points, negative signs
    and percentages that are clinically meaningful.  Only clearly non-medical
    artefacts (excessive whitespace, repeated blank lines, non-printable
    control characters) are removed.  Medical content is NEVER altered.
    """

    # Control characters except tab (\x09) and newline (\x0a, \x0d)
    _CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    # Three or more consecutive newlines collapsed to two (one blank line)
    _EXCESS_BLANK_LINES_RE = re.compile(r"\n{3,}")

    # Trailing spaces / tabs on each line
    _TRAILING_WHITESPACE_RE = re.compile(r"[ \t]+$", re.MULTILINE)

    # Leading spaces / tabs on each line (keep indentation minimal)
    _LEADING_WHITESPACE_RE = re.compile(r"^[ \t]+", re.MULTILINE)

    # Multiple spaces / tabs compressed to a single space
    # IMPORTANT: newlines are NOT touched here so structure is kept.
    _MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")

    def clean(self, text: str) -> str:
        """
        Clean a single string of extracted text.

        Operations applied (in order):
        1. Remove non-printable control characters.
        2. Normalize Windows-style line endings (\\r\\n → \\n).
        3. Strip trailing whitespace from every line.
        4. Strip leading whitespace from every line.
        5. Collapse multiple consecutive spaces/tabs to one space.
        6. Collapse three or more consecutive blank lines to one blank line.
        7. Strip leading/trailing whitespace from the whole string.

        Parameters
        ----------
        text : str
            Raw text from PDF extraction.

        Returns
        -------
        str
            Cleaned text with medical values fully intact.
        """
        if not isinstance(text, str):
            return ""

        # 1. Remove control characters
        text = self._CONTROL_CHARS_RE.sub("", text)

        # 2. Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Trailing whitespace per line
        text = self._TRAILING_WHITESPACE_RE.sub("", text)

        # 4. Leading whitespace per line
        text = self._LEADING_WHITESPACE_RE.sub("", text)

        # 5. Multiple inline spaces → single space
        text = self._MULTI_SPACE_RE.sub(" ", text)

        # 6. Excess blank lines
        text = self._EXCESS_BLANK_LINES_RE.sub("\n\n", text)

        # 7. Global strip
        text = text.strip()

        return text

    def clean_pages(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Clean the text field of each page dictionary in-place (returns a new list).

        Parameters
        ----------
        pages : list[dict]
            Page dictionaries as returned by :class:`PDFExtractor`.

        Returns
        -------
        list[dict]
            Same structure with cleaned ``"text"`` values.
        """
        cleaned: list[dict[str, Any]] = []
        for page in pages:
            cleaned.append(
                {
                    **page,
                    "text": self.clean(page.get("text", "")),
                }
            )
        return cleaned
