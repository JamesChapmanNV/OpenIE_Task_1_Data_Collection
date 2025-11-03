"""
Demo: fetch from YouTube/Reddit, normalize, score, print top results.
"""

import os
from oie_search.apis.youtube import search_videos
from oie_search.apis.reddit import search_posts
from oie_search.digestors import normalize_preview
from oie_search.scoring import score_preview

SEED = {
    "seed_id": 101,
    "title": "ASD vs ADHD clinical diagnosis vs self-diagnosis",
    "description": "Neuroscience of mental health: diagnostic criteria, informal signs, community discourse, and ethics.",
    "transcript": None,
    "ocr": None,
    "body": None,
}

def main():
    q = '"ASD" "ADHD" clinical diagnosis vs self-diagnosis'
    yt = search_videos(q, published_after=None, max_results=10)
    rd = search_posts(q, sort="new", limit=10, oauth=False)

    previews = []
    for it in yt:
        previews.append(normalize_preview("youtube", it))
    for it in rd:
        previews.append(normalize_preview("reddit", it))

    scored = []
    for p in previews:
        s = score_preview(SEED, p)
        scored.append((s["score"], s["decision"], p["platform"], p["title"], p["url"]))

    scored.sort(reverse=True, key=lambda x: x[0])
    for score, decision, platform, title, url in scored[:10]:
        print(f"{score:6.2f}  {decision:8}  {platform:7}  {title[:70]}  {url}")

if __name__ == "__main__":
    main()
