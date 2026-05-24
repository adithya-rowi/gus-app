"""
ingest.py — One-time ingestion of the Gus Baha knowledge base into ZeroEntropy.

Replaces the Ragie.ai upload step. Run this ONCE (or again with --overwrite)
to populate the ZeroEntropy collection that zeroentropy_client.py queries.

Usage:
    export ZEROENTROPY_API_KEY="ze_..."
    python ingest.py                       # uploads everything in ./attached_assets
    python ingest.py --dir ./my_sources    # use a different source folder
    python ingest.py --overwrite           # re-upload + re-index existing docs
    python ingest.py --dry-run             # just list what WOULD be uploaded

Notes:
- .txt / .md files are uploaded as plain text.
- .pdf files are uploaded as base64; ZeroEntropy parses (and OCRs) them automatically.
- The ZeroEntropy document "path" is set to the bare filename, because
  zeroentropy_client.get_source_metadata() matches citations on the filename.
  Keep your original filenames intact.
"""

import argparse
import base64
import os
import sys
import time

try:
    from zeroentropy import ZeroEntropy
except ImportError:
    sys.exit("Missing dependency. Run:  pip install zeroentropy")

# ConflictError lives in the package; fall back gracefully across SDK versions.
try:
    from zeroentropy import ConflictError
except ImportError:  # pragma: no cover
    ConflictError = Exception

DEFAULT_COLLECTION = os.environ.get("ZEROENTROPY_COLLECTION", "gus-baha")
TEXT_EXTS = {".txt", ".md", ".markdown"}
PDF_EXTS = {".pdf"}


def find_source_files(root: str) -> list:
    """Recursively collect supported source files under `root`."""
    found = []
    for dirpath, _dirs, filenames in os.walk(root):
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext in TEXT_EXTS or ext in PDF_EXTS:
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def build_content(filepath: str):
    """Build the ZeroEntropy `content` payload for a file, or None if unusable."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in PDF_EXTS:
        with open(filepath, "rb") as f:
            data = f.read()
        if not data:
            return None
        return {"type": "auto", "base64_data": base64.b64encode(data).decode("utf-8")}
    # text / markdown
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()
    if not text:
        return None
    return {"type": "text", "text": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload the Gus Baha KB to ZeroEntropy.")
    parser.add_argument("--dir", default="attached_assets",
                        help="Folder containing source files (default: attached_assets)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION,
                        help="ZeroEntropy collection name (default: %s)" % DEFAULT_COLLECTION)
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-upload and re-index documents that already exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files without uploading")
    parser.add_argument("--no-wait", action="store_true",
                        help="Skip waiting for indexing to finish")
    args = parser.parse_args()

    if not os.environ.get("ZEROENTROPY_API_KEY"):
        sys.exit("ZEROENTROPY_API_KEY is not set. Run: export ZEROENTROPY_API_KEY=...")

    if not os.path.isdir(args.dir):
        sys.exit("Source folder not found: %s\n"
                 "Put your Gus Baha source files there, or pass --dir <path>." % args.dir)

    files = find_source_files(args.dir)
    if not files:
        sys.exit("No .txt / .md / .pdf files found under: %s" % args.dir)

    print("Found %d source file(s) under '%s':" % (len(files), args.dir))
    for fp in files:
        print("  - %s" % os.path.basename(fp))

    if args.dry_run:
        print("\n[dry-run] Nothing uploaded.")
        return

    zclient = ZeroEntropy()

    # 1) Ensure the collection exists.
    try:
        zclient.collections.add(collection_name=args.collection)
        print("\nCreated collection '%s'." % args.collection)
    except ConflictError:
        print("\nCollection '%s' already exists - reusing it." % args.collection)

    # 2) Upload each document.
    uploaded, skipped, failed = 0, 0, 0
    for fp in files:
        name = os.path.basename(fp)  # used as the ZeroEntropy `path`
        content = build_content(fp)
        if content is None:
            print("  SKIP  %s  (empty / unreadable)" % name)
            failed += 1
            continue
        try:
            zclient.documents.add(
                collection_name=args.collection,
                path=name,
                content=content,
                metadata={"filename": name},
                overwrite=args.overwrite,
            )
            print("  OK    %s" % name)
            uploaded += 1
        except ConflictError:
            print("  SKIP  %s  (already exists - use --overwrite to replace)" % name)
            skipped += 1
        except Exception as e:  # noqa: BLE001 - report and continue
            print("  FAIL  %s  (%s)" % (name, e))
            failed += 1

    print("\nUpload summary: %d uploaded, %d skipped, %d failed." % (uploaded, skipped, failed))

    if args.no_wait or uploaded == 0:
        return

    # 3) Wait for indexing to finish (indexing is asynchronous).
    print("\nWaiting for indexing to complete...")
    deadline = time.time() + 600  # 10-minute safety timeout
    while time.time() < deadline:
        try:
            status = zclient.status.get_status(collection_name=args.collection)
        except Exception as e:  # noqa: BLE001
            print("  (could not read status: %s) - give it a minute and query anyway." % e)
            return
        pending = status.num_parsing_documents + status.num_indexing_documents
        print("  indexed=%d pending=%d failed=%d"
              % (status.num_indexed_documents, pending, status.num_failed_documents))
        if pending == 0:
            print("\nDone. The collection is ready to query.")
            if status.num_failed_documents:
                print("WARNING: %d document(s) failed to index." % status.num_failed_documents)
            return
        time.sleep(5)

    print("\nStill indexing after 10 min - check the dashboard before querying.")


if __name__ == "__main__":
    main()
