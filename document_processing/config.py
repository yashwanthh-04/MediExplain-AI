"""
Configuration constants for MediExplain AI - Phase 1 document processing.
All tunable parameters live here so they never need to be hardcoded elsewhere.
"""

# ── PDF validation ──────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB: int = 50          # Maximum allowed PDF size in megabytes
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS: tuple = (".pdf",)
PDF_MAGIC_BYTES: bytes = b"%PDF"    # First 4 bytes of every valid PDF

# ── Chunking ────────────────────────────────────────────────────────────────
DEFAULT_CHUNK_SIZE: int = 500       # Target characters per chunk
DEFAULT_CHUNK_OVERLAP: int = 100    # Characters of overlap between adjacent chunks
CHUNK_ID_PREFIX: str = "chunk"

# ── Document metadata ───────────────────────────────────────────────────────
DOCUMENT_TYPE: str = "medical_report"

# ── Knowledge base ──────────────────────────────────────────────────────────
KNOWLEDGE_BASE_PATH: str = "medical_knowledge/medical_glossary.json"
