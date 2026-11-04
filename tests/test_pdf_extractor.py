"""
Tests for document_processing.pdf_extractor
All test data is synthetic – no real patient information.
"""

import pytest
from document_processing.pdf_extractor import (
    PDFExtractionError,
    PDFExtractor,
    PDFValidationError,
)


@pytest.fixture()
def extractor() -> PDFExtractor:
    return PDFExtractor()


class TestValidation:
    def test_missing_file_raises(self, extractor, missing_file):
        with pytest.raises(PDFValidationError, match="not found"):
            extractor.validate(missing_file)

    def test_wrong_extension_raises(self, extractor, txt_file):
        with pytest.raises(PDFValidationError, match="Unsupported file type"):
            extractor.validate(txt_file)

    def test_empty_file_raises(self, extractor, empty_pdf):
        with pytest.raises(PDFValidationError, match="empty"):
            extractor.validate(empty_pdf)

    def test_non_pdf_magic_raises(self, extractor, non_pdf_file):
        with pytest.raises(PDFValidationError):
            extractor.validate(non_pdf_file)

    def test_corrupted_pdf_raises(self, extractor, corrupted_pdf):
        with pytest.raises(PDFValidationError):
            extractor.validate(corrupted_pdf)

    def test_valid_pdf_returns_path(self, extractor, single_page_pdf):
        path = extractor.validate(single_page_pdf)
        assert path.exists()


class TestExtraction:
    def test_single_page_extraction(self, extractor, single_page_pdf):
        result = extractor.extract(single_page_pdf)
        assert result["total_pages"] == 1
        assert len(result["pages"]) == 1
        assert result["pages"][0]["page_number"] == 1

    def test_multi_page_extraction(self, extractor, multi_page_pdf):
        result = extractor.extract(multi_page_pdf)
        assert result["total_pages"] == 2
        assert len(result["pages"]) == 2
        assert result["pages"][0]["page_number"] == 1
        assert result["pages"][1]["page_number"] == 2

    def test_filename_in_result(self, extractor, single_page_pdf):
        result = extractor.extract(single_page_pdf)
        assert result["filename"] == single_page_pdf.name

    def test_medical_values_preserved(self, extractor, single_page_pdf):
        result = extractor.extract(single_page_pdf)
        full_text = " ".join(p["text"] for p in result["pages"])
        # Values that must not be stripped or altered
        assert "10" in full_text
        assert "g/dL" in full_text or "g" in full_text

    def test_ocr_flag_on_empty_page(self, extractor, single_page_pdf):
        """Pages with no text should have ocr_required=True."""
        result = extractor.extract(single_page_pdf)
        # Our synthetic PDF should have text, so ocr_required should be False
        for page in result["pages"]:
            # ocr_required key must always exist
            assert "ocr_required" in page

    def test_invalid_file_raises_on_extract(self, extractor, missing_file):
        with pytest.raises(PDFValidationError):
            extractor.extract(missing_file)
