"""
conftest.py – Shared pytest fixtures for MediExplain AI Phase 1 tests.

All test data is synthetic and contains no real patient information.
"""

import io
from pathlib import Path

import pytest


# ── Helpers ─────────────────────────────────────────────────────────────────

def _build_raw_pdf(pages_text: list[str]) -> bytes:
    """
    Build a minimal but valid PDF from scratch using raw PDF syntax.
    Embeds text directly into the content stream with a standard Type1 font
    (Helvetica) so pypdf can extract it reliably without needing an embedded
    font program.
    """
    objects: list[bytes] = []  # object bodies, 1-indexed
    offsets: list[int] = []

    def add_obj(body: bytes) -> int:
        """Append an indirect object body and return its 1-based index."""
        objects.append(body)
        return len(objects)

    # Object 1 – catalog (filled in after we know pages obj id)
    # Object 2 – pages dict (filled in after page obj ids are known)
    # Reserve slots
    add_obj(b"")  # 1: catalog placeholder
    add_obj(b"")  # 2: pages placeholder

    page_obj_ids: list[int] = []
    content_obj_ids: list[int] = []

    for text in pages_text:
        # Escape parentheses and backslashes for the PDF string literal
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_data = (
            "BT\n"
            "/F1 12 Tf\n"
            "50 700 Td\n"
            f"({safe}) Tj\n"
            "ET\n"
        ).encode("latin-1")

        # Content stream object
        content_body = (
            b"<<\n"
            b"/Length " + str(len(stream_data)).encode() + b"\n"
            b">>\n"
            b"stream\n" +
            stream_data +
            b"\nendstream"
        )
        cid = add_obj(content_body)
        content_obj_ids.append(cid)

        # Font resource object
        font_body = (
            b"<<\n"
            b"/Type /Font\n"
            b"/Subtype /Type1\n"
            b"/BaseFont /Helvetica\n"
            b"/Encoding /WinAnsiEncoding\n"
            b">>"
        )
        fid = add_obj(font_body)

        # Page object
        page_body = (
            f"<<\n"
            f"/Type /Page\n"
            f"/Parent 2 0 R\n"
            f"/MediaBox [0 0 612 792]\n"
            f"/Contents {cid} 0 R\n"
            f"/Resources << /Font << /F1 {fid} 0 R >> >>\n"
            f">>"
        ).encode()
        pid = add_obj(page_body)
        page_obj_ids.append(pid)

    # Fill placeholder: pages dict
    kids = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    pages_body = (
        f"<<\n"
        f"/Type /Pages\n"
        f"/Kids [{kids}]\n"
        f"/Count {len(page_obj_ids)}\n"
        f">>"
    ).encode()
    objects[1] = pages_body  # index 1 = object 2

    # Fill placeholder: catalog
    catalog_body = b"<<\n/Type /Catalog\n/Pages 2 0 R\n>>"
    objects[0] = catalog_body  # index 0 = object 1

    # Serialise
    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")

    for i, body in enumerate(objects, start=1):
        offsets.append(buf.tell())
        buf.write(f"{i} 0 obj\n".encode())
        buf.write(body)
        buf.write(b"\nendobj\n")

    xref_offset = buf.tell()
    n = len(objects)
    buf.write(b"xref\n")
    buf.write(f"0 {n + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for off in offsets:
        buf.write(f"{off:010d} 00000 n \n".encode())

    buf.write(b"trailer\n")
    buf.write(f"<<\n/Size {n + 1}\n/Root 1 0 R\n>>\n".encode())
    buf.write(b"startxref\n")
    buf.write(f"{xref_offset}\n".encode())
    buf.write(b"%%EOF\n")

    return buf.getvalue()


def _write_pdf(tmp_path: Path, name: str, pages_text: list[str]) -> Path:
    dest = tmp_path / name
    dest.write_bytes(_build_raw_pdf(pages_text))
    return dest


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def single_page_pdf(tmp_path: Path) -> Path:
    """A single-page PDF with a synthetic CBC report."""
    text = (
        "CBC REPORT "
        "Haemoglobin: 10 g/dL Reference Range: 12-16 g/dL "
        "WBC: 7000 cells/mcL Reference Range: 4000-11000 cells/mcL "
        "Platelets: 250000 cells/mcL Reference Range: 150000-450000 cells/mcL"
    )
    return _write_pdf(tmp_path, "single_page_report.pdf", [text])


@pytest.fixture()
def multi_page_pdf(tmp_path: Path) -> Path:
    """A two-page PDF with synthetic medical content."""
    page1 = (
        "PATIENT REPORT PAGE 1 "
        "Haemoglobin: 13.5 g/dL Reference Range: 12-16 g/dL "
        "RBC: 4.5 million cells/mcL Reference Range: 4.2-5.4 million cells/mcL"
    )
    page2 = (
        "PATIENT REPORT PAGE 2 "
        "Blood Glucose: 95 mg/dL Reference Range: 70-100 mg/dL "
        "Creatinine: 0.9 mg/dL Reference Range: 0.6-1.2 mg/dL"
    )
    return _write_pdf(tmp_path, "multi_page_report.pdf", [page1, page2])


@pytest.fixture()
def non_pdf_file(tmp_path: Path) -> Path:
    """A plain text file disguised with a .pdf extension."""
    p = tmp_path / "not_a_pdf.pdf"
    p.write_text("This is not a PDF file.", encoding="utf-8")
    return p


@pytest.fixture()
def missing_file(tmp_path: Path) -> Path:
    """A path that does not exist on disk."""
    return tmp_path / "nonexistent.pdf"


@pytest.fixture()
def empty_pdf(tmp_path: Path) -> Path:
    """A zero-byte file with a .pdf extension."""
    p = tmp_path / "empty.pdf"
    p.write_bytes(b"")
    return p


@pytest.fixture()
def corrupted_pdf(tmp_path: Path) -> Path:
    """A file with the PDF magic bytes but garbage content afterwards."""
    p = tmp_path / "corrupted.pdf"
    p.write_bytes(b"%PDF-1.4 this is not real pdf content @@##$$")
    return p


@pytest.fixture()
def txt_file(tmp_path: Path) -> Path:
    """A plain .txt file – wrong extension."""
    p = tmp_path / "report.txt"
    p.write_text("Not a PDF.", encoding="utf-8")
    return p
