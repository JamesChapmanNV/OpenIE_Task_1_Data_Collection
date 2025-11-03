# OpenIE Task 1 — Data Collection (Neuroscience of Mental Health)

> **KDD Lab / Open Information Extraction (OIE) Testbed**  
> Foundation layer for discovering, normalizing, and scoring social-media content in the domain of mental-health neuroscience.

---

## Overview

This repository implements **Task 1: Data Collection** for a multi-task Open IE research system. It provides a **modular, reproducible pipeline** that:

1) defines **domain seeds** (problem statements & example phrases),  
2) generates **platform-specific search queries**,  
3) calls **platform APIs** (YouTube, Reddit),  
4) **normalizes** heterogeneous results to a common schema,  
5) **scores** previews with domain-tuned heuristics, and  
6) creates a **small labeled developer set** and **evaluates thresholds** (PR / ROC / F1) to select a production **KEEP** cutoff.

This data layer feeds downstream tasks such as information extraction (entities/relations), knowledge-graph building, ranking, and evaluation.

---

## Research Focus (reframed)

We target the **neuroscience of mental health** across public discourse and scientific context, including:

- Clinical vs **self-diagnosis** of **ASD, ADHD, AuDHD**  
- **Informal signs/symptoms** and **pop-psychology coping** strategies  
- **Neurodivergent identity & community** narratives  
- **Ethical debates** surrounding diagnostics & treatments  
- Emerging research on **DREADDs**, **genetic pathways**, **detection methods**, **diagnostic procedures**, and **pharmaceuticals** potentially affecting neurodivergent conditions

The pipeline seeks content that connects public conversation with contemporary scientific themes, surfacing high-value material that naïve keyword search would miss.

---

## Relationship to Other Tasks

| Task | What it does | How it uses Task 1 |
|---|---|---|
| **Task 1 – Data Collection (this repo)** | Seeds → queries → API fetch → normalize → score → label & calibrate | Produces high-quality, scored previews and labeled sets |
| **Task 2 – Ground Truth & Annotation** | Curates and scales labeled datasets | Bootstraps from `sample_for_labeling.py` and thresholding results |
| **Task 3 – Information Extraction** | NER, relation/claim extraction from posts/videos | Consumes normalized text/snippets/transcripts from Task 1 |
| **Task 4 – Knowledge Graphs** | Ontology integration of extracted facts | Links to Task 1 source URLs and metadata |
| **Task 5 – Ranking & Evaluation** | Learned ranking, metrics, and ablations | Uses Task 1 thresholds and labels for training/validation |

---

## Repository Structure


```bash
OpenIE_Task_1_Data_Collection
├── .env
├── .gitattributes
├── .github
├── .gitignore
├── bash_scratch.txt
├── cli
│   ├── eval_thresholds.py
│   ├── gen_queries.py
│   ├── sample_for_labeling.py
│   └── score_previews.py
├── dev_init.ps1
├── docker-compose.yml
├── documents_for_chat_context
├── OpenIE_Task_1_Data_Collection.ini
├── README.md
├── requirements.txt
├── scripts
│   └── demo_fetch_and_score.py
├── src
│   └── oie_search
│       ├── apis
│       │   ├── reddit.py
│       │   └── youtube.py
│       ├── config.py
│       ├── db
│       │   ├── mongo_init.js
│       │   ├── mongo_runner.py
│       │   ├── postgres_runner.py
│       │   ├── schema_postgres.sql
│       │   ├── seed_mongo.js
│       │   ├── seed_postgres.sql
│       │   └── __init__.py
│       ├── digestors.py
│       ├── docs
│       │   └── schema.md
│       ├── pipelines
│       │   ├── generate_queries.py
│       │   └── preview_intake.py
│       ├── prompts.py
│       ├── query_generator.py
│       ├── scoring.py
│       ├── utils
│       │   └── logging.py
│       └── __init__.py
└── tests
    ├── test_digestors.py
    ├── test_query_generator.py
    └── test_scoring.py
```





---

## Quick Start

### 0) Install & start services
```bash
pip install -r requirements.txt

# Start Postgres + Mongo locally
docker-compose up -d
# (Optional convenience on Windows)
powershell -ExecutionPolicy Bypass -File dev_init.ps1

```

### 1) Configure environment

Create .env (see Environment Variables below) with DB connection and API keys:

```bash
cp .env.example .env   # if you keep an example, else create manually
```

### 2) Generate queries from seeds

```bash
python cli/gen_queries.py --backend postgres --limit 10
```

### 3) Fetch previews (YouTube/Reddit), normalize & score

Use `scripts/demo_fetch_and_score.py` for a quick end-to-end smoke test, or integrate your own fetcher using `src/oie_search/apis/*`.

Persist fetched items to the previews table/collection, then:

```bash
python cli/score_previews.py --backend postgres --batch-size 200 --limit 5000 --dump-csv top_previews.csv
```

### 4) Build a small ground truth & calibrate threshold

```bash
python cli/sample_for_labeling.py --backend postgres --n 100 --out labels_devset.csv
# Manually label gold_keep as 1/0 in the CSV
python cli/eval_thresholds.py --labels labels_devset.csv --report thresholds_report.csv
# Update KEEP_MIN in scoring (or ini) per recommendation
```

## Components & Functions (what each file does)

### cli/

#### gen_queries.py

- parse_args() — CLI flags (--backend, --platforms, --limit, etc.).
- main() — loads backend via db.get_backend(), iterates seeds, calls query_generator.generate_queries_for_platform(), persists to search_queries.

#### score_previews.py

- parse_args(), _setup_logger() — CLI & logging.
- Batch loop: backend.list_unscored_previews() → digestors.normalize_preview(platform, raw) → scoring.score_preview(seed, normalized) → backend.save_preview_scores(rows).
- Optional per-seed leaderboard CSV via --dump-csv.

#### sample_for_labeling.py

- _pg_fetch_scored() / _mongo_fetch_scored() — pull a large random pool of scored previews.
- _stratify_by_score(rows, n, bins=8) — stratified sampling across score range for balanced labels.
- main() — writes labels_devset.csv with fields to annotate + placeholders (notes, gold_keep).

#### eval_thresholds.py

- _load(labels_csv) — reads score and gold_keep from CSV.
- _sweep_thresholds(y_score, y_true) — computes precision/recall/F1 across score thresholds.
- main() — prints ROC-AUC, PR-AUC, per-threshold metrics, and recommends KEEP_MIN (max F1; tie-break by precision → higher threshold); optionally writes thresholds_report.csv.

### src/oie_search/

#### config.py

- PLATFORMS_PRIORITY — ordering of platforms to target first.
- QueryGenConfig — pydantic config (include author flag, time windows, language priority).
- DEFAULT_QCFG — default query-generation config object.

#### query_generator.py

- normalize_text(s) — trims & collapses whitespace.
- top_k_terms(text, k=8) — lightweight term frequency extractor (drops digits/stopwords).
- build_phrase_candidates(seed) — uses seed title + first sentences from description/transcript/ocr/body; deduplicates to ~6 phrases.
- generate_queries_for_platform(seed, platform, config=None) — core per-platform templates (YouTube, Reddit, federated, podcasts, Threads/Twitter/X, generic); returns {precise, broad, hashtag_phrase}; can prepend from:<author> if configured.

#### prompts.py

- PREVIEW_ANALYZER_PROMPT — LLM rubric template for 0–100 “download interest” scoring (semantic/lexical/hashtag/media/recency/engagement) with a compact JSON output format (used in future learned-ranking extensions).

#### digestors.py

- normalize_preview(platform, raw) — converts native API items to a common schema:

```json
{
  "platform": "youtube|reddit|...",
  "url": "...",
  "title": "...",
  "snippet": "...",
  "author": "...",
  "date": "ISO-8601",
  "hashtags": ["..."],
  "engagement": {"views": "int?", "likes": "int?", "comments": "int?"},
  "media": {"has_video": "bool?", "duration_sec": "int?"},
  "raw": {"...": "..."}
}
```

- _normalize_youtube(raw) — merges search snippet + statistics + duration.
- _normalize_reddit(raw) — uses public or OAuth fields to populate normalized schema.
- featurize_preview(seed, normalized_preview) — optional shim (if you later split scoring into {features → score}).

#### scoring.py

- Constants: KEEP_MIN, TOPK_PER_SEED, weight caps (title/desc overlap, domain/novel terms, recency half-life, credibility, engagement caps).
- _quick_text_cosine(a,b) — TF-IDF cosine between short texts.
- score_preview(seed, preview) — heuristic ensemble: semantic similarity + lexical phrase hits + hashtag overlap + media/recency bonuses + engagement; returns {"score": float, "decision": "keep|consider|reject", "signals": {...}}.

### apis/

#### youtube.py

- search_videos(query, published_after=None, max_results=None, order="relevance")
  - Returns items that already combine snippet + statistics + content details (duration) and convenient fields (title, description, channelTitle, publishedAt, statistics, durationSec).

#### reddit.py

- search_posts(query, sort="relevance", limit=25, oauth=False)
  - Supports public JSON endpoint (no OAuth; needs REDDIT_USER_AGENT) or OAuth (set REDDIT_CLIENT_ID/SECRET/USERNAME/PASSWORD) for better reliability.

### db/

#### __init__.py

- BaseBackend interface; concrete PostgresBackend, MongoBackend.
- get_backend(name) — returns the requested backend (or by QUERY_BACKEND env).
- Methods expected by CLIs:
  - list_seeds(limit), save_generated_queries(rows),
  - list_unscored_previews(batch_size, limit), save_preview_scores(rows),
  - (optional) get_seed(seed_id) if you choose to implement a join.

- schema_postgres.sql — tables seeds_table, search_queries, previews, plus indexes/uniques.
- seed_postgres.sql — 10 seed topics spanning diagnosis vs self-diagnosis, identity/ethics, DREADDs, genetics, screening, trials; includes example queries and a sample preview row.
- postgres_runner.py / mongo_runner.py — examples for iterating seeds, generating queries, and persisting to search_queries.
- mongo_init.js / seed_mongo.js — MongoDB bootstrap (mirror Postgres seed content if you use Mongo first-class).

### pipelines/

- generate_queries.py — reads QUERY_BACKEND and dispatches to Postgres/Mongo query generation.
- preview_intake.py — example intake: normalize → score → return structured results (wires digestors + scoring).

### docs/schema.md

- Documents the normalized preview schema, key fields, and suggested DB column types.

### utils/logging.py

- Tiny logging helpers (formatters, levels) for consistent CLI output.

### scripts/

- demo_fetch_and_score.py — Minimal end-to-end test: runs a query through YouTube + Reddit clients, normalizes and scores previews, and prints top results (useful for sanity checks before full ingestion).

### tests/

- test_query_generator.py — validates phrase selection & platform templates.
- test_digestors.py — validates normalization shape and critical fields.
- test_scoring.py — validates scoring range, monotonicities of key signals.

## Environment Variables

Define in .env:

```bash
# --- Database ---
POSTGRES_DSN="host=localhost dbname=oie user=postgres password=postgres"
MONGO_URI="mongodb://localhost:27017"
MONGO_DB="oie"
SEEDS_TABLE=seeds_table
SEARCH_QUERIES_TABLE=search_queries
PREVIEWS_TABLE=previews
QUERY_BACKEND=postgres
LOG_LEVEL=INFO

# --- YouTube ---
YOUTUBE_API_KEY=YOUR_KEY
YOUTUBE_MAX_RESULTS=25

# --- Reddit ---
REDDIT_USER_AGENT="OpenIE/0.1 (by u/your_username)"
# OAuth (optional but recommended)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
```

Scoring weights / thresholds: see `OpenIE_Task_1_Data_Collection.ini` (or edit constants in `scoring.py`).

## Data Model (preview schema)

See `src/oie_search/docs/schema.md` for details. Core fields saved to DB/CSV:

```json
{
  "seed_id": 123,
  "platform": "youtube|reddit|...",
  "url": "...",
  "title": "...",
  "snippet": "...",
  "author": "...",
  "date": "ISO-8601",
  "hashtags": ["..."],
  "engagement": {"views": "int?", "likes": "int?", "comments": "int?"},
  "media": {"has_video": "bool?", "duration_sec": "int?"},
  "score": "0..100",
  "decision": "keep|consider|reject",
  "signals": {"...": "..."}
}
```

## Ground Truth & Thresholds (recommended practice)

Run scoring to populate score.

Export a balanced dev set across score bins:

```bash
python cli/sample_for_labeling.py --backend postgres --n 100 --out labels_devset.csv
```

Manually label `gold_keep` ∈ {0,1}.

Evaluate thresholds & select KEEP_MIN:

```bash
python cli/eval_thresholds.py --labels labels_devset.csv --report thresholds_report.csv
```

Update KEEP_MIN (in `scoring.py` or the ini file) based on the recommended threshold.

## Troubleshooting

- No API results — verify keys in .env and internet access; for Reddit public search you must set `REDDIT_USER_AGENT`.
- Cannot save scores — ensure `schema_postgres.sql` has been applied; tables/collections exist and match field names.
- Encoding issues — store text as UTF-8; truncate overly long fields at ingestion (see `digestors.normalize_preview`).

## Roadmap

- Add Mastodon/BlueSky API clients & normalizers.
- Integrate LLM re-ranking using `prompts.PREVIEW_ANALYZER_PROMPT`.
- Expand annotation schema beyond binary keep/not-keep.
- Move from heuristics → learned ranking (Task 5).
