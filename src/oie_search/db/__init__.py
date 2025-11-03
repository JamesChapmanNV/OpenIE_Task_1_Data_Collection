"""
Database backend abstraction for OpenIE Task 1 Data Collection.

This module provides a unified interface for Postgres and MongoDB backends.
Each backend implements:
    - list_seeds(limit)
    - save_generated_queries(rows)
    - list_unscored_previews(batch_size, limit)
    - save_preview_scores(rows)
"""

import os
from typing import Iterable, Dict, Any, List, Generator
import psycopg2
import pymongo
from psycopg2.extras import RealDictCursor

# ---------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------
class BaseBackend:
    """Defines the minimal interface expected by CLI scripts."""

    def list_seeds(self, limit: int = 100) -> Generator[Dict[str, Any], None, None]:
        raise NotImplementedError

    def save_generated_queries(self, rows: Iterable[Dict[str, Any]]):
        raise NotImplementedError

    def list_unscored_previews(
        self, batch_size: int = 100, limit: int = 1000
    ) -> Generator[Dict[str, Any], None, None]:
        raise NotImplementedError

    def save_preview_scores(self, rows: Iterable[Dict[str, Any]]):
        raise NotImplementedError


# ---------------------------------------------------------------------
# Postgres implementation
# ---------------------------------------------------------------------
class PostgresBackend(BaseBackend):
    def __init__(self):
        dsn = os.getenv("POSTGRES_DSN", "host=localhost dbname=oie user=postgres password=postgres")
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True
        self.seeds_table = os.getenv("SEEDS_TABLE", "seeds_table")
        self.queries_table = os.getenv("SEARCH_QUERIES_TABLE", "search_queries")
        self.previews_table = os.getenv("PREVIEWS_TABLE", "previews")

    def list_seeds(self, limit: int = 100):
        q = f"SELECT * FROM {self.seeds_table} ORDER BY seed_id ASC LIMIT %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, (limit,))
            for row in cur.fetchall():
                yield dict(row)

    def save_generated_queries(self, rows: Iterable[Dict[str, Any]]):
        with self.conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    f"""INSERT INTO {self.queries_table}
                    (seed_id, platform, precise, broad, hashtag_phrase)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING;""",
                    (r["seed_id"], r["platform"], r["precise"], r["broad"], r["hashtag_phrase"]),
                )

    def list_unscored_previews(self, batch_size: int = 100, limit: int = 1000):
        q = f"""
            SELECT * FROM {self.previews_table}
            WHERE score IS NULL
            ORDER BY id ASC
            LIMIT %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, (limit,))
            batch = []
            for row in cur.fetchall():
                batch.append(dict(row))
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

    def save_preview_scores(self, rows: Iterable[Dict[str, Any]]):
        with self.conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    f"""UPDATE {self.previews_table}
                    SET score=%s, decision=%s, signals=%s
                    WHERE id=%s;""",
                    (r["score"], r["decision"], str(r.get("signals", {})), r["id"]),
                )


# ---------------------------------------------------------------------
# MongoDB implementation
# ---------------------------------------------------------------------
class MongoBackend(BaseBackend):
    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        dbname = os.getenv("MONGO_DB", "oie")
        client = pymongo.MongoClient(uri)
        self.db = client[dbname]

    def list_seeds(self, limit: int = 100):
        for doc in self.db["seeds"].find().limit(limit):
            yield doc

    def save_generated_queries(self, rows: Iterable[Dict[str, Any]]):
        if not rows:
            return
        self.db["search_queries"].insert_many(list(rows))

    def list_unscored_previews(self, batch_size: int = 100, limit: int = 1000):
        cursor = self.db["previews"].find({"score": {"$exists": False}}).limit(limit)
        batch = []
        for doc in cursor:
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def save_preview_scores(self, rows: Iterable[Dict[str, Any]]):
        for r in rows:
            self.db["previews"].update_one(
                {"_id": r["_id"]},
                {"$set": {"score": r["score"], "decision": r["decision"], "signals": r.get("signals", {})}},
            )


# ---------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------
def get_backend(name: str = None) -> BaseBackend:
    """
    Factory that returns the requested backend instance.

    Parameters
    ----------
    name : str
        Either 'postgres' or 'mongo'. Defaults to the env var QUERY_BACKEND
        or 'postgres' if not set.
    """
    name = name or os.getenv("QUERY_BACKEND", "postgres").lower()
    if name.startswith("pg") or name == "postgres":
        return PostgresBackend()
    elif name.startswith("mongo"):
        return MongoBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")
