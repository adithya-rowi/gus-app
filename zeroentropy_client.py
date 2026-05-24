"""
ZeroEntropy Client - Retrieves relevant context from the Gus Baha knowledge base.

Drop-in replacement for ragie_client.py. Exposes the SAME three public functions
so generator.py only needs its import line changed:

    retrieve_context(query, top_k)        -> list[dict]
    format_context_for_prompt(chunks)     -> str
    get_unique_sources(chunks)            -> list[dict]

Retrieval uses ZeroEntropy's end-to-end search engine (top_snippets) with the
zerank-2 reranker. zembed-1 + zerank-2 are natively multilingual, so the old
Indonesian->English keyword-expansion / parallel-search hack from ragie_client.py
is no longer needed and has been removed. If retrieval quality ever regresses,
that is the first place to look.
"""

import os
import re

try:
    from zeroentropy import ZeroEntropy
except ImportError:  # pragma: no cover
    ZeroEntropy = None

# Collection populated by ingest.py
COLLECTION_NAME = os.environ.get("ZEROENTROPY_COLLECTION", "gus-baha")
# Reranker applied on top of retrieval. zerank-2 is the flagship; zerank-1-small is cheaper.
RERANKER = os.environ.get("ZEROENTROPY_RERANKER", "zerank-2")

# Source metadata for citations (unchanged from ragie_client.py).
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
    """Get source metadata for a document (unchanged from ragie_client.py)."""
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


# --- Lazy ZeroEntropy client -------------------------------------------------

_zclient = None


def _get_client():
    """Instantiate the ZeroEntropy client once, lazily. Returns None if unavailable."""
    global _zclient
    if _zclient is not None:
        return _zclient
    if ZeroEntropy is None:
        print("Warning: zeroentropy package not installed (pip install zeroentropy)")
        return None
    if not os.environ.get("ZEROENTROPY_API_KEY"):
        print("Warning: ZEROENTROPY_API_KEY not set")
        return None
    _zclient = ZeroEntropy()
    return _zclient


def retrieve_context(query: str, top_k: int = 6) -> list:
    """
    Retrieve the most relevant snippets from ZeroEntropy for `query`.

    Returns a list of dicts shaped exactly like the old Ragie output:
        {"text": str, "score": float, "document_name": str, "source": dict}
    Returns [] on any failure so the caller can degrade gracefully.
    """
    zclient = _get_client()
    if zclient is None:
        return []

    # top_snippets k must be between 1 and 128.
    k = max(1, min(int(top_k), 128))

    try:
        response = zclient.queries.top_snippets(
            collection_name=COLLECTION_NAME,
            query=query[:4096],  # API hard limit on query length
            k=k,
            reranker=RERANKER,
        )
    except Exception as e:  # noqa: BLE001
        print(f"ZeroEntropy retrieval error: {e}")
        return []

    results = []
    for r in getattr(response, "results", []):
        # `path` was set to the bare filename at ingest time; basename() is
        # defensive in case a path-style value slips through.
        doc_name = os.path.basename(getattr(r, "path", "") or "")
        results.append({
            "text": getattr(r, "content", "") or "",
            "score": getattr(r, "score", 0.0) or 0.0,
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
