"""
Tests for document_processing.chunking
"""

import pytest
from document_processing.chunking import TextChunker


@pytest.fixture()
def chunker() -> TextChunker:
    return TextChunker(chunk_size=200, chunk_overlap=30)


SAMPLE_PAGES = [
    {
        "page_number": 1,
        "text": (
            "CBC REPORT\n\n"
            "Haemoglobin: 10 g/dL Reference Range: 12-16 g/dL\n\n"
            "WBC: 7000 cells/mcL Reference Range: 4000-11000 cells/mcL\n\n"
            "Platelets: 250000 cells/mcL Reference Range: 150000-450000 cells/mcL"
        ),
        "ocr_required": False,
    },
    {
        "page_number": 2,
        "text": (
            "METABOLIC PANEL\n\n"
            "Blood Glucose: 95 mg/dL Reference Range: 70-100 mg/dL\n\n"
            "Creatinine: 0.9 mg/dL Reference Range: 0.6-1.2 mg/dL"
        ),
        "ocr_required": False,
    },
]


class TestChunker:
    def test_chunks_produced(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        assert len(chunks) > 0

    def test_chunk_has_text_and_metadata(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        for chunk in chunks:
            assert "text" in chunk
            assert "metadata" in chunk

    def test_metadata_fields(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        for chunk in chunks:
            meta = chunk["metadata"]
            assert "source" in meta
            assert "page" in meta
            assert "chunk_id" in meta
            assert "document_type" in meta

    def test_source_in_metadata(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="my_report.pdf")
        assert all(c["metadata"]["source"] == "my_report.pdf" for c in chunks)

    def test_chunk_ids_unique(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        ids = [c["metadata"]["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunk_ids_sequential(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        for i, chunk in enumerate(chunks, start=1):
            assert chunk["metadata"]["chunk_id"] == f"chunk_{i:03d}"

    def test_no_content_loss(self, chunker):
        """All source text must appear somewhere across the chunks."""
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        combined = " ".join(c["text"] for c in chunks)
        assert "Haemoglobin" in combined
        assert "10" in combined
        assert "g/dL" in combined
        assert "Creatinine" in combined

    def test_chunk_size_respected(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        # Chunks may slightly exceed chunk_size due to overlap merge, but
        # should not be wildly over (we allow a small tolerance)
        for chunk in chunks:
            assert len(chunk["text"]) <= chunker.chunk_size + chunker.chunk_overlap + 50

    def test_empty_pages_skipped(self, chunker):
        pages = [{"page_number": 1, "text": "", "ocr_required": True}]
        chunks = chunker.chunk_pages(pages, source="empty.pdf")
        assert chunks == []

    def test_page_number_recorded(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        page_numbers = {c["metadata"]["page"] for c in chunks}
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=0)

    def test_overlap_larger_than_size_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=150)

    def test_document_type_label(self, chunker):
        chunks = chunker.chunk_pages(SAMPLE_PAGES, source="report.pdf")
        for chunk in chunks:
            assert chunk["metadata"]["document_type"] == "medical_report"
