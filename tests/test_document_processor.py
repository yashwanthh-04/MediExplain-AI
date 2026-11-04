"""
Tests for document_processing.document_processor
Integration-level tests for the main Phase 1 pipeline.
"""

import pytest
from document_processing.document_processor import (
    get_document_chunks,
    process_medical_pdf,
    process_multiple_pdfs,
)
from document_processing.pdf_extractor import PDFValidationError


class TestProcessMedicalPdf:
    def test_returns_dict(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        assert isinstance(result, dict)

    def test_required_keys(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        for key in ("filename", "total_pages", "total_chunks", "chunks"):
            assert key in result

    def test_total_pages_correct(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        assert result["total_pages"] == 1

    def test_multi_page_total_pages(self, multi_page_pdf):
        result = process_medical_pdf(multi_page_pdf)
        assert result["total_pages"] == 2

    def test_chunks_is_list(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        assert isinstance(result["chunks"], list)

    def test_total_chunks_matches_list(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        assert result["total_chunks"] == len(result["chunks"])

    def test_chunk_structure(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        for chunk in result["chunks"]:
            assert "text" in chunk
            assert "metadata" in chunk
            meta = chunk["metadata"]
            assert "source" in meta
            assert "page" in meta
            assert "chunk_id" in meta
            assert "document_type" in meta

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(PDFValidationError):
            process_medical_pdf(missing_file)

    def test_invalid_format_raises(self, txt_file):
        with pytest.raises(PDFValidationError):
            process_medical_pdf(txt_file)

    def test_corrupted_pdf_raises(self, corrupted_pdf):
        with pytest.raises(PDFValidationError):
            process_medical_pdf(corrupted_pdf)

    def test_medical_values_in_chunks(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf)
        combined = " ".join(c["text"] for c in result["chunks"])
        assert "Haemoglobin" in combined or "CBC" in combined or "10" in combined

    def test_custom_chunk_size(self, single_page_pdf):
        result = process_medical_pdf(single_page_pdf, chunk_size=100, chunk_overlap=20)
        assert result["total_chunks"] >= 1


class TestGetDocumentChunks:
    def test_returns_list(self, single_page_pdf):
        doc = process_medical_pdf(single_page_pdf)
        chunks = get_document_chunks(doc)
        assert isinstance(chunks, list)

    def test_chunks_match_document(self, single_page_pdf):
        doc = process_medical_pdf(single_page_pdf)
        chunks = get_document_chunks(doc)
        assert chunks == doc["chunks"]

    def test_raises_on_non_dict(self):
        with pytest.raises(ValueError):
            get_document_chunks("not a dict")  # type: ignore[arg-type]

    def test_raises_on_missing_chunks_key(self):
        with pytest.raises(ValueError):
            get_document_chunks({"filename": "x.pdf"})


class TestProcessMultiplePdfs:
    def test_processes_multiple(self, single_page_pdf, multi_page_pdf):
        results = process_multiple_pdfs([single_page_pdf, multi_page_pdf])
        assert len(results) == 2

    def test_skips_invalid_file(self, single_page_pdf, missing_file):
        results = process_multiple_pdfs([single_page_pdf, missing_file])
        assert len(results) == 1

    def test_returns_list(self, single_page_pdf):
        results = process_multiple_pdfs([single_page_pdf])
        assert isinstance(results, list)
