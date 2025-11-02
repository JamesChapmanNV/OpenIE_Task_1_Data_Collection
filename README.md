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
```bash
OpenIE_Task_1_Data_Collection
├── .env
├── .gitattributes
├── .gitignore
├── README.md
├── requirements.txt
├── dev_init.ps1
├── docker-compose.yml
├── OpenIE_Task_1_Data_Collection.ini
├── cli
│   ├── gen_queries.py
│   └── score_previews.py
└── src
    └── oie_search
        ├── config.py
        ├── db
        │   ├── mongo_init.js
        │   ├── mongo_runner.py
        │   ├── postgres_runner.py
        │   ├── schema_postgres.sql
        │   ├── seed_mongo.js
        │   ├── seed_postgres.sql
        │   └── __init__.py
        ├── digestors.py
        ├── pipelines
        │   ├── generate_queries.py
        │   └── preview_intake.py
        ├── prompts.py
        ├── query_generator.py
        ├── scoring.py
        └── __init__.py
```



