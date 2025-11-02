# OpenIE Task 1 — Storage Schema

This doc defines **canonical fields** for both Postgres tables and Mongo collections. When fields are optional, keep them nullable (SQL) or omit (Mongo).

## 1. seeds
Canonical “source” exemplars curated by the team.

| Field | Type (SQL) | Type (Mongo) | Notes |
|---|---|---|---|
| seed_id | BIGSERIAL PK | NumberLong | Primary key |
| seed_topic | TEXT | String | E.g., "Mental Health + Neuroscience" |
| title | TEXT | String | Short label |
| description | TEXT | String | Free text |
| transcript | TEXT | String/null | Optional |
| ocr | TEXT | String/null | Optional |
| body | TEXT | String/null | Optional |
| created_at | TIMESTAMPTZ | Date | Default now() |

## 2. platform_queries
Per-platform query strings generated from a seed.

| Field | Type (SQL) | Type (Mongo) | Notes |
|---|---|---|---|
| pq_id | BIGSERIAL PK | ObjectId | |
| seed_id | BIGINT FK → seeds(seed_id) | NumberLong | |
| platform | TEXT | String | e.g., `youtube`, `reddit`, `tiktok`, `bsky` |
| variant | TEXT | String | e.g., `exact`, `hashtag`, `broad` |
| query | TEXT | String | The actual platform query string |
| created_at | TIMESTAMPTZ | Date | Default now() |

Index: `(seed_id, platform)`.

## 3. previews
Raw “preview” items returned by search/crawl, normalized to a common shape.

| Field | Type (SQL) | Type (Mongo) | Notes |
|---|---|---|---|
| preview_id | BIGSERIAL PK | ObjectId | |
| seed_id | BIGINT FK | NumberLong | Link back for evaluation |
| platform | TEXT | String | |
| post_id | TEXT | String | Platform’s native ID |
| url | TEXT | String | |
| title | TEXT | String | |
| description | TEXT | String | Channel/caption/snippet |
| author | TEXT | String | Channel/user handle |
| timestamp | TIMESTAMPTZ | Date | Post/video publish time if known |
| engagement | JSONB | Object | {views, likes, comments} (optional) |
| raw | JSONB | Object | Raw preview blob (optional) |
| created_at | TIMESTAMPTZ | Date | Default now() |

Indexes: `(seed_id)`, `(platform, post_id)` unique where possible.

## 4. preview_scores
Scored relevance (and explanation) for each preview.

| Field | Type (SQL) | Type (Mongo) | Notes |
|---|---|---|---|
| ps_id | BIGSERIAL PK | ObjectId | |
| preview_id | BIGINT FK → previews | ObjectId/NumberLong | |
| seed_id | BIGINT | NumberLong | |
| platform | TEXT | String | |
| score | NUMERIC(6,3) | Double | Composite score 0–1 (or 0–100) |
| features | JSONB | Object | Feature vector used |
| reasons | TEXT | String | Brief explanation |
| created_at | TIMESTAMPTZ | Date | Default now() |

Unique index: `(preview_id)`.

## Governance Options
- **IDs-only mode**: skip `raw` and long text fields for redistributable sets.
- **Safety filters**: soft rules before persisting: blocked terms, minors, SFW-only, etc.
