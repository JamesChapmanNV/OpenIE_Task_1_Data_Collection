#!/usr/bin/env python
"""
Score previews CLI

This version wires:
  - normalize_preview(platform, raw) from oie_search.digestors
  - score_preview(seed, preview) from oie_search.scoring
and supports both Postgres and Mongo backends via oie_search.db.get_backend().

It:
  • pulls unscored previews in batches
  • builds/recovers a minimal seed dict (from the record, or via backend if available)
  • normalizes each raw preview to a common schema
  • scores each preview (0–100) and writes score/decision/signals back
  • optionally writes a per-seed leaderboard CSV (top-K kept/considered)

Assumptions:
  - backend.list_unscored_previews(batch_size, limit) yields lists of preview records
  - backend.save_preview_scores(rows) accepts rows with {id/_id, score, decision, signals}
  - Preview records contain at least: platform, and either a "raw" blob or already-flat fields.
  - If seed text is not embedded in the record, we try backend.get_seed(seed_id) when available.

Environment / args:
  --backend (defaults to $QUERY_BACKEND or "postgres")
  --batch-size
  --limit
  --log-level
  --dump-csv (optional path)
"""

import argparse
import csv
import logging
import os
from collections import defaultdict
from typing import Any, Dict, Optional

from oie_search.db import get_backend
from oie_search.digestors import normalize_preview
from oie_search.scoring import score_preview, KEEP_MIN, TOPK_PER_SEED


# ------------------------------ CLI Args ------------------------------------ #

def parse_args():
    ap = argparse.ArgumentParser("Score previews")
    ap.add_argument("--backend", default=os.getenv("QUERY_BACKEND", "postgres"))
    ap.add_argument("--batch-size", type=int, default=int(os.getenv("BATCH_SIZE", "100")))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    ap.add_argument("--dump-csv", default=None, help="Optional: path to write a per-seed leaderboard CSV")
    return ap.parse_args()


# ---------------------------- Helper functions ------------------------------ #

def _setup_logger(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("score_previews")
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def _preview_record_id(rec: Dict[str, Any]):
    """Return the identifier used by the backend (Postgres id or Mongo _id)."""
    return rec.get("id", rec.get("_id"))


def _extract_seed_from_record(rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Build a minimal seed dict from fields embedded in the preview record.
    This is preferred to an extra DB fetch when present.
    """
    seed_blob = rec.get("seed")
    if isinstance(seed_blob, dict):
        # Already embedded
        return seed_blob

    # Sometimes flattened under specific keys (seed_title, seed_description, etc.)
    if any(k in rec for k in ("seed_title", "seed_description", "seed_transcript", "seed_ocr", "seed_body")):
        return {
            "seed_id": rec.get("seed_id"),
            "title": rec.get("seed_title"),
            "description": rec.get("seed_description"),
            "transcript": rec.get("seed_transcript"),
            "ocr": rec.get("seed_ocr"),
            "body": rec.get("seed_body"),
        }

    # Fallback: if the preview itself includes enough seed-like context (rare)
    return None


def _fetch_seed_from_backend(db, seed_id) -> Optional[Dict[str, Any]]:
    """
    Best-effort: only call if backend exposes get_seed.
    """
    if not seed_id:
        return None
    get_seed = getattr(db, "get_seed", None)
    if callable(get_seed):
        try:
            return get_seed(seed_id)
        except Exception:
            return None
    return None


def _normalize_from_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single preview record:
      - use rec["raw"] if present, else treat rec as already-flat
      - platform = rec["platform"] or "unknown"
    """
    platform = (rec.get("platform") or "unknown").lower()
    raw = rec.get("raw") or rec
    return normalize_preview(platform, raw)


# --------------------------------- Main ------------------------------------- #

def main():
    args = parse_args()
    log = _setup_logger(args.log_level)
    db = get_backend(args.backend)

    total_scored = 0
    per_seed = defaultdict(list)  # seed_id -> list[(score, normalized_preview)]

    # Iterate batches from backend
    for batch in db.list_unscored_previews(batch_size=args.batch_size, limit=args.limit):
        out_rows = []

        for rec in batch:
            # Resolve/construct seed dict
            seed = _extract_seed_from_record(rec)
            if seed is None:
                seed = _fetch_seed_from_backend(db, rec.get("seed_id"))

            # As a final fallback, create a minimal seed to keep the pipeline flowing.
            # (Heuristics in score_preview can still work with title-only.)
            if seed is None:
                seed = {
                    "seed_id": rec.get("seed_id"),
                    "title": rec.get("seed_title") or "",    # may be None
                    "description": rec.get("seed_description") or "",
                    "transcript": rec.get("seed_transcript") or "",
                    "ocr": rec.get("seed_ocr") or "",
                    "body": rec.get("seed_body") or "",
                }

            # Normalize preview and score
            normalized = _normalize_from_record(rec)
            scored = score_preview(seed, normalized)  # -> {"score": float, "decision": str, "signals": {...}}

            out_rows.append({
                "id": _preview_record_id(rec),
                "score": float(scored["score"]),
                "decision": scored["decision"],
                "signals": scored.get("signals", {}),
            })
            total_scored += 1

            # collect for leaderboard if meets min
            if args.dump_csv and float(scored["score"]) >= KEEP_MIN:
                per_seed[seed.get("seed_id")].append((float(scored["score"]), normalized))

        # Persist this batch of scores
        if out_rows:
            try:
                db.save_preview_scores(out_rows)
            except Exception as e:
                log.error(f"Failed to save a batch of {len(out_rows)} scores: {e}")

    log.info(f"Scored {total_scored} previews.")

    # Optional: write per-seed leaderboard CSV
    if args.dump_csv:
        try:
            with open(args.dump_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["seed_id", "platform", "score", "url", "title", "author", "date"])
                for sid, items in per_seed.items():
                    # sort high → low, cap at TOPK_PER_SEED
                    for s, pv in sorted(items, key=lambda x: x[0], reverse=True)[:TOPK_PER_SEED]:
                        w.writerow([
                            sid,
                            pv.get("platform", ""),
                            f"{s:.3f}",
                            pv.get("url", ""),
                            (pv.get("title") or "")[:240],
                            pv.get("author", ""),
                            pv.get("date", ""),
                        ])
            log.info(f"Wrote leaderboard CSV → {args.dump_csv}")
        except Exception as e:
            log.error(f"Failed to write CSV to {args.dump_csv}: {e}")


if __name__ == "__main__":
    main()

#example usage:
# python cli/score_previews.py --backend postgres --batch-size 200 --limit 5000
# # or for Mongo:
# python cli/score_previews.py --backend mongo --batch-size 200 --limit 5000
