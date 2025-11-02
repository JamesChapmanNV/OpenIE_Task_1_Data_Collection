#!/usr/bin/env python
# import sys, os
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# from oie_search.pipelines.generate_queries import main

import argparse, os
from oie_search.utils.logging import setup_logger
from oie_search.config import get_app
from oie_search.pipelines.generate_queries import generate_queries_for_seed
from oie_search.db import get_backend  # assume you expose a factory

def parse_args():
    ap = argparse.ArgumentParser("Generate platform queries from seeds")
    ap.add_argument("--backend", default=os.getenv("QUERY_BACKEND", get_app("QUERY_BACKEND","postgres")))
    ap.add_argument("--platforms", default=get_app("PLATFORMS","youtube,reddit"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log-level", default="INFO")
    return ap.parse_args()

def main():
    args = parse_args()
    log = setup_logger(level=args.log_level)
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    db = get_backend(args.backend)

    count = 0
    for seed in db.list_seeds(limit=args.limit):
        rows = generate_queries_for_seed(seed, platforms=platforms)
        count += len(rows)
        if not args.dry_run:
            db.save_generated_queries(rows)
    log.info(f"Seeds processed: {min(args.limit or 10**9, db.last_seed_count)}; queries generated: {count}; dry_run={args.dry_run}")

if __name__ == "__main__":
    main()
