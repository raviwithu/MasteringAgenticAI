"""Ingest the reference threat-modeling books into ChromaDB (GPU embeddings).

Reads the PDFs in the reference books folder, chunks them, embeds them with a
local model (GPU when available), and stores them in a persistent ChromaDB
collection used to ground threat-model generation.

Usage:
    python ingest_references.py                 # incremental ingest
    python ingest_references.py --force         # re-index everything
    python ingest_references.py --books-dir /path/to/Books
    python ingest_references.py --stats         # show collection size
    python ingest_references.py --search "spoofing of an API client"

Requires: chromadb, sentence-transformers, torch, pypdf, langchain-text-splitters
(see requirements.txt). For an RTX 5090 install a CUDA 12.8+ torch build.
"""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

from threat_model.references import ReferenceKB, resolve_books_dir


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    logging.basicConfig(
        level="INFO", format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = argparse.ArgumentParser(description="Ingest reference books into ChromaDB.")
    parser.add_argument("--books-dir", help="Folder with the PDF books.")
    parser.add_argument("--force", action="store_true", help="Re-index everything.")
    parser.add_argument("--stats", action="store_true", help="Show collection size and exit.")
    parser.add_argument("--search", help="Run a similarity search and print top hits.")
    args = parser.parse_args(argv)

    kb = ReferenceKB()

    if args.stats:
        print(f"Reference collection chunks: {kb.count()}")
        return 0

    if args.search:
        for i, h in enumerate(kb.search(args.search), 1):
            m = h["metadata"]
            print(f"\n[{i}] score={h['score']:.4f}  {m.get('source')} p.{m.get('page')}")
            print("   ", h["text"][:300].replace("\n", " "), "…")
        return 0

    books_dir = args.books_dir or resolve_books_dir()
    if not books_dir:
        print("ERROR: reference books folder not found. Set REFERENCE_BOOKS_DIR or "
              "pass --books-dir.", file=sys.stderr)
        return 1
    print(f"Books dir: {books_dir}")
    report = kb.ingest(books_dir=books_dir, force=args.force)
    print(f"Ingest report: {report}")
    print(f"Total chunks in collection: {kb.count()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
