"""Reference knowledge base — threat-modeling books in ChromaDB.

Ingests the PDF books in the reference folder (PDF → chunk → **local GPU
embeddings** → persistent ChromaDB) and retrieves relevant passages to ground
threat-model generation.

All heavy dependencies (chromadb, sentence-transformers/torch, pypdf, langchain
text splitters) are imported **lazily**, so the rest of the app keeps working
without them — the reference feature is simply unavailable until they're
installed and `ingest_references.py` has been run.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Paths & config (env-overridable)
# --------------------------------------------------------------------------- #
_PKG_DIR = Path(__file__).resolve().parent          # .../threat_model
_PROJECT_DIR = _PKG_DIR.parent                       # ai-threat-modeling-assistant
_DATA_DIR = _PROJECT_DIR / "data"

EMBEDDING_MODEL = os.getenv("REFERENCE_EMBEDDING_MODEL",
                            os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"))
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE") or None          # None => auto (cuda>mps>cpu)
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "128"))
CHROMA_DIR = Path(os.getenv("REFERENCE_CHROMA_DIR", str(_DATA_DIR / "reference_chroma")))
COLLECTION = os.getenv("REFERENCE_COLLECTION", "threat_modeling_refs")
STATE_PATH = _DATA_DIR / "reference_index_state.json"
CHUNK_SIZE = int(os.getenv("REFERENCE_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("REFERENCE_CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("REFERENCE_TOP_K", "5"))
QUERY_INSTRUCTION = os.getenv(
    "REFERENCE_QUERY_INSTRUCTION",
    "Represent this sentence for searching relevant passages: ",
)


def resolve_books_dir() -> Path | None:
    """Locate the reference books folder.

    Uses ``REFERENCE_BOOKS_DIR`` if set, else searches upward from the project for
    a ``Reference/Books`` directory (so it works regardless of nesting).
    """
    env = os.getenv("REFERENCE_BOOKS_DIR")
    if env:
        p = Path(env).expanduser()
        return p if p.is_dir() else None
    for base in [_PROJECT_DIR, *_PROJECT_DIR.parents]:
        cand = base / "Reference" / "Books"
        if cand.is_dir():
            return cand
    return None


# --------------------------------------------------------------------------- #
# Embeddings (local, GPU auto-detect) — lazy
# --------------------------------------------------------------------------- #
_MODEL: Any = None


def _device() -> str:
    if EMBEDDING_DEVICE:
        return EMBEDDING_DEVICE
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        dev = _device()
        logger.info("Loading reference embedding model '%s' on device '%s'…",
                    EMBEDDING_MODEL, dev)
        _MODEL = SentenceTransformer(EMBEDDING_MODEL, device=dev)
        if dev == "cuda":
            try:
                import torch
                logger.info("GPU: %s", torch.cuda.get_device_name(0))
            except Exception:  # noqa: BLE001
                pass
    return _MODEL


def _embed_passages(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return model.encode(
        texts, batch_size=EMBEDDING_BATCH_SIZE, normalize_embeddings=True,
        show_progress_bar=len(texts) > 1, convert_to_numpy=True,
    ).tolist()


def _embed_query(text: str) -> list[float]:
    model = _get_model()
    return model.encode(
        [f"{QUERY_INSTRUCTION}{text}"], normalize_embeddings=True, convert_to_numpy=True,
    )[0].tolist()


# --------------------------------------------------------------------------- #
# PDF loading + chunking
# --------------------------------------------------------------------------- #
def _file_hash(path: Path, block: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(block), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _pdf_stream(path: Path) -> io.BytesIO:
    """Return a clean PDF byte stream.

    Some "PDFs" are actually saved HTTP multipart upload bodies (a ``-----``
    boundary + headers wrapping the real PDF). We slice from the ``%PDF`` marker
    to the final ``%%EOF`` so such files parse correctly.
    """
    data = path.read_bytes()
    if data[:5] == b"%PDF-":
        return io.BytesIO(data)
    start = data.find(b"%PDF-")
    if start == -1:
        raise ValueError(f"{path.name}: no %PDF marker found (not a PDF?)")
    end = data.rfind(b"%%EOF")
    data = data[start: end + 5] if end != -1 else data[start:]
    logger.info("%s: stripped non-PDF wrapper (PDF starts at byte %d)", path.name, start)
    return io.BytesIO(data)


def _load_pdf_chunks(path: Path, splitter) -> list[dict[str, Any]]:
    """Extract text per page and split into chunks with page metadata."""
    from pypdf import PdfReader

    reader = PdfReader(_pdf_stream(path))
    title = path.stem
    chunks: list[dict[str, Any]] = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        for j, piece in enumerate(splitter.split_text(text)):
            chunks.append({
                "id": f"{title}-p{page_no:04d}-c{j:02d}",
                "text": piece,
                "metadata": {
                    "source": title,
                    "source_file": path.name,
                    "page": page_no,
                    "chunk_index": j,
                },
            })
    return chunks


# --------------------------------------------------------------------------- #
# The knowledge base
# --------------------------------------------------------------------------- #
class ReferenceKB:
    """Persistent ChromaDB index over the reference PDFs."""

    def __init__(self, persist_dir: Path | str = CHROMA_DIR,
                 collection: str = COLLECTION) -> None:
        import chromadb

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._col = self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self._col.count()

    def reset(self) -> None:
        self._client.delete_collection(self.collection_name)
        self._col = self._client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    # ---- state ----
    def _load_state(self) -> dict[str, Any]:
        if STATE_PATH.exists():
            try:
                return json.loads(STATE_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"documents": {}, "embedding_model": EMBEDDING_MODEL}

    def _save_state(self, state: dict[str, Any]) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

    # ---- ingest ----
    def ingest(self, books_dir: Path | str | None = None,
               force: bool = False) -> dict[str, int]:
        """Incrementally index the PDF books (per-file content hash)."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        books = Path(books_dir) if books_dir else resolve_books_dir()
        if not books or not books.is_dir():
            raise FileNotFoundError(
                "Reference books folder not found. Set REFERENCE_BOOKS_DIR or place "
                "PDFs in a Reference/Books folder."
            )
        pdfs = sorted(books.glob("*.pdf"))
        if not pdfs:
            raise FileNotFoundError(f"No PDF files in {books}")

        state = self._load_state()
        if state.get("embedding_model") != EMBEDDING_MODEL:
            logger.warning("Embedding model changed; re-indexing all references.")
            force = True
        docs_state: dict[str, Any] = state.get("documents", {})
        if force:
            self.reset()
            docs_state = {}

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        report = {"files_indexed": 0, "files_skipped": 0, "chunks": 0}

        for pdf in pdfs:
            file_hash = _file_hash(pdf)
            prev = docs_state.get(pdf.name)
            if prev and prev.get("hash") == file_hash:
                report["files_skipped"] += 1
                continue
            if prev:  # changed → drop old chunks first
                self._col.delete(where={"source_file": pdf.name})

            logger.info("Reading %s…", pdf.name)
            try:
                chunks = _load_pdf_chunks(pdf, splitter)
            except Exception as exc:  # noqa: BLE001 - one bad file shouldn't abort all
                logger.error("Failed to read %s: %s; skipping.", pdf.name, exc)
                report["files_skipped"] += 1
                continue
            if not chunks:
                logger.warning("No extractable text in %s; skipping.", pdf.name)
                continue
            logger.info("Embedding %d chunks from %s…", len(chunks), pdf.name)
            embeddings = _embed_passages([c["text"] for c in chunks])
            self._col.upsert(
                ids=[c["id"] for c in chunks],
                embeddings=embeddings,
                documents=[c["text"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks],
            )
            docs_state[pdf.name] = {"hash": file_hash, "chunks": len(chunks)}
            report["files_indexed"] += 1
            report["chunks"] += len(chunks)
            logger.info("Indexed %s: %d chunks", pdf.name, len(chunks))

        state["documents"] = docs_state
        state["embedding_model"] = EMBEDDING_MODEL
        self._save_state(state)
        logger.info("Reference ingest done: %s | total=%d", report, self.count())
        return report

    # ---- search ----
    def search(self, query: str, k: int = TOP_K) -> list[dict[str, Any]]:
        if self.count() == 0:
            return []
        qv = _embed_query(query)
        res = self._col.query(
            query_embeddings=[qv], n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        return [
            {"text": t, "metadata": m or {}, "score": round(1.0 - float(d), 4)}
            for t, m, d in zip(docs, metas, dists)
        ]


# --------------------------------------------------------------------------- #
# Convenience: formatted context for prompt injection (always graceful)
# --------------------------------------------------------------------------- #
def retrieve_reference_context(query: str, k: int = TOP_K,
                              max_chars: int = 4000) -> str:
    """Return formatted reference passages for the prompt, or '' if unavailable.

    Never raises — if the deps/index are missing, returns '' so generation
    proceeds without reference grounding.
    """
    try:
        kb = ReferenceKB()
        if kb.count() == 0:
            return ""
        hits = kb.search(query, k=k)
    except Exception as exc:  # noqa: BLE001 - reference grounding is best-effort
        logger.warning("Reference retrieval unavailable: %s", exc)
        return ""

    parts, total = [], 0
    for h in hits:
        m = h["metadata"]
        block = f"[{m.get('source', 'book')}, p.{m.get('page', '?')}]\n{h['text'].strip()}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
