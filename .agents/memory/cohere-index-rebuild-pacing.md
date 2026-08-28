---
name: Cohere index rebuild pacing
description: Rate-limit constraint observed while embedding the full knowledge base with Cohere.
---

Full knowledge-base rebuilds can exceed Cohere trial token-per-minute limits even when each request stays within the per-call batch limit. Pace embedding batches or use retry/backoff when rebuilding the complete index.

**Why:** A 522-chunk build reached the API's token-per-minute ceiling after several successful batches.

**How to apply:** When regenerating the complete local index with a trial-rate key, allow time between embedding batches or wrap the unchanged builder with retry/backoff.