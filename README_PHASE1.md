# MediExplain AI – Phase 1: Medical Document Processing

## Introduction

MediExplain AI is a Retrieval-Augmented Generation (RAG) system that explains medical reports in plain language. This repository contains **Phase 1** — the document-processing foundation that feeds the RAG pipeline built by the other three team members.

---

## Phase 1 Objectives

1. Accept and validate PDF medical reports.
2. Extract text from every page while preserving medical values (numbers, units, reference ranges).
3. Clean the extracted text without altering clinical content.
4. Split the cleaned text into overlapping chunks suitable for embedding.
5. Provide an educational medical glossary.
6. Expose a clean, documented API for Member 2 (embeddings & FAISS).

---

## Technologies

| Library | Version | Purpose |
|---------|---------|---------|
| Python  | 3.11+   | Core language |
| pypdf   | 4.3.1   | PDF reading & validation |
| pytest  | 8.2.2   | Automated testing |
| re      | stdlib  | Text cleaning |
| json    | stdlib  | Glossary & structured output |
| pathlib | stdlib  | Safe file handling |

---

## Folder Structure

```
MediExplain-AI/
├── document_processing/
│   ├── __init__.py
│   ├── config.py              # All tunable constants
│   ├── pdf_extractor.py       # PDF validation + text extraction
│   ├── text_cleaner.py        # Text cleaning (preserves medical values)
│   ├── chunking.py            # Overlapping chunk generation
│   ├── knowledge_base.py      # Medical glossary loader
│   └── document_processor.py # Main pipeline + integration contract
├── medical_knowledge/
│   ├── README.md
│   └── medical_glossary.json
├── sample_reports/
│   └── README.md              # Never commit real patient PDFs
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures (synthetic data only)
│   ├── test_pdf_extractor.py
│   ├── test_text_cleaner.py
│   ├── test_chunking.py
│   └── test_document_processor.py
├── requirements.txt
├── .gitignore
└── README_PHASE1.md
```

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd MediExplain-AI

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Process a single PDF

```python
from document_processing import process_medical_pdf

result = process_medical_pdf("sample_reports/cbc_report.pdf")

print(result["filename"])      # cbc_report.pdf
print(result["total_pages"])   # 2
print(result["total_chunks"])  # 6

for chunk in result["chunks"]:
    print(chunk["text"])
    print(chunk["metadata"])
```

### Get chunks for embedding (Member 2 integration)

```python
from document_processing import process_medical_pdf, get_document_chunks

doc = process_medical_pdf("sample_reports/report.pdf")
chunks = get_document_chunks(doc)

# chunks is a list of:
# {
#   "text": "Haemoglobin: 10 g/dL. Reference range: 12-16 g/dL.",
#   "metadata": {
#     "source": "report.pdf",
#     "page": 1,
#     "chunk_id": "chunk_001",
#     "document_type": "medical_report"
#   }
# }
```

### Process multiple PDFs

```python
from document_processing.document_processor import process_multiple_pdfs

results = process_multiple_pdfs([
    "reports/report_a.pdf",
    "reports/report_b.pdf",
])
```

### Use the medical glossary

```python
from document_processing import MedicalKnowledgeBase

kb = MedicalKnowledgeBase()

# Look up a term
entry = kb.get_entry("Haemoglobin")
print(entry["simple_explanation"])

# Get all terms as embeddable chunks
chunks = kb.get_chunks_for_embedding()
```

### Clean and chunk text directly

```python
from document_processing.text_cleaner import TextCleaner
from document_processing.chunking import TextChunker

cleaner = TextCleaner()
clean_text = cleaner.clean("Haemoglobin:  10  g/dL\r\n\r\n\r\n")
# → "Haemoglobin: 10 g/dL"

chunker = TextChunker(chunk_size=500, chunk_overlap=100)
pages = [{"page_number": 1, "text": clean_text, "ocr_required": False}]
chunks = chunker.chunk_pages(pages, source="report.pdf")
```

---

## Example Output

```json
{
  "filename": "sample_report.pdf",
  "total_pages": 2,
  "total_chunks": 4,
  "chunks": [
    {
      "text": "CBC REPORT Haemoglobin: 10 g/dL Reference Range: 12-16 g/dL",
      "metadata": {
        "source": "sample_report.pdf",
        "page": 1,
        "chunk_id": "chunk_001",
        "document_type": "medical_report"
      }
    }
  ]
}
```

---

## Configuration

All tunable constants are in `document_processing/config.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE_MB` | 50 | Maximum PDF size |
| `DEFAULT_CHUNK_SIZE` | 500 | Target chars per chunk |
| `DEFAULT_CHUNK_OVERLAP` | 100 | Overlap chars between chunks |
| `DOCUMENT_TYPE` | `"medical_report"` | Metadata label |

---

## Running Tests

```bash
pytest -v
```

All tests use synthetic data. No real patient information is used anywhere.

---

## Integration Guide for Member 2 (Embeddings & FAISS)

### What Phase 1 provides

The function `process_medical_pdf(file_path)` returns:

```python
{
    "filename": str,
    "total_pages": int,
    "total_chunks": int,
    "chunks": [
        {
            "text": str,           # cleaned text ready for embedding
            "metadata": {
                "source": str,     # original filename
                "page": int,       # page number (1-based)
                "chunk_id": str,   # unique ID e.g. "chunk_001"
                "document_type": str  # always "medical_report"
            }
        }
    ]
}
```

### Stable helper

Use `get_document_chunks(processed_document)` to extract the chunk list without depending on the internal dict structure.

### Glossary chunks

`MedicalKnowledgeBase().get_chunks_for_embedding()` returns the same chunk format (`text` + `metadata`) so glossary entries can be embedded alongside report chunks.

### Page metadata note

When a chunk merges content that spans a page boundary, the `"page"` field records the page where the chunk's text begins. If fine-grained page attribution is needed, use the raw page-level extraction result from `PDFExtractor.extract()`.

### Do not modify

Do not change the structure of the `chunks` list or its `metadata` keys. Member 3 (RAG/Gemini) also depends on this contract.
