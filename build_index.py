"""
build_index.py - Build the local search index from the rescued knowledge base.

Replaces ingest.py. Reads kb_export/originals/, extracts text, chunks it,
embeds every chunk with Cohere, and writes two files that retrieval.py loads
at startup. No search service involved - the index is just files in the repo.

    export COHERE_API_KEY="..."
    python build_index.py                 # build from kb_export/originals
    python build_index.py --dry-run       # extract + chunk, skip embedding

Outputs:
    kb_index.npz     float32 matrix of chunk embeddings
    kb_chunks.json   chunk text + source filename, aligned to the matrix rows
"""

import argparse
import json
import os
import sys

SRC_DEFAULT = "kb_export/originals"
EMBED_MODEL = "embed-multilingual-v3.0"
BATCH = 96                 # Cohere's per-call limit for embed
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
MIN_CHUNK = 80             # discard slivers


def extract_text(path):
    """Pull plain text out of a .pdf / .md / .txt file."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            sys.exit("Missing dependency. Run:  pip install pypdf")
        try:
            reader = PdfReader(path)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:  # noqa: BLE001
            print("  WARN  could not parse %s (%s)" % (os.path.basename(path), e))
            return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk_text(text, size=CHUNK_CHARS, overlap=CHUNK_OVERLAP):
    """Split on paragraph boundaries, packing up to `size` chars per chunk."""
    text = "\n".join(line.rstrip() for line in text.splitlines())
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""

    for para in paras:
        # A single oversized paragraph gets hard-split.
        if len(para) > size:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(para), size - overlap):
                piece = para[i:i + size].strip()
                if len(piece) >= MIN_CHUNK:
                    chunks.append(piece)
            continue
        if len(current) + len(para) + 2 <= size:
            current = (current + "\n\n" + para) if current else para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) >= MIN_CHUNK]


def main():
    ap = argparse.ArgumentParser(description="Build the local KB search index.")
    ap.add_argument("--dir", default=SRC_DEFAULT, help="Source folder (default: %s)" % SRC_DEFAULT)
    ap.add_argument("--dry-run", action="store_true", help="Extract and chunk without embedding")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        sys.exit("Source folder not found: %s" % args.dir)

    files = sorted(
        os.path.join(args.dir, n) for n in os.listdir(args.dir)
        if os.path.splitext(n)[1].lower() in (".pdf", ".md", ".txt", ".markdown")
    )
    if not files:
        sys.exit("No .pdf / .md / .txt files found under: %s" % args.dir)

    print("Extracting text from %d file(s)...\n" % len(files))

    records, empty = [], []
    for path in files:
        name = os.path.basename(path)
        text = extract_text(path)
        pieces = chunk_text(text) if text.strip() else []
        if not pieces:
            empty.append(name)
            print("  EMPTY %s" % name)
            continue
        for piece in pieces:
            records.append({"text": piece, "document_name": name})
        print("  %-58s %6d chars -> %3d chunks" % (name[:58], len(text), len(pieces)))

    print("\n%d chunks from %d file(s)." % (len(records), len(files) - len(empty)))
    if empty:
        print("WARNING: %d file(s) yielded no text (likely scanned images "
              "needing OCR):" % len(empty))
        for n in empty:
            print("  - %s" % n)

    if args.dry_run:
        print("\n[dry-run] Nothing embedded.")
        return
    if not records:
        sys.exit("Nothing to embed.")

    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        sys.exit("COHERE_API_KEY is not set.")
    try:
        import cohere
        import numpy as np
    except ImportError:
        sys.exit("Missing dependencies. Run:  pip install cohere numpy pypdf")

    co = cohere.ClientV2(api_key=api_key)
    vectors = []
    print("\nEmbedding %d chunks with %s..." % (len(records), EMBED_MODEL))
    for i in range(0, len(records), BATCH):
        batch = [r["text"] for r in records[i:i + BATCH]]
        resp = co.embed(texts=batch, model=EMBED_MODEL,
                        input_type="search_document", embedding_types=["float"])
        vectors.extend(resp.embeddings.float_)
        print("  %d / %d" % (min(i + BATCH, len(records)), len(records)))

    matrix = np.array(vectors, dtype="float32")
    # Pre-normalise so query time is a single dot product.
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = matrix / np.maximum(norms, 1e-9)

    np.savez_compressed("kb_index.npz", vectors=matrix)
    with open("kb_chunks.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)

    print("\nWrote kb_index.npz (%d x %d) and kb_chunks.json (%d chunks)."
          % (matrix.shape[0], matrix.shape[1], len(records)))
    print("Commit both so deploys don't need to rebuild.")


if __name__ == "__main__":
    main()