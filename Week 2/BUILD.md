# Week 2 — Build Documentation

A writeup of what was built in Week 2, the data and prompts used, the iterations
(including the dead-ends and bugs), and what was learned along the way. Week 2 was
built "vibe-coding" style — driven by short natural-language asks to a coding
assistant, verifying each step by actually running it.

---

## 1. Project overview

Week 2 contains **two related projects**, both about doing Retrieval-Augmented
Generation over security literature and turning it into a *traceable* threat model.

### 2a. `graph-rag-neo4j/`
Uses **Neo4j as both the vector database and the knowledge graph** over the
threat-modeling reference books.

- **`neo4j_graph_rag.ipynb`** — ingest books → chunk → embed (local GPU) → load into
  Neo4j as `(:Book)-[:HAS_CHUNK]->(:Chunk)-[:NEXT]->(:Chunk)` and
  `(:Chunk)-[:MENTIONS]->(:Entity)`, with a native **vector index** on the chunk
  embeddings. Query flow: *encode → vector seed (`db.index.vector.queryNodes`) →
  graph expansion (neighbours + same-entity chunks) → optional grounded answer*.
- **`threat_modeling_flow_review.ipynb`** — uses that Graph-RAG KB to **review a
  proposed ISO/SAE 21434 TARA flow** step by step (each transition grounded in
  retrieved passages and judged by an LLM), then synthesizes a verdict and a
  **visual mapping** of the corrected flow.

### 2b. `linux-threat-model-rag/`
A self-contained **ChromaDB + SQLite** pipeline that generates a fully traceable
Linux threat model.

- **`linux_threat_model_rag.ipynb`** — hash-based ingestion of the Linux security
  PDFs into ChromaDB, then a **12-entity TARA chain** (Use Case → Item Definition →
  Assets → Damage Scenarios → Impact Rating → Threats → Attack Vectors → Attack
  Feasibility → Risk Value → Risk Treatment → Goals/Requirements → Test Cases).
  Each entity runs *embed → retrieve → metadata-filter → rerank → LLM (grounded +
  prior entities)*, is stored in a **SQLite relational DB** with `parent_entity_id`
  links and `source_chunk_ids` provenance, and finally an **item-level traceability
  graph** is extracted and visualized (A1 → DS1 → T1 → AV1 → …).

**Shared toolchain:** local embeddings `BAAI/bge-small-en-v1.5` (384-dim, cosine,
GPU-auto on an RTX 5090 with CUDA 12.8 torch), cross-encoder reranker
`cross-encoder/ms-marco-MiniLM-L-6-v2`, OpenAI `gpt-4o-mini` for generation/judging.

---

## 2. Datasets used

| Project | Source | Notes |
|---------|--------|-------|
| graph-rag-neo4j | `Reference/Books/` (repo root) — *Threat Modeling: Designing for Security* (Shostack) + an automotive ISO/SAE 21434 threat-modeling book | **2,801 chunks** (1,932 + 869). The automotive book was an **image-only scan** and had to be OCR'd before it produced any text. |
| linux-threat-model-rag | `Week 2/Data/Linux/` — 6 PDFs: *Linux Primer*, *Linux Privilege Escalation* (Weeks I–IV), *Hacking Exposed Linux 3rd* | **2,281 chunks**. One PDF was a saved HTTP-multipart upload (starts with `-----`, not `%PDF`) and needed wrapper-stripping. |

Both corpora are **copyrighted books**, so they are **gitignored** (`Week 2/Data/`
and the root `Reference/Books/` are kept out of the repo). Generated stores
(ChromaDB, SQLite, ingestion state) live under each project's `data/` folder and are
also ignored.

A notable **observation about the Linux corpus**: it is ~90% *Hacking Exposed Linux*
(2,073 of 2,281 chunks), and it is rich on *concrete* offensive/defensive content
but contains almost nothing about *ISO 21434 TARA methodology*. This showed up
directly in the per-entity **confidence scores** (see §5).

---

## 3. Prompts used during vibe coding

### 3a. Natural-language asks that drove the build
The Week 2 work was produced from a sequence of short prompts to the coding
assistant (paraphrased, in order):

1. "Review all the CLAUDE.md and README files to understand this workspace."
2. "I added a new file in `Reference/Books`. Re-run the ingestion and check whether it
   uses the GPU for embedding."  → revealed the new PDF was an image-only scan.
3. "Add an OCR fallback" (so scanned PDFs are ingested automatically).
4. "Create a notebook: take a query → embed → retrieve top-k → rerank → display."
5. "What is vector length / L2 norm?" (a concept question, answered in chat).
6. "Create a notebook for Neo4j Graph RAG as a vector database."
7. "Create a notebook that walks the TARA flow (System → Item Definition → Assets →
   … → Test Cases), checks each step against the knowledge base, and recommends how
   the flow should look."
8. **Re-scope:** "Build the RAG knowledge base from `Week 2/Data/Linux`, generate a
   full Linux threat model with the 12-stage traceability chain, store every entity
   in a relational DB with `entity_id, parent_entity_id, source_chunk_ids,
   retrieval_score, rerank_score, confidence_score, …`, apply metadata filters, and
   produce a relationship graph + traceability report. Keep everything in Week 2."
9. "Present the final mapping visually."
10. "I meant a visualization of the *actual outputs* — item definition mapped to
    assets to damage scenarios, etc."
11. Plus operational asks: "Is Streamlit/Jupyter running? I can't reach it from the
    host" → port-forwarding + restarting services; "add the Week 2 folder to git."

### 3b. LLM prompts embedded in the notebooks
These are the prompts the notebooks send to `gpt-4o-mini`:

- **Per-entity generation** (`linux_threat_model_rag.ipynb`): a system prompt —
  *"You are a Linux security engineer performing an ISO/SAE 21434-style TARA … produce
  ONLY this entity's output … build strictly on the prior entities for traceability
  (reuse their IDs and state what each item derives from), and ground your method in
  the reference passages; cite as [source p.N]."* — with a user message carrying the
  system context, the prior entities, the reranked passages, and the stage task.
- **Flow review / judge** (`threat_modeling_flow_review.ipynb`): *"You are a
  cybersecurity engineer reviewing an automotive TARA (Clause 15). Use the provided
  reference passages as primary evidence … reply as JSON with verdict
  (sound/needs_refinement/misordered/missing_step), rationale, missing, citation."*
- **Traceability extraction**: *"Build ONE coherent, CONNECTED traceability graph …
  IGNORE inconsistent IDs and ASSIGN fresh canonical IDs per stage (A#, DS#, IR#, T#,
  AV#, AF#, RV#, RT#, SR#, TC#). Connectivity REQUIRED: DS→A; IR→DS; T→A/DS; AV→T;
  AF→AV; RV→IR/AF; RT→RV; SR→RT/T; TC→SR. Return JSON {items:[{id,stage,label,parents}]}."*
- **Validation page** (Week 1 `pages/1_TARA_Flow_Validator.py`): a per-stage prompt
  asking whether the user's content follows the expected structure, grounded in the
  retrieved passages, returning a JSON verdict.

All structured prompts use OpenAI's `response_format={"type":"json_object"}`.

---

## 4. Iterations tried (what went wrong, what fixed it)

The build was iterative — most features took 2–3 passes, verified by re-running.

**OCR fallback**
- The newly-added automotive book yielded **0 extractable text pages** (a 274-page
  scan). First it was skipped; then OCR'd with `ocrmypdf` (all 274 pages gained a
  text layer); then an **automatic OCR fallback** was added to `references.py` so any
  image-only PDF is OCR'd at ingest time (cached by content hash).

**Neo4j Graph RAG**
- First run had **0 `NEXT` edges**: `:Chunk` nodes were created without a `book`
  property, so the `ORDER BY c.book` / `WHERE a.book = b.book` reading-order query
  silently produced nothing. Fixed by storing `book` on each chunk → 2,799 `NEXT`
  edges. Also fixed a `-[:NEXT|NEXT]-` typo and silenced noisy server notifications.

**Flow-review visualization**
- The "recommended addition" boxes first showed a `➕` emoji that rendered as a
  **missing-glyph tofu box** (matplotlib's default font has no emoji) → replaced with
  an ASCII `+ add here`.

**Linux TARA — re-scope and the relational DB**
- Originally scoped to the threat-modeling books; re-scoped to `Week 2/Data/Linux`
  and a SQLite relational schema with parent→child links + ChromaDB provenance.

**Linux item-level traceability — three passes (the hardest part)**
1. The SQLite DB initially held **"LLM disabled" placeholder text** — the notebook
   had been run without an `OPENAI_API_KEY`, so no `A#`/`DS#` IDs existed to map.
   Fix: re-run with the key injected at execution time.
2. First extraction was **sparse and broken**: the 12 entities were generated
   independently with inconsistent ID schemes (`LS-TARA-001` vs `A1`), so
   cross-references pointed at IDs that were never captured → dangling edges, and the
   end-to-end trace collapsed.
3. A "normalize into one connected graph" extraction prompt then returned **0
   items** — the model put the stage in the `stage` field as the *ID prefix*
   (`"A"`, `"DS"`) rather than the full name, and the `stage in ID_STAGES` filter
   dropped everything. **Final fix:** derive each item's stage from its **ID prefix**
   (`A1`→assets, `TC1`→test_cases), require per-stage coverage + connectivity in the
   prompt, and **prune any parent reference that doesn't resolve**. Result: **53
   items, 10/10 stages, 53/53 linked, 0 dangling refs.**

**Operational hiccups**
- **ChromaDB single-process limit:** opening `data/reference_chroma` from a notebook
  while another kernel (the rerank notebook) still held it triggered a Rust-bindings
  panic (`'RustBindingsAPI' object has no attribute 'bindings'` / "Could not connect
  to tenant"). The store was fine; the fix was to ensure only one process opens it.
- **Container restart** killed both Jupyter and the Neo4j container mid-session;
  restarting them restored everything (Neo4j data persisted across stop/start).

---

## 5. Learnings & observations

- **Neo4j as a unified vector + graph store works well.** `db.index.vector.queryNodes`
  finds the seeds; one extra Cypher hop expands to neighbours and same-entity chunks.
  Graph RAG surfaced relevant passages that pure vector search ranked low (e.g. a
  passage at retrieval rank #18 was promoted to a top result after expansion/rerank).
- **Retrieve-then-rerank matters.** The cross-encoder reordered results meaningfully
  vs the bi-encoder (e.g. the most on-topic "payment threat model" passage was dense
  rank #4 but rerank #1). The same rerank confidence doubles as a useful signal.
- **Confidence exposes corpus/topic mismatch.** In the Linux TARA, concrete entities
  grounded strongly (Assets 0.99, Threats 0.98, Attack Vectors 0.98) but abstract
  *method* entities grounded weakly (Item Definition 0.06, Feasibility 0.02, Risk
  Treatment 0.005) — because the Linux books cover hacking, not ISO 21434 process.
  The confidence score made that visible rather than hiding it.
- **LLM structured extraction needs defensive parsing.** Don't trust the model's
  `stage`/category labels (it returned ID prefixes); derive structure deterministically
  from a reliable field (the ID), require coverage + connectivity explicitly, and
  prune edges that don't resolve so the graph is never silently broken.
- **Independent generations don't share an ID namespace.** Generating 12 entities
  separately produced inconsistent IDs; a single *normalization* pass over the whole
  output produced a coherent, connected graph.
- **Local-first is cheap and fast.** Ingest + embed + rerank are 100% local on the
  GPU; only generation/judging calls OpenAI. Embedding ~2,800 chunks takes seconds.
- **Reproducibility:** content-hash incremental ingest skips unchanged PDFs; SQLite
  uses deterministic `entity_id`s with `INSERT OR REPLACE`; deleting `data/` rebuilds
  from scratch. The same ChromaDB version must read and write a store.
- **Vibe-coding workflow:** every notebook was *executed and its outputs inspected
  programmatically* (counts, link resolution, rendered images) rather than assumed
  correct — which is how the 0-edge, placeholder-text, and 0-item bugs were caught.
  Secrets and copyrighted data were kept out of git throughout.

---

## 6. File map

```
Week 2/
├── BUILD.md                      # this document
├── Data/Linux/                   # source PDFs (gitignored, copyrighted)
├── graph-rag-neo4j/
│   ├── neo4j_graph_rag.ipynb
│   ├── threat_modeling_flow_review.ipynb
│   ├── README.md · requirements.txt · .env.example
└── linux-threat-model-rag/
    ├── linux_threat_model_rag.ipynb
    ├── README.md · requirements.txt · .env.example · .gitignore
    └── data/                     # generated: chroma/, threat_model.db, … (gitignored)
```

> Training/sample projects — generated threat models assist analysis and are not a
> substitute for a certified security assessment.
