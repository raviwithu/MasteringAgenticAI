# 🕸️ Graph RAG with Neo4j

Week 2 notebooks using **Neo4j** as both the **vector database** (native vector
index over chunk embeddings) **and** the **knowledge graph** (typed nodes +
relationships), over the threat-modeling reference books.

| Notebook | What it does |
|----------|--------------|
| [`neo4j_graph_rag.ipynb`](neo4j_graph_rag.ipynb) | Builds the graph + vector index and runs Graph RAG: query → encode → vector seed → graph expansion → optional answer. **Run this first** (it populates the graph the other notebook reads). |
| [`threat_modeling_flow_review.ipynb`](threat_modeling_flow_review.ipynb) | Uses the Graph RAG KB to **review a proposed threat-modeling (ISO/SAE 21434 TARA) flow** step by step — grounds each transition in retrieved passages, has an LLM judge it, then synthesizes an overall verdict + a recommended corrected flow. |

The first notebook builds a **Graph RAG** pipeline: plain vector RAG retrieves the
*k* nearest chunks and stops; Graph RAG uses those hits as **entry points**, then
**traverses the graph** to gather context the embedding alone would miss.

Plain vector RAG retrieves the *k* nearest chunks and stops. Graph RAG uses those
vector hits as **entry points**, then **traverses the graph** to gather context the
embedding alone would miss — the surrounding passage, and other chunks about the
same entities.

```
                    ┌──────────────── Neo4j ────────────────┐
 query ──encode──▶  │  VECTOR INDEX           GRAPH          │
                    │  (:Chunk {embedding})   (:Book)-[:HAS_CHUNK]->(:Chunk)
                    │      │ top-k seeds       (:Chunk)-[:NEXT]->(:Chunk)
                    │      ▼                   (:Chunk)-[:MENTIONS]->(:Entity)
                    │   seed chunks ──expand──▶ neighbours + same-entity chunks
                    └───────────────────────────────│──────┘
                                                     ▼
                                       grounded context ──▶ (optional) LLM answer
```

## Graph schema

| Node | Key properties | Relationships |
|------|----------------|----------------|
| `:Book` | `title` | `-[:HAS_CHUNK]->(:Chunk)` |
| `:Chunk` | `id, text, page, seq, embedding` (384-dim) | `-[:NEXT]->(:Chunk)`, `-[:MENTIONS]->(:Entity)` |
| `:Entity` | `name, type` | `<-[:MENTIONS]-(:Chunk)` |

- **`HAS_CHUNK`** — which book a chunk came from.
- **`NEXT`** — reading order, so a hit can pull its neighbouring passage.
- **`MENTIONS`** — links chunks (across books/pages) that share a threat-modeling
  entity (STRIDE categories, standards like ISO/SAE 21434, core concepts). These
  are the cross-corpus paths Graph RAG traverses.

## Pipeline (what the notebook does)

1. **Load & chunk** the PDFs in `Reference/Books` (auto-discovered upward).
2. **Encode** every chunk with `BAAI/bge-small-en-v1.5` (local, GPU auto-detected,
   384-dim, L2-normalized).
3. **Build the graph** — bulk-load `:Book`/`:Chunk` nodes with embeddings, then
   `NEXT` and `MENTIONS` relationships.
4. **Create the vector index** (`db.index.vector.queryNodes`, cosine).
5. **Retrieve** — vector search for seed chunks, then **graph-expand** to
   neighbours and same-entity chunks.
6. **(Optional) Answer** with an LLM grounded on the expanded context.

## Run it

### 1. Start Neo4j (local Docker)

```bash
docker run -d --name neo4j-graphrag -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphrag-demo-pw neo4j:5.26
```

Browser UI: <http://localhost:7474> · Bolt: `bolt://localhost:7687`.
Requires Neo4j **5.15+** for the GA vector index (5.26 used here). To use **Neo4j
Aura** (cloud) instead, skip Docker and set the connection vars below.

### 2. Install deps & configure

```bash
pip install -r requirements.txt
cp .env.example .env        # defaults match the Docker command; add OPENAI_API_KEY to enable answers
```

| Variable | Purpose | Default |
|----------|---------|---------|
| `NEO4J_URI` | Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Credentials | `neo4j` / `graphrag-demo-pw` |
| `OPENAI_API_KEY` | Enables the final answer step (blank → skipped) | _(empty)_ |
| `REFERENCE_BOOKS_DIR` | Override book folder | auto-discovered |

### 3. Open the notebook

```bash
jupyter lab neo4j_graph_rag.ipynb     # run cells top to bottom
```

### 4. Stop / clean up

```bash
docker stop neo4j-graphrag      # keep the data
docker rm -f neo4j-graphrag     # delete the container
```

## Why Graph RAG (vs plain vector RAG)

The vector index finds *semantically* similar chunks; the graph adds chunks that
are *structurally* related — the passage a hit was cut from (`NEXT`) and
corpus-wide chunks on the same entity (`MENTIONS`). Neo4j serves **both** from one
store, so there's no separate vector database to keep in sync.

The entity layer here is a deterministic keyword vocabulary for clarity; a
production system would extract entities/relationships with an LLM (e.g.
`neo4j-graphrag` or LangChain's `LLMGraphTransformer`) for a richer graph to
traverse. You can also rerank the expanded set (see the Week 1 app's
`reference_query_rerank.ipynb`) before sending it to the LLM.

> Training/sample project — generated content assists analysis and is not a
> substitute for a professional security review.
