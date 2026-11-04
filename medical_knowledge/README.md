# medical_knowledge/

Contains the educational medical glossary used by MediExplain AI.

## Files

- `medical_glossary.json` – 10 common blood/lab test terms with plain-English explanations, categories, and source references.

## Usage

```python
from document_processing.knowledge_base import MedicalKnowledgeBase

kb = MedicalKnowledgeBase()
entry = kb.get_entry("Haemoglobin")
print(entry["simple_explanation"])

# Get all entries formatted as embeddable chunks (for Member 2)
chunks = kb.get_chunks_for_embedding()
```

## Important Notes

- All definitions are sourced from MedlinePlus (U.S. National Library of Medicine).
- These are **educational definitions only** — not personalised medical advice.
- Do not mix glossary data with patient report data.
