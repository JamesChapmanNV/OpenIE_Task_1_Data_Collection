
#!/usr/bin/env python
# import sys, os, json
# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# from oie_search.pipelines.preview_intake import process_previews

import argparse, csv, os
from collections import defaultdict
from oie_search.utils.logging import setup_logger
from oie_search.config import get_app, get_score_int, get_score_float
from oie_search.db import get_backend
from oie_search.scoring import featurize_preview, score_preview, KEEP_MIN, TOPK_PER_SEED

def parse_args():
    ap = argparse.ArgumentParser("Score previews")
    ap.add_argument("--backend", default=os.getenv("QUERY_BACKEND", get_app("QUERY_BACKEND","postgres")))
    ap.add_argument("--batch-size", type=int, default=int(get_app("BATCH_SIZE","100")))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--log-level", default="INFO")
    ap.add_argument("--dump-csv", default=None, help="Path to write top-k per-seed CSV")
    return ap.parse_args()


# def main():
#     if len(sys.argv) < 4:
#         print("Usage: score_previews.py <platform> <seed_json_path> <previews_json_path>")
#         sys.exit(1)
#     platform = sys.argv[1]
#     seed = json.load(open(sys.argv[2], "r", encoding="utf-8"))
#     previews = json.load(open(sys.argv[3], "r", encoding="utf-8"))
#     results = process_previews(platform, seed, previews)
#     print(json.dumps(results, indent=2))



def main():
    args = parse_args()
    log = setup_logger(level=args.log_level)
    db = get_backend(args.backend)

    wrote = 0
    per_seed = defaultdict(list)

    for pv in db.list_unscored_previews(batch_size=args.batch_size, limit=args.limit):
        seed = db.get_seed(pv["seed_id"])
        feats = featurize_preview(pv, seed)
        s = score_preview(feats)
        record = {
            "preview_id": pv["preview_id"],
            "seed_id": pv["seed_id"],
            "platform": pv["platform"],
            "score": s,
            "features": feats,
            "reasons": feats.get("_reasons","")
        }
        db.save_preview_scores([record])
        wrote += 1
        if s >= KEEP_MIN:
            per_seed[pv["seed_id"]].append((s, pv))

    log.info(f"Scored previews: {wrote}")

    if args.dump_csv:
        with open(args.dump_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["seed_id","platform","score","url","title","author","timestamp"])
            for sid, items in per_seed.items():
                for s, pv in sorted(items, key=lambda x: x[0], reverse=True)[:TOPK_PER_SEED]:
                    w.writerow([sid, pv.get("platform"), f"{s:.3f}", pv.get("url",""), pv.get("title",""), pv.get("author",""), pv.get("timestamp","")])
        log.info(f"Wrote leaderboard CSV → {args.dump_csv}")

if __name__ == "__main__":
    main()




