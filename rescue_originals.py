"""
rescue_originals.py - Download the ORIGINAL source files out of ZeroEntropy.

The document records carry short-lived signed file_url tokens. This grabs the
real PDFs / .md / .txt files while those still work. Run this FIRST.

    export ZEROENTROPY_API_KEY="ze_..."
    python rescue_originals.py
"""

import os
import re
import sys
import time

import requests

BASE = os.environ.get("ZEROENTROPY_BASE_URL", "https://api.zeroentropy.dev/v1")
KEY = os.environ.get("ZEROENTROPY_API_KEY", "")
COLLECTION = os.environ.get("ZEROENTROPY_COLLECTION", "gus-baha")
OUT = "kb_export/originals"
HEADERS = {"Authorization": "Bearer %s" % KEY, "Content-Type": "application/json"}

if not KEY:
    sys.exit("ZEROENTROPY_API_KEY is not set.")

os.makedirs(OUT, exist_ok=True)

# 1) Page through every document record.
docs, cursor, seen = [], None, set()
while True:
    body = {"collection_name": COLLECTION, "limit": 100}
    if cursor:
        body["id_gt"] = cursor
    r = requests.post(BASE + "/documents/get-document-info-list",
                      json=body, headers=HEADERS, timeout=60)
    r.raise_for_status()
    batch = r.json().get("documents", [])
    fresh = [d for d in batch if d.get("id") not in seen]
    if not fresh:
        break
    for d in fresh:
        seen.add(d.get("id"))
    docs.extend(fresh)
    print("  ...%d documents listed" % len(docs))
    if len(batch) < 100:
        break
    cursor = batch[-1].get("id")
    if not cursor:
        break

print("\nFound %d document(s). Downloading originals...\n" % len(docs))

# 2) Download each original file.
ok = fail = 0
for d in docs:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_",
                  os.path.basename(d.get("path") or "") or "unnamed")
    url = d.get("file_url")
    dest = os.path.join(OUT, name)
    if not url:
        print("  NOURL %s" % name)
        fail += 1
        continue
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("  HAVE  %s" % name)
        ok += 1
        continue
    got = 0
    for attempt in range(3):
        try:
            resp = requests.get(url, headers={"Authorization": "Bearer %s" % KEY},
                                timeout=120, allow_redirects=True)
            if resp.status_code == 200 and resp.content:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                got = len(resp.content)
                break
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                print("  ERR   %s (%s)" % (name, e))
        time.sleep(2 ** attempt)
    if got:
        print("  OK    %-58s %8d bytes" % (name, got))
        ok += 1
    else:
        print("  FAIL  %s" % name)
        fail += 1

print("\nDownloaded %d, failed %d -> %s/" % (ok, fail, OUT))
if fail:
    print("Re-run to retry failures (already-downloaded files are skipped).")
print("\nNEXT: git add kb_export/ && git commit  -- so this can never be lost again.")