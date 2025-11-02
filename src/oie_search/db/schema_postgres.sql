-- PostgreSQL schema for database: openie

-- 3.1 SEEDS
CREATE TABLE IF NOT EXISTS public.seeds_table (
  seed_id         BIGSERIAL PRIMARY KEY,
  seed_topic      TEXT,                 -- e.g., "Mental Health + Neuroscience"
  title           TEXT,
  description     TEXT,
  transcript      TEXT,                 -- ASR text if available
  ocr             TEXT,                 -- OCR text if available
  body            TEXT,                 -- fallback long text
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_seeds_topic ON public.seeds_table(seed_topic);

-- 3.2 GENERATED SEARCH QUERIES
CREATE TABLE IF NOT EXISTS public.search_queries (
  query_id        BIGSERIAL PRIMARY KEY,
  seed_id         BIGINT REFERENCES public.seeds_table(seed_id) ON DELETE CASCADE,
  platform        TEXT NOT NULL,        -- 'youtube', 'reddit', 'x', 'spotify', ...
  query_text      TEXT NOT NULL,
  gen_meta        JSONB DEFAULT '{}'::jsonb,  -- store prompt/version/weights
  created_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (seed_id, platform, query_text)
);

CREATE INDEX IF NOT EXISTS idx_queries_seed ON public.search_queries(seed_id);
CREATE INDEX IF NOT EXISTS idx_queries_platform ON public.search_queries(platform);

-- 3.3 (Optional) PREVIEWS table if you store previews in Postgres
CREATE TABLE IF NOT EXISTS public.previews (
  preview_id      BIGSERIAL PRIMARY KEY,
  seed_id         BIGINT REFERENCES public.seeds_table(seed_id) ON DELETE SET NULL,
  platform        TEXT NOT NULL,
  url             TEXT NOT NULL,
  title           TEXT,
  snippet         TEXT,
  author          TEXT,
  published_at    TIMESTAMPTZ,
  raw_meta        JSONB DEFAULT '{}'::jsonb,
  score           DOUBLE PRECISION,     -- heuristic score (scoring.py)
  created_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE (platform, url)
);

CREATE INDEX IF NOT EXISTS idx_previews_platform ON public.previews(platform);
CREATE INDEX IF NOT EXISTS idx_previews_seed ON public.previews(seed_id);
CREATE INDEX IF NOT EXISTS idx_previews_score ON public.previews(score);
