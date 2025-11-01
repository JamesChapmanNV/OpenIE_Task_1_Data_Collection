# OpenIE_Task_1_Data_Collection

# OIE Social Search Starter

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # or create .env from template in root
```

Make both scripts executable:
```bash
chmod +x cli/gen_queries.py
chmod +x cli/score_previews.py
```

Generate platform queries from seeds
(select backend via env (postgres or mongo))
```bash
export QUERY_BACKEND=postgres
python cli/gen_queries.py
```

Score preview results

Prepare two JSON files:

seed.json (single seed)

previews.json (array of raw preview items from a platform API/UI export)
```bash
python cli/score_previews.py youtube seed.json previews.json > scored.json
```
The pipeline normalizes previews, computes scores, and emits keep/consider/reject with signals.



