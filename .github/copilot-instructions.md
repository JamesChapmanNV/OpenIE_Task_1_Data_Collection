# Copilot instructions — OpenIE Task 1: Data Collection

Purpose: Help agents work productively in this repo by outlining architecture, key entry points, and project-specific conventions.

Big picture
- Pipeline: seeds → query generation → platform APIs (YouTube/Reddit) → normalize previews → heuristic scoring → optional DB persistence and threshold calibration.
- Goal: surface high-value social content connecting public discourse to mental-health neuroscience, feeding downstream extraction and evaluation tasks.

Where things live (key modules)
- `src/oie_search/query_generator.py`
  - `build_phrase_candidates(seed)` picks ~6 representative phrases from title/description/transcript/ocr/body.
  - `generate_queries_for_platform(seed, platform, config=None)` returns `{precise,broad,hashtag_phrase}` with per-platform templates; can prepend `from:<author>` when `include_author=True`.
- `src/oie_search/apis/{youtube.py, reddit.py}`
  - `search_videos(query, published_after=None, max_results=None)` enriches items with `statistics` and `durationSec`.
  - `search_posts(query, sort="relevance", limit=25, oauth=False)` supports public JSON (requires `REDDIT_USER_AGENT`) or OAuth.
- `src/oie_search/digestors.py`
  - `normalize_preview(platform, raw)` → common dict schema: `platform,url,title,snippet,author,date,hashtags,engagement(media),raw`.
  - `featurize_preview(seed, normalized)` currently a thin passthrough shim.
- `src/oie_search/scoring.py`
  - `_quick_text_cosine(a,b)` TF‑IDF cosine for short texts.
  - `score_preview(seed, preview)` → `{score:int 0..100, decision:keep|consider|reject, signals:{...}}` using semantic similarity, lexical/hashtag overlap, media/freshness/engagement.
- `src/oie_search/pipelines/preview_intake.py` ties normalization + scoring: `process_previews(platform, seed, raw_previews)`.
- `src/oie_search/db/__init__.py` provides `get_backend('postgres'|'mongo')` with minimal methods for seeds, queries, previews.

Typical dev flows (minimal examples)
- End‑to‑end sanity check: see `scripts/demo_fetch_and_score.py` (YouTube+Reddit → normalize → score → print top results).
- Generate queries from Postgres or Mongo directly: use `src/oie_search/db/postgres_runner.py::generate_queries_postgres` or `db/mongo_runner.py::generate_queries_mongo`.
- Services: `docker-compose.yml` brings up Postgres 16 and Mongo 7; set `.env` for API keys and DB URIs. Python deps in `requirements.txt`.

Conventions and data shapes
- Normalized preview schema (digestors output) is the contract for scoring; see `src/oie_search/docs/schema.md` for broader storage schema (naming may differ slightly from in‑code fields).
- Seeds are dicts with at least `title`, optional `description/transcript/ocr/body`, and `metadata.hashtags` plus `important_phrases` for better lexical features.
- Query templates prefer quoted phrases for precision and token lists for breadth; federated platforms lean on hashtags.

Integration points & env
- YouTube: `YOUTUBE_API_KEY` (and optional `YOUTUBE_MAX_RESULTS`).
- Reddit: set `REDDIT_USER_AGENT`; optional OAuth (`REDDIT_CLIENT_ID/SECRET/USERNAME/PASSWORD`).
- DB: Postgres `POSTGRES_DSN` (default dsn in code if unset), or Mongo `MONGO_URI`/`MONGO_DB`. Backend selection via `QUERY_BACKEND`.

Gotchas (repo‑specific)
- Version skew: some `cli/` scripts and `tests/` reference older APIs (e.g., `digest_youtube_preview`, `featurize_preview` in scoring). Prefer using `pipelines/` and `scripts/demo_fetch_and_score.py` as current references.
- `scoring.py` imports `get_score_float/get_score_int` from `config.py`, but those helpers are currently commented out. Until wired up, constants effectively come from defaults in `scoring.py`; if you see import errors, re‑enable or inline defaults.
- Naming between `docs/schema.md` and in‑code normalized dict differs (e.g., `post_id` vs `url/title/snippet`). Treat digestors’ schema as source‑of‑truth for scoring code.

Quick usage sketch
- Build queries → fetch: `queries = generate_queries_for_platform(seed, 'youtube'); items = search_videos(queries['precise'])`.
- Then: `pv = normalize_preview('youtube', items[0]); out = score_preview(seed, pv)`.

If you need more, start from the functions listed above and follow call sites in `pipelines/`.
