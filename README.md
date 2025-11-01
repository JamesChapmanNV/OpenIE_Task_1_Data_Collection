# OpenIE_Task_1_Data_Collection

# OIE Social Search Starter

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # or create .env from template in root


Make both scripts executable:
chmod +x cli/gen_queries.py
chmod +x cli/score_previews.py

Generate platform queries from seeds
# select backend via env (postgres or mongo)
export QUERY_BACKEND=postgres
python cli/gen_queries.py

Score preview results

Prepare two JSON files:

seed.json (single seed)

previews.json (array of raw preview items from a platform API/UI export)
python cli/score_previews.py youtube seed.json previews.json > scored.json

he pipeline normalizes previews, computes scores, and emits keep/consider/reject with signals.


---

## Where things go (direct answer to your question)

- **Postgres/Mongo code:** `src/oie_search/db/postgres_runner.py` and `src/oie_search/db/mongo_runner.py`.  
- **Preview-analyzer prompt:** `src/oie_search/prompts.py`.  
- **Search-result digestor (normalizers):** `src/oie_search/digestors.py`.  
- **Preview scoring rubric:** `src/oie_search/scoring.py`.  
- **Pipelines:** `src/oie_search/pipelines/generate_queries.py` (build queries) and `src/oie_search/pipelines/preview_intake.py` (normalize + score).  
- **CLI entry points:** `cli/gen_queries.py` and `cli/score_previews.py`.  

If you paste these files in as-is, you’ll be able to (a) generate queries into your DB and (b) score preview results offline. When you’re ready, I can add per-platform API callers and a Smart Crawler loop that uses the scores to decide what to download next.

