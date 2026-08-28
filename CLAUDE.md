# CLAUDE.md — gus-app

Guidance for Claude Code working in this repository.

## What this is

**Gus Ahab** (gusahab.com) — an AI Islamic Q&A chatbot inspired by the warm,
humble, story-driven teaching style of Gus Baha. It is an **educational
chatbot, NOT a fatwa service**. The persona must never claim to be the real
Gus Baha and must never invent personal details about him.

Stack: Python **Flask** backend · **DeepSeek** LLM (`deepseek-chat`, via the
OpenAI SDK pointed at `api.deepseek.com`) · **Cohere** (`embed-multilingual-v3.0`
+ `rerank-v3.5`) with a repo-local index for RAG retrieval · vanilla
HTML/CSS/JS frontend (mobile-first).

## Request flow

1. `POST /chat` (main.py) receives `{message, history}`.
2. `generate_response()` (generator.py):
   - `detect_language()` picks `id` or `en`.
   - Selects the matching system prompt + few-shot examples.
  - Retrieves RAG context via `retrieval.retrieve_context()`.
   - Builds messages: system prompt + few-shots + recent history + user
     message (with retrieved context inlined).
   - Calls DeepSeek, strips markdown, runs off-topic "redirect" detection.
   - Returns `{response, sources, language, context_used, ...}`.
3. main.py returns the JSON to the frontend.

## Key files

- `main.py` — Flask app and routes (`/`, `/chat`, `/health`).
- `generator.py` — core logic: language detection, prompt assembly, DeepSeek
  call, RAG orchestration. Holds the English prompt/few-shots inline.
- `persona.py` — `SYSTEM_PROMPT` and `FEW_SHOTS` (Indonesian).
- `retrieval.py` — Cohere-backed retrieval over the repo-local index. Citation
  metadata lives in the `SOURCES` dict + `SOURCE_PATTERNS`.
- `critic.py` — optional tone-validator (`validate_response`). **Currently
  dormant** — not wired into the request flow.
- `build_index.py` — builds the local search index from `kb_export/originals/`.
- `ragie_export.py` — one-off tool to pull source files out of the legacy
  Ragie.ai account. Transitional; remove after migration is verified.
- `ragie_client.py` — legacy RAG client (Ragie.ai), retained only for historical
  reference.
- `static/`, `templates/` — frontend assets.

## Environment variables

- `DEEPSEEK_API_KEY` — required (LLM).
- `COHERE_API_KEY` — required (RAG).
- `KB_INDEX_PATH` — optional, default `kb_index.npz`.
- `KB_CHUNKS_PATH` — optional, default `kb_chunks.json`.
- `COHERE_EMBED_MODEL` — optional, default `embed-multilingual-v3.0`.
- `COHERE_RERANK_MODEL` — optional, default `rerank-v3.5`.
- `KB_CANDIDATE_POOL` — optional, default `40`.
- `RAGIE_API_KEY` — legacy; only used by `ragie_export.py`.
- `PORT` — optional, default `5000`.

## Running

```bash
# Dev
python main.py
# Prod (this is what .replit uses)
gunicorn --bind 0.0.0.0:5000 main:app
```

## RAG / knowledge base

- Cohere embeddings and reranking run over the repo-local index files.
- Knowledge base source files live in `kb_export/originals/`.
- Rebuild the index with `python build_index.py`.
- Citations are matched by **document filename** → keep filenames stable and
  meaningful, since `get_source_metadata()` keys off them.

## Conventions & gotchas

- `retrieval.py` MUST keep its three-function contract:
  `retrieve_context`, `format_context_for_prompt`, `get_unique_sources`.
  `generator.py` depends on the exact shapes. Each retrieved chunk is a dict:
  `{text, score, document_name, source}`.
- Responses are intentionally short (5–8 sentences); markdown `*`/`_` is
  stripped before returning.
- `attached_assets/` is gitignored — source files are NOT in the repo.
- Two languages throughout: always handle both `id` and `en`.

## Do not

- Do not commit API keys or `.env`.
- Do not change the `retrieve_context` return shape.
- Do not let the persona claim to be the real Gus Baha or give a fatwa.
