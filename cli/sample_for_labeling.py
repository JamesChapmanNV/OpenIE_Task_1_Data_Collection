#!/usr/bin/env python
"""
Sample a balanced devset of already-scored previews for human labeling.

Output CSV schema (labels_devset.csv by default):
 seed_id,platform,url,title,snippet,author,date,score,decision,notes,gold_keep

- Fill 'gold_keep' with 1 (relevant) or 0 (not relevant) after manual review.
- 'notes' is optional free text for annotators.

Supports Postgres and Mongo backends via simple direct queries using env vars:
  POSTGRES_DSN, PREVIEWS_TABLE
  MONGO_URI, MONGO_DB

Usage:
  python cli/sample_for_labeling.py --backend postgres --n 80 --out labels_devset.csv
  python cli/sample_for_labeling.py --backend mongo --n 100
"""
import argparse, csv, os, random, math
from typing import List, Dict, Any

# --- PG
import psycopg2
from psycopg2.extras import RealDictCursor
# --- Mongo
import pymongo


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default=os.getenv("QUERY_BACKEND", "postgres"))
    ap.add_argument("--n", type=int, default=80, help="Total samples to export")
    ap.add_argument("--out", default="labels_devset.csv")
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


def _pg_fetch_scored(n: int) -> List[Dict[str, Any]]:
    dsn = os.getenv("POSTGRES_DSN", "host=localhost dbname=oie user=postgres password=postgres")
    table = os.getenv("PREVIEWS_TABLE", "previews")
    with psycopg2.connect(dsn) as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Pull a bigger pool for stratified sampling (e.g., 10× n)
        pool = n * 10
        cur.execute(f"""
            SELECT id, seed_id, platform, url, title, snippet, author, date, score, decision
            FROM {table}
            WHERE score IS NOT NULL
            ORDER BY RANDOM()
            LIMIT %s
        """, (pool,))
        return [dict(x) for x in cur.fetchall()]


def _mongo_fetch_scored(n: int) -> List[Dict[str, Any]]:
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    dbname = os.getenv("MONGO_DB", "oie")
    client = pymongo.MongoClient(uri)
    db = client[dbname]
    # Pull a bigger pool
    pool = n * 10
    cursor = db["previews"].aggregate([
        {"$match": {"score": {"$exists": True}}},
        {"$sample": {"size": pool}},
        {"$project": {
            "_id": 0,  # drop internal id for CSV simplicity
            "id": "$_id",
            "seed_id": 1, "platform": 1, "url": 1, "title": 1,
            "snippet": 1, "author": 1, "date": 1, "score": 1, "decision": 1
        }}
    ])
    return list(cursor)


def _stratify_by_score(rows: List[Dict[str, Any]], n: int, bins: int = 8) -> List[Dict[str, Any]]:
    # Place into bins by score; sample ~n/bins per bin to cover the range
    rows = [r for r in rows if isinstance(r.get("score"), (int, float))]
    if not rows:
        return []
    lo = min(r["score"] for r in rows)
    hi = max(r["score"] for r in rows)
    if hi <= lo:
        random.shuffle(rows)
        return rows[:n]

    span = hi - lo
    buckets = [[] for _ in range(bins)]
    for r in rows:
        idx = int((r["score"] - lo) / max(span, 1e-6) * (bins - 1))
        buckets[idx].append(r)

    per = max(1, n // bins)
    out = []
    for b in buckets:
        random.shuffle(b)
        out.extend(b[:per])
    # If short due to thin bins, top up randomly
    if len(out) < n:
        random.shuffle(rows)
        need = n - len(out)
        out.extend(rows[:need])
    return out[:n]


def main():
    args = parse_args()
    random.seed(args.seed)

    if args.backend.lower().startswith("pg") or args.backend.lower() == "postgres":
        pool = _pg_fetch_scored(args.n)
    else:
        pool = _mongo_fetch_scored(args.n)

    sample = _stratify_by_score(pool, args.n)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed_id","platform","url","title","snippet","author","date","score","decision","notes","gold_keep"])
        for r in sample:
            w.writerow([
                r.get("seed_id",""),
                r.get("platform",""),
                r.get("url",""),
                (r.get("title") or "")[:240],
                (r.get("snippet") or "")[:500],
                r.get("author",""),
                r.get("date",""),
                f'{float(r.get("score",0.0)):.3f}',
                r.get("decision",""),
                "",   # notes (to be filled by annotator)
                "",   # gold_keep (1 or 0 by annotator)
            ])
    print(f"Wrote {len(sample)} rows → {args.out}")
    print("Now open this CSV and label gold_keep as 1 (relevant) or 0 (not relevant).")


if __name__ == "__main__":
    main()

# Example usage:
#
# python cli/sample_for_labeling.py --backend postgres --n 100 --out labels_devset.csv
# (Annotate gold_keep: 1 = relevant / keep, 0 = not-relevant)
