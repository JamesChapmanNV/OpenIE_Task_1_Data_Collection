# query_generator.py
import re
from typing import Dict, List

def normalize_text(s: str) -> str:
    if not s: return ""
    s = s.strip()
    s = re.sub(r'\s+', ' ', s) # one or more whitespace characters to single space
    return s

def top_k_terms(text: str, k=8):
    # creates a list of terms from text,  sorted by frequency (descending)
    # lightweight heuristic: split, remove very short tokens and common stopwords
    stopwords = set(["the","and","a","an","to","in","on","of","for","with","is","this","that","it","by","be","are","as","at"])
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9#@']{2,}", text)]
    freq = {}
    for t in tokens:
        if t in stopwords or t.isdigit(): continue
        freq[t] = freq.get(t,0) + 1
    sorted_terms = sorted(freq.items(), key=lambda x: -x[1])
    return [t for t,_ in sorted_terms[:k]]

def build_phrase_candidates(seed: Dict, num_sentences=3) -> List[str]:
    # choose representative phrases (title first, then long ngrams from transcript/description)
    phrases = []
    if seed.get("title"):
        phrases.append(seed["title"])
    # prefer long descriptive phrases from description/transcript / OCR
    for fld in ("description","transcript","ocr","body"):
        text = seed.get(fld,"")
        if not text: continue
        # extract quoted-like phrases: heuristics
        sentences = re.split(r'[\.!\?]\s+', text)
        sentences = [s for s in sentences if len(s.split())>=4]
        for s in sentences[:num_sentences]:
            phrases.append(s.strip())
    # dedupe, normalize
    seen = set()
    out = []
    for p in phrases:
        np = normalize_text(p)
        if not np or np in seen: continue
        out.append(np)
        seen.add(np)
    return out[:6]

def generate_queries_for_platform(seed: Dict, platform: str, config: Dict=None) -> Dict[str,str]:
    """
    Returns dict with keys: 'precise','broad','hashtag_phrase'
    """
    config = config or {}
    title = normalize_text(seed.get("title",""))
    body = normalize_text(seed.get("body",""))
    transcript = normalize_text(seed.get("transcript",""))
    ocr = normalize_text(seed.get("ocr",""))
    description = normalize_text(seed.get("description",""))
    hashtags = seed.get("metadata",{}).get("hashtags",[]) or []
    author = seed.get("metadata",{}).get("author","")
    lang = seed.get("metadata",{}).get("language","")
    phrases = build_phrase_candidates(seed)
    # select top tokens
    combined_text = " ".join([title, description, transcript, ocr, body])
    top_terms = top_k_terms(combined_text, k=10)

    # platform-specific escaping / operator differences
    def q_escape(s):
        # escape quotes
        return s.replace('"','\\"')

    if platform.lower() == "youtube":
        # YouTube search box supports quoted phrases and + for required words; no boolean OR reliably
        precise = f'"{q_escape(title)}"' if title else f'"{q_escape(phrases[0] if phrases else combined_text[:80])}"'
        broad = " ".join(top_terms[:6])
        hashtag_phrase = " ".join(hashtags[:3]) + " " + (precise if title else "")
    elif platform.lower() == "reddit":
        # reddit.com/search supports "title:" and subreddit: but search UI varies; use exact phrase + subreddit hints
        precise = f'title:"{q_escape(title)}"' if title else f'"{q_escape(phrases[0] if phrases else combined_text[:80])}"'
        broad = " OR ".join(top_terms[:8])
        hashtag_phrase = " ".join(["#"+h for h in hashtags[:4]]) + " " + (precise if title else "")
    elif platform.lower() in ("bluesky","mastodon"):
        # federated platforms: hashtags and phrases are strongest
        precise = f'"{q_escape(phrases[0])}"' if phrases else f'"{q_escape(title)}"'
        broad = " ".join(top_terms[:8])
        hashtag_phrase = " ".join(["#"+h for h in hashtags[:6]])
    elif platform.lower() in ("spotify","apple podcasts"):
        # search primarily by title and episode description
        precise = f'"{q_escape(title)}"' if title else f'"{q_escape(phrases[0])}"'
        broad = " ".join(top_terms[:10])
        hashtag_phrase = ""  # podcasts rarely use hashtags in platform search
    elif platform.lower() in ("instagram","threads","facebook","x","twitter"):
        # social networks: hashtags, exact phrase, author: etc.
        if platform.lower() in ("x","twitter"):
            precise = f'"{q_escape(title)}"'
            broad = " OR ".join(top_terms[:8])
            hashtag_phrase = " ".join(["#"+h for h in hashtags[:6]])
        else:
            precise = f'"{q_escape(title)}"' if title else f'"{q_escape(phrases[0])}"'
            broad = " ".join(top_terms[:8])
            hashtag_phrase = " ".join(["#"+h for h in hashtags[:6]])
    else:
        # generic
        precise = f'"{q_escape(title)}"' if title else f'"{q_escape(phrases[0])}"'
        broad = " ".join(top_terms[:8])
        hashtag_phrase = " ".join(["#"+h for h in hashtags[:4]])

    # optionally include author/date operators if configured
    if author and config.get("include_author", True):
        precise = (f'from:{author} ' + precise).strip()

    return {"precise": precise, "broad": broad, "hashtag_phrase": hashtag_phrase}


