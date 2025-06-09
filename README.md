# MTG Judge Assistant

A semantic, LLM-assisted assistant for **Magic: The Gathering** rules interpretation and judging.  
Built using **Qdrant**, **sentence-transformers**, and optionally **Meta Llama 3 Instruct** or other chat-capable LLMs.

---

## 🔍 Features

- ✅ Chunked rules (1 rule per atomic chunk)
- ✅ Semantic retrieval with sentence-transformers
- ✅ Structural re-ranking by rule group
- ✅ Dynamic glossary injection (on-demand) (WIP)
- ✅ Hugging Face or local LLM generation
- ✅ JSON-based RAG indexing & prompt building

---

## Project Structure

```
├── download/                                 # Download files goes here (rules)
├── output/                                   # Generated chunks (json)
├── qdrant_data/                              # Vector DB volume
├── download_rules_and_create_chunks.json     # Rules split into chunks
├── save_chunks_to_db.py                      # Vector indexing for rules
├── ask_mtg.py                                # LLM Q&A interface
├── pyproject.toml                            # uv / dependencies
└── README.md                                 # You're here
```
---

## Setup

1. **Install dependencies using `uv`:**
Make sure, that `uv` is installed.

```bash
uv venv
uv sync
```

2. **Run Qdrant locally via Docker:**

```bash
docker run -p 6333:6333 qdrant/qdrant
```

3. **Download and chunk rules (includes glossary):**

```bash
python download_rules_and_create_chunks.py
```

4. **Index rules into Qdrant:**

```bash
python save_chunks_to_db.py
```

---

## Ask Questions

Run the CLI interface:

```bash
python ask_mtg.py
```

Example:

```text
Q> Can a creature with summoning sickness block?

🤖 Answer:
Yes. According to rule 302.6, creatures with summoning sickness can block but can't attack unless they have haste...
```

---

## Retrieval-Augmented Generation

### Prompt Construction Logic

- Retrieve top **K** rule chunks by semantic similarity
- Expand structurally via `rule_group` (under investigation, whether it is good approach)
- Scan rules for glossary terms
- Inject definitions for relevant terms (if found)
- Pass everything to LLM for final response

---

## (WIP) Glossary Integration

Glossary entries are stored and indexed separately.
- Dynamic lookup: only definitions used in retrieved rules are injected

---

## Configuration

Environment variables:
```bash
export HF_API_TOKEN=hf_abc123   # Hugging Face token (if using their endpoint)
```

---

## Data Sources

- Official Magic: The Gathering rules: https://magic.wizards.com/en/rules
- Rules text is parsed from the latest available `.txt` file

---

##  License

This project is for educational purposes.  
Magic: The Gathering is a trademark of Wizards of the Coast.

---
