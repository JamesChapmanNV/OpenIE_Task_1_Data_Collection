from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from numpy import dot
from numpy.linalg import norm

def _quick_text_cosine(a: str, b: str) -> float:
    a = a or ""
    b = b or ""
    vect = TfidfVectorizer(max_features=500).fit([a, b])
    A = vect.transform([a]).toarray()[0]
    B = vect.transform([b]).toarray()[0]
    denom = (norm(A) * norm(B))
    return float(dot(A, B) / denom) if denom > 0 else 0.0

def score_preview(seed: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
    seed_text = " ".join(filter(None, [seed.get("title",""), seed.get("description",""), seed.get("transcript","")]))
    preview_text = " ".join(filter(None, [preview.get("title",""), preview.get("snippet",""), preview.get("transcript_snippet","")]))
    semantic = _quick_text_cosine(seed_text, preview_text)

    phrases: List[str] = [p.strip('"') for p in seed.get("important_phrases", [])]
    lex_over = 0.0
    if phrases:
        lex_over = sum(1 for p in phrases if p and p.lower() in (preview_text.lower())) / len(phrases)

    seed_tags = set(seed.get("metadata", {}).get("hashtags", []) or [])
    preview_tags = set(preview.get("hashtags", []) or [])
    hashtag_overlap = (len(seed_tags & preview_tags) / len(seed_tags)) if seed_tags else 0.0

    media_keywords = {"podcast","interview","tutorial","how-to","review","news","explainer"}
    media_match = 1.0 if any(k in (preview_text.lower()) for k in media_keywords) else 0.0

    # Freshness placeholder (tweak per your project)
    freshness = 1.0 if preview.get("date") else 0.5

    engagement = 0.0
    if isinstance(preview.get("engagement"), dict):
        vals = []
        for v in preview["engagement"].values():
            try:
                vals.append(float(v))
            except Exception:
                pass
        if vals:
            engagement = min(1.0, sum(vals) / 10000.0)

    score = (semantic*0.4 + lex_over*0.2 + hashtag_overlap*0.1 + media_match*0.1 + freshness*0.1 + engagement*0.1)*100
    decision = "keep" if score >= 65 else ("consider" if score >= 50 else "reject")
    return {
        "decision": decision,
        "score": int(score),
        "signals": {
            "semantic_similarity": round(semantic, 3),
            "lexical_overlap": round(lex_over, 3),
            "hashtag_overlap": round(hashtag_overlap, 3),
            "media_match": round(media_match, 3),
            "freshness": round(freshness, 3),
            "engagement": round(engagement, 3)
        }
    }
