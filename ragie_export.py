"""
ragie_export.py — Download the original source files out of Ragie.ai.

Run this BEFORE ingest.py. It lists every document in your Ragie partition,
downloads each one's original uploaded file, and saves them into a local
folder (default: attached_assets/) so ingest.py can re-upload them to
ZeroEntropy.

Usage:
    export RAGIE_API_KEY="..."
    python ragie_export.py                       # exports partition "gus-baha"
    python ragie_export.py --partition default   # try a different partition
    python ragie_export.py --out attached_assets # change output folder
    python ragie_export.py --list-only           # just list, don't download

This uses the Ragie REST API directly (only the `requests` library), so it
needs no extra dependencies. It does NOT modify or delete anything in Ragie.
"""

import argparse
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests")

RAGIE_BASE_URL = "https://api.ragie.ai"


def list_documents(headers: dict, partition: str) -> list:
    """List all documents in the given Ragie partition (handles pagination)."""
    docs = []
    cursor = None
    while True:
        params = {"partition": partition, "page_size": 100}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(RAGIE_BASE_URL + "/documents",
                             headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        page = data.get("documents", []) or []
        docs.extend(page)
        # Cursor can live under "pagination" or at the top level depending on API version.
        pagination = data.get("pagination", {}) or {}
        cursor = pagination.get("next_cursor") or data.get("next_cursor")
        if not cursor or not page:
            break
    return docs


def safe_filename(name: str, doc_id: str, used: set) -> str:
    """Return a filesystem-safe, non-colliding filename."""
    name = (name or "").strip() or ("ragie_%s.bin" % doc_id[:8])
    name = os.path.basename(name)  # strip any path components
    if name in used:
        stem, ext = os.path.splitext(name)
        name = "%s_%s%s" % (stem, doc_id[:8], ext)
    used.add(name)
    return name


def download_source(headers: dict, doc_id: str, partition: str) -> bytes | None:
    """Download a document's original file; fall back to extracted content."""
    # Preferred: the original uploaded file.
    url = "%s/documents/%s/source" % (RAGIE_BASE_URL, doc_id)
    resp = requests.get(url, headers=headers,
                         params={"partition": partition}, timeout=60)
    if resp.status_code == 200 and resp.content:
        return resp.content
    # Fallback: extracted text content (for docs added as raw text, no file).
    url = "%s/documents/%s/content" % (RAGIE_BASE_URL, doc_id)
    resp = requests.get(url, headers=headers,
                         params={"partition": partition}, timeout=60)
    if resp.status_code == 200 and resp.content:
        return resp.content
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Export source files from Ragie.ai.")
    parser.add_argument("--partition", default="gus-baha",
                        help="Ragie partition to export (default: gus-baha)")
    parser.add_argument("--out", default="attached_assets",
                        help="Output folder for downloaded files (default: attached_assets)")
    parser.add_argument("--list-only", action="store_true",
                        help="List documents without downloading")
    args = parser.parse_args()

    api_key = os.environ.get("RAGIE_API_KEY")
    if not api_key:
        sys.exit("RAGIE_API_KEY is not set. Run: export RAGIE_API_KEY=...")

    headers = {"Authorization": "Bearer " + api_key}

    print("Listing documents in Ragie partition '%s'..." % args.partition)
    try:
        docs = list_documents(headers, args.partition)
    except requests.exceptions.RequestException as e:
        sys.exit("Failed to list documents from Ragie: %s" % e)

    if not docs:
        print("No documents found in partition '%s'." % args.partition)
        print("If you expected files here, try a different partition with "
              "--partition <name> (e.g. 'default').")
        return

    print("Found %d document(s):" % len(docs))
    for d in docs:
        print("  - %s  [%s]" % (d.get("name", "(unnamed)"), d.get("id", "?")))

    if args.list_only:
        print("\n[list-only] Nothing downloaded.")
        return

    os.makedirs(args.out, exist_ok=True)
    used_names = set()
    saved, failed = 0, 0

    print("\nDownloading source files into '%s/'..." % args.out)
    for d in docs:
        doc_id = d.get("id")
        if not doc_id:
            failed += 1
            continue
        fname = safe_filename(d.get("name", ""), doc_id, used_names)
        try:
            content = download_source(headers, doc_id, args.partition)
        except requests.exceptions.RequestException as e:
            print("  FAIL  %s  (%s)" % (fname, e))
            failed += 1
            continue
        if not content:
            print("  FAIL  %s  (no source or content available)" % fname)
            failed += 1
            continue
        with open(os.path.join(args.out, fname), "wb") as f:
            f.write(content)
        print("  OK    %s  (%d bytes)" % (fname, len(content)))
        saved += 1

    print("\nExport summary: %d saved, %d failed." % (saved, failed))
    if saved:
        print("Next: review the files in '%s/', then run ingest.py." % args.out)


if __name__ == "__main__":
    main()
