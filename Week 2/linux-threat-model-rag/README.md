# 🐧 Linux System Threat Model — RAG + Traceable TARA

A self-contained Week 2 project that builds a **RAG knowledge base from the Linux
security PDFs** in [`../Data/Linux`](../Data/Linux) and uses it to generate a
complete, **fully traceable** threat model for a Linux system — an ISO/SAE
21434-style TARA chain — persisted in a **SQLite relational database** with
ChromaDB source provenance.

All generated stores (ChromaDB, SQLite, ingestion state) live under this project's
`data/` folder.

## Pipeline

```
RAW PDFs (Week 2/Data/Linux)
    └─ hash check ─ chunk ─ embed (bge-small, GPU) ─▶ ChromaDB collection "linux_kb"

For each of the 12 TARA entities, in order:
    create query → embed → retrieve (ChromaDB) → metadata filter → rerank
        → LLM (grounded + prior entities) → store (SQLite) → parent→child mapping
```

## Traceability chain (each entity is the parent of the next)

```
Linux System / Business Use Case → Item Definition → Assets → Damage Scenarios →
Impact Rating → Threats → Attack Vectors → Attack Feasibility Rating →
Risk Value Determination → Risk Treatment Decision →
Cybersecurity Goals / Requirements → Security Test Cases
```

The threat/attack/feasibility entities use a ChromaDB **metadata filter** to prefer
the offensive-security + privilege-escalation material (with a fallback to
unfiltered retrieval so a filter never starves results). The LLM reuses prior-entity
IDs (`A#`, `DS#`, `T#`, `AV#`, `RV#`, `SR#`, `TC#`) so the linking is visible in the
content as well as in the database.

## Relational schema (`data/threat_model.db` → `threat_model_entities`)

| Column | Meaning |
|--------|---------|
| `entity_id` | `LIN-NN-<key>` (PK) |
| `entity_type` | UseCase, ItemDefinition, Assets, … TestCase |
| `entity_name` | human label |
| `description` | the generated entity output |
| `parent_entity_id` | previous entity in the chain (the parent→child link) |
| `source_chunk_ids` | JSON list of ChromaDB chunk ids that grounded it |
| `retrieval_score` | top-1 cosine similarity |
| `rerank_score` | top-1 cross-encoder score |
| `confidence_score` | `sigmoid(best rerank score)` |
| `created_timestamp` | UTC ISO-8601 |

A companion `entity_relationships` table stores the `child → parent` edges.

## Final outputs (end of the notebook)

1. **Linux threat model summary** (`data/linux_threat_model.md`)
2. **Full relationship graph** — System → … → Security Test Cases (matplotlib + DB edges)
3. **Retrieved source chunks per entity** (provenance table)
4. **Stored database records** (SQLite query)
5. **ChromaDB collection statistics** (count, dim, by-category, source files)
6. **Hash-based ingestion report** (per-file content hash + status)
7. **End-to-end traceability report** (entity → parent → grounding chunks)

## Run

```bash
cd "MasteringAgenticAI/Week 2/linux-threat-model-rag"
pip install -r requirements.txt
cp .env.example .env        # add OPENAI_API_KEY to generate entity text (recommended)
jupyter lab linux_threat_model_rag.ipynb   # run top to bottom
```

- GPU auto-detected for embeddings/rerank. First run downloads `bge-small` (~130 MB)
  and the MiniLM cross-encoder (~80 MB).
- **Re-runs are idempotent:** unchanged PDFs are skipped by content hash; entity
  rows use `INSERT OR REPLACE`. To rebuild from scratch, delete `data/`.
- Run with the **same interpreter/kernel** that wrote `data/chroma` (matching
  ChromaDB version), and don't open that store from another process at the same
  time.

> Training/sample project — the generated TARA assists analysis and is not a
> certified security assessment.
