#!/usr/bin/env python
import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from oie_search.pipelines.preview_intake import process_previews

def main():
    if len(sys.argv) < 4:
        print("Usage: score_previews.py <platform> <seed_json_path> <previews_json_path>")
        sys.exit(1)
    platform = sys.argv[1]
    seed = json.load(open(sys.argv[2], "r", encoding="utf-8"))
    previews = json.load(open(sys.argv[3], "r", encoding="utf-8"))
    results = process_previews(platform, seed, previews)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
