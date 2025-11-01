import json
from typing import Dict, Any, List
from oie_search.digestors import normalize_preview
from oie_search.scoring import score_preview

def process_previews(platform: str, seed: Dict[str, Any], raw_previews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # seed should include: title, description, transcript, metadata.hashtags, important_phrases (list)
    results = []
    for raw in raw_previews:
        pv = normalize_preview(platform, raw)
        scored = score_preview(seed, pv)
        results.append({
            "platform": platform,
            "url": pv.get("url"),
            "normalized": pv,
            "score": scored["score"],
            "decision": scored["decision"],
            "signals": scored["signals"]
        })
    return results

if __name__ == "__main__":
    # Example local test:
    seed = {
        "title": "Example Seed Title",
        "description": "Seed description here",
        "transcript": "Seed transcript here",
        "important_phrases": ["example phrase one", "example phrase two"],
        "metadata": {"hashtags": ["science","neuro"]}
    }
    raw_previews = [
        {"snippet":{"title":"Test video","description":"how-to explainer"},"id":"abc123","statistics":{"viewCount":5000}}
    ]
    out = process_previews("youtube", seed, raw_previews)
    print(json.dumps(out, indent=2))

