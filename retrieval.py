"""
Local Cohere-backed retrieval for the Gus Baha knowledge base.

Exposes the same three public functions expected by generator.py:

    retrieve_context(query, top_k)        -> list[dict]
    format_context_for_prompt(chunks)     -> str
    get_unique_sources(chunks)            -> list[dict]
"""

import json
import os
import re

try:
    import cohere
except ImportError:  # pragma: no cover
    cohere = None

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

# Index files produced by build_index.py
INDEX_PATH = os.environ.get("KB_INDEX_PATH", "kb_index.npz")
CHUNKS_PATH = os.environ.get("KB_CHUNKS_PATH", "kb_chunks.json")

EMBED_MODEL = os.environ.get("COHERE_EMBED_MODEL", "embed-multilingual-v3.0")
RERANK_MODEL = os.environ.get("COHERE_RERANK_MODEL", "rerank-v3.5")
# How many nearest neighbours to hand the reranker.
CANDIDATE_POOL = int(os.environ.get("KB_CANDIDATE_POOL", "40"))

# Source metadata for citations (unchanged from zeroentropy_client.py).
SOURCES = {
    # ==================
    # YOUTUBE VIDEOS
    # ==================
    "gus_baha_full_transcript.txt": {
        "title": "Ngaji Penuh Humor Ilmiah Gus Baha' bersama Prof Quraish Shihab",
        "url": "https://www.youtube.com/watch?v=RHnuHSFOeNw",
        "channel": "NU Online",
        "date": "1 Oktober 2025",
        "type": "video"
    },
    "gusbaha_10_refined.md": {
        "title": "10 Ajaran Inti Gus Baha (Distilasi)",
        "url": "https://www.youtube.com/watch?v=RHnuHSFOeNw",
        "channel": "NU Online",
        "date": "1 Oktober 2025",
        "type": "summary"
    },

    # ==================
    # BOOKS - Islam Santuy
    # ==================
    "IslamSantuy_HTI_GusBaha.txt": {
        "title": "Islam Santuy Ala Gus Baha - Pandangan tentang HTI",
        "url": None,
        "author": "Muhammad Khoirul Huda",
        "book": "Islam Santuy Ala Gus Baha",
        "pages": "151-154",
        "date": None,
        "type": "book"
    },
    "IslamSantuy_DikotomiIlmu_GusBaha.txt": {
        "title": "Islam Santuy Ala Gus Baha - Dikotomi Ilmu Pengetahuan",
        "url": None,
        "author": "Habib Maulana Maslahul Adi",
        "book": "Islam Santuy Ala Gus Baha",
        "pages": "99-103",
        "date": None,
        "type": "book"
    },
}

# Partial match patterns for flexible source detection (unchanged).
SOURCE_PATTERNS = {
    "IslamSantuy": {
        "title": "Islam Santuy Ala Gus Baha",
        "url": None,
        "book": "Islam Santuy Ala Gus Baha",
        "type": "book"
    },
    "HTI": {
        "title": "Pandangan Gus Baha tentang HTI",
        "url": None,
        "book": "Islam Santuy Ala Gus Baha",
        "type": "book"
    },
    "Dikotomi": {
        "title": "Dikotomi Ilmu Pengetahuan",
        "url": None,
        "book": "Islam Santuy Ala Gus Baha",
        "type": "book"
    },
    "transcript": {
        "title": "Ngaji Gus Baha bersama Prof Quraish Shihab",
        "url": "https://www.youtube.com/watch?v=RHnuHSFOeNw",
        "channel": "NU Online",
        "type": "video"
    },
    "refined": {
        "title": "10 Ajaran Inti Gus Baha",
        "url": "https://www.youtube.com/watch?v=RHnuHSFOeNw",
        "channel": "NU Online",
        "type": "summary"
    },
    # Hawa's Blog pattern
    "Hawa's Blog": {
        "title": "Hawa's Blog",
        "url": None,
        "book": "Syajaratul Ma'arif",
        "author": "Syaikh al-'Izz bin Abdus Salam",
        "type": "book"
    },
}


def get_source_metadata(document_name: str) -> dict:
    """Get source metadata for a document (unchanged from zeroentropy_client.py)."""
    if not document_name:
        return _default_source()

    # Try exact match first
    if document_name in SOURCES:
        return SOURCES[document_name]

    # Try partial match on full path/name
    for key, value in SOURCES.items():
        if key in document_name or document_name in key:
            return value

    # Special handling for Hawa's Blog PDFs
    doc_lower = document_name.lower()
    if "hawa" in doc_lower or "hawa's blog" in doc_lower:
        # Extract article title from filename
        # e.g., "don't be harsh _ Hawa's Blog.PDF" -> "Don't Be Harsh"
        title = document_name
        # Remove common suffixes
        title = re.sub(r"[_\s]*Hawa'?s?\s*Blog\.PDF", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\.pdf$", "", title, flags=re.IGNORECASE)
        title = title.replace("_", " ").strip()
        # Capitalize nicely
        title = title.title()

        return {
            "title": title,
            "url": None,
            "book": "Syajaratul Ma'arif",
            "author": "Syaikh al-'Izz bin Abdus Salam",
            "type": "book"
        }

    # Try pattern matching
    for pattern, meta in SOURCE_PATTERNS.items():
        if pattern.lower() in doc_lower:
            return meta

    # Default fallback
    return _default_source()


def _default_source() -> dict:
    """Default source when no match found."""
    return {
        "title": "Pengajian Gus Baha",
        "url": None,
        "type": "unknown"
    }


# --- Lazy client + index ------------------------------------------------------

_co = None
_vectors = None      # (n_chunks, dim) float32, L2-normalised
_chunks = None       # list of {"text", "document_name"}


def _get_client():
    """Instantiate the Cohere client once, lazily. Returns None if unavailable."""
    global _co
    if _co is not None:
        return _co
    if cohere is None:
        print("Warning: cohere package not installed (pip install cohere)")
        return None
    if not os.environ.get("COHERE_API_KEY"):
        print("Warning: COHERE_API_KEY not set")
        return None
    _co = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
    return _co


def _load_index():
    """Load the embedding matrix and chunk texts once. Returns False if missing."""
    global _vectors, _chunks
    if _vectors is not None and _chunks is not None:
        return True
    if np is None:
        print("Warning: numpy not installed (pip install numpy)")
        return False
    if not (os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH)):
        print("Warning: index not found (%s / %s). Run: python build_index.py"
              % (INDEX_PATH, CHUNKS_PATH))
        return False
    try:
        with np.load(INDEX_PATH) as data:
            _vectors = data["vectors"]
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            _chunks = json.load(f)
    except Exception as e:  # noqa: BLE001
        print("Index load error: %s" % e)
        _vectors, _chunks = None, None
        return False
    if len(_chunks) != _vectors.shape[0]:
        print("Warning: index/chunks length mismatch (%d vs %d) - rebuild the index."
              % (_vectors.shape[0], len(_chunks)))
        _vectors, _chunks = None, None
        return False
    return True


def retrieve_context(query: str, top_k: int = 6) -> list:
    """
    Retrieve the most relevant snippets for `query`.

    Returns a list of dicts shaped exactly like the old ZeroEntropy output:
        {"text": str, "score": float, "document_name": str, "source": dict}
    Returns [] on any failure so the caller can degrade gracefully.
    """
    co = _get_client()
    if co is None or not _load_index():
        return []

    q = (query or "").strip()[:4096]
    if not q:
        return []

    k = max(1, min(int(top_k), 128))

    # 1) Embed the query and take the nearest neighbours by cosine similarity.
    try:
        resp = co.embed(texts=[q], model=EMBED_MODEL,
                        input_type="search_query", embedding_types=["float"])
        qvec = np.asarray(resp.embeddings.float_[0], dtype="float32")
    except Exception as e:  # noqa: BLE001
        print("Cohere embed error: %s" % e)
        return []

    qnorm = np.linalg.norm(qvec)
    if qnorm < 1e-9:
        return []
    qvec = qvec / qnorm

    sims = _vectors @ qvec              # rows are already normalised
    pool = min(CANDIDATE_POOL, sims.shape[0])
    top_idx = np.argpartition(-sims, pool - 1)[:pool]
    top_idx = top_idx[np.argsort(-sims[top_idx])]

    candidates = [(int(i), float(sims[i])) for i in top_idx]

    # 2) Rerank the pool. If reranking fails, fall back to raw similarity order.
    try:
        ranked = co.rerank(
            model=RERANK_MODEL,
            query=q,
            documents=[_chunks[i]["text"] for i, _ in candidates],
            top_n=min(k, len(candidates)),
        )
        ordered = [(candidates[r.index][0], float(r.relevance_score))
                   for r in ranked.results]
    except Exception as e:  # noqa: BLE001
        print("Cohere rerank error (falling back to similarity order): %s" % e)
        ordered = candidates[:k]

    results = []
    for idx, score in ordered:
        chunk = _chunks[idx]
        doc_name = chunk.get("document_name", "")
        results.append({
            "text": chunk.get("text", ""),
            "score": score,
            "document_name": doc_name,
            "source": get_source_metadata(doc_name),
        })
    return results


def format_context_for_prompt(chunks: list, max_chars: int = 3000) -> str:
    """Format retrieved chunks into a context string for the LLM (unchanged)."""
    if not chunks:
        return ""

    context_parts = []
    total_chars = 0

    for i, chunk in enumerate(chunks, 1):
        text = chunk.get("text", "").strip()
        source = chunk.get("source", {})
        source_type = source.get("type", "unknown")

        # Determine label based on source type
        if source_type == "book":
            book_name = source.get("book", "Buku")
            label = f"BUKU: {book_name}"
        elif source_type == "summary":
            label = "AJARAN INTI"
        elif source_type == "video":
            label = "NGAJI GUS BAHA"
        else:
            label = "SUMBER"

        # Truncate if too long
        if len(text) > 800:
            text = text[:800] + "..."

        block = f"[{label} {i}]\n{text}"

        if total_chars + len(block) > max_chars:
            break

        context_parts.append(block)
        total_chars += len(block)

    return "\n\n".join(context_parts)


def get_unique_sources(chunks: list) -> list:
    """Extract unique sources from chunks for citation display (unchanged)."""
    seen_titles = set()
    unique_sources = []

    for chunk in chunks:
        source = chunk.get("source", {})
        title = source.get("title", "")
        source_type = source.get("type", "unknown")

        # Create unique key based on title (for books without URL)
        unique_key = title or source.get("url", "") or source.get("book", "")

        if unique_key and unique_key not in seen_titles:
            seen_titles.add(unique_key)

            # Build citation based on source type
            if source_type == "book":
                unique_sources.append({
                    "title": title,
                    "url": source.get("url"),  # Will be None for books
                    "author": source.get("author", ""),
                    "book": source.get("book", ""),
                    "pages": source.get("pages", ""),
                    "type": "book"
                })
            else:
                unique_sources.append({
                    "title": title,
                    "url": source.get("url", ""),
                    "channel": source.get("channel", ""),
                    "date": source.get("date", ""),
                    "type": source_type
                })

    return unique_sources