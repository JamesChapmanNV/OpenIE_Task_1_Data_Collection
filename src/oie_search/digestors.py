from typing import Dict, Any

def normalize_preview(platform: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    p = {
        "title": "",
        "snippet": "",
        "transcript_snippet": "",
        "ocr": "",
        "hashtags": [],
        "author": None,
        "date": None,
        "engagement": {},
        "url": None,
    }

    pl = platform.lower()
    if pl == "youtube":
        snip = raw.get("snippet", {})
        p["title"] = snip.get("title") or ""
        p["snippet"] = (snip.get("description") or "")[:400]
        p["date"] = snip.get("publishedAt")
        stats = raw.get("statistics", {})
        p["engagement"] = {"views": stats.get("viewCount")}
        vid = raw.get("id") if isinstance(raw.get("id"), str) else raw.get("id", {}).get("videoId")
        p["url"] = f"https://www.youtube.com/watch?v={vid}" if vid else raw.get("url")
        return p

    if pl == "reddit":
        data = raw.get("data", {})
        p["title"] = data.get("title") or ""
        p["snippet"] = (data.get("selftext") or "")[:400]
        p["date"] = data.get("created_utc")
        p["engagement"] = {"score": data.get("score"), "comments": data.get("num_comments")}
        p["url"] = "https://reddit.com" + (data.get("permalink") or "")
        return p

    # Generic fallback
    p["title"] = raw.get("title") or ""
    p["snippet"] = (raw.get("description") or raw.get("content") or "")[:400]
    p["date"] = raw.get("published") or raw.get("created_at")
    p["engagement"] = raw.get("metrics", {})
    p["url"] = raw.get("url")
    p["hashtags"] = raw.get("hashtags", [])
    p["author"] = raw.get("author")
    return p

