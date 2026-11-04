"""
Tests for document_processing.text_cleaner
Verifies that cleaning preserves medically critical content.
"""

import pytest
from document_processing.text_cleaner import TextCleaner


@pytest.fixture()
def cleaner() -> TextCleaner:
    return TextCleaner()


class TestClean:
    def test_removes_extra_blank_lines(self, cleaner):
        result = cleaner.clean("Line 1\n\n\n\nLine 2")
        assert "\n\n\n" not in result

    def test_normalizes_crlf(self, cleaner):
        result = cleaner.clean("Line 1\r\nLine 2\r\nLine 3")
        assert "\r" not in result

    def test_strips_trailing_spaces(self, cleaner):
        result = cleaner.clean("CBC REPORT   \nHaemoglobin: 10 g/dL   ")
        for line in result.splitlines():
            assert line == line.rstrip()

    def test_preserves_decimal_points(self, cleaner):
        text = "Creatinine: 0.9 mg/dL"
        assert cleaner.clean(text) == "Creatinine: 0.9 mg/dL"

    def test_preserves_negative_sign(self, cleaner):
        text = "Temperature change: -2 degrees"
        result = cleaner.clean(text)
        assert "-2" in result

    def test_preserves_percentage(self, cleaner):
        text = "Haematocrit: 38%"
        result = cleaner.clean(text)
        assert "38%" in result

    def test_preserves_units(self, cleaner):
        text = "WBC: 7000 cells/mcL"
        result = cleaner.clean(text)
        assert "cells/mcL" in result

    def test_preserves_reference_range(self, cleaner):
        text = "Reference Range: 12-16 g/dL"
        result = cleaner.clean(text)
        assert "12-16" in result
        assert "g/dL" in result

    def test_preserves_test_names(self, cleaner):
        text = "Haemoglobin: 10 g/dL Reference Range: 12-16 g/dL"
        result = cleaner.clean(text)
        assert "Haemoglobin" in result

    def test_empty_string_returns_empty(self, cleaner):
        assert cleaner.clean("") == ""

    def test_non_string_returns_empty(self, cleaner):
        assert cleaner.clean(None) == ""  # type: ignore[arg-type]

    def test_collapses_multi_spaces(self, cleaner):
        result = cleaner.clean("WBC:   7000  cells/mcL")
        assert "  " not in result


class TestCleanPages:
    def test_clean_pages_returns_same_count(self, cleaner):
        pages = [
            {"page_number": 1, "text": "  CBC REPORT  \n\n\nHaemoglobin: 10 g/dL  ", "ocr_required": False},
            {"page_number": 2, "text": "Blood Glucose: 95 mg/dL", "ocr_required": False},
        ]
        cleaned = cleaner.clean_pages(pages)
        assert len(cleaned) == 2

    def test_clean_pages_preserves_page_number(self, cleaner):
        pages = [{"page_number": 3, "text": "Some text", "ocr_required": False}]
        cleaned = cleaner.clean_pages(pages)
        assert cleaned[0]["page_number"] == 3

    def test_clean_pages_cleans_text(self, cleaner):
        pages = [{"page_number": 1, "text": "WBC:   7000   cells/mcL   ", "ocr_required": False}]
        cleaned = cleaner.clean_pages(pages)
        assert "  " not in cleaned[0]["text"]
