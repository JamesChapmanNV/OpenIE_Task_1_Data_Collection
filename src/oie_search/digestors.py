"""
Digestors: normalize previews from different platforms into a common schema
and (optionally) featurize them for scoring.

Common normalized preview schema (dict):
{
  "platform": "youtube" | "reddit" | "mastodon" | "bsky" | "twitter" | ...,
  "url": str,
  "title": str,
  "snippet": str,        # short text summary or first lines of body/description
  "author": str,
  "date": str,           # ISO 8601 (UTC) e.g. "2025-10-30T17:02:55Z"
  "hashtags": [str],     # lowercase, without '#'
  "engagement": {        # all optional, ints if known
      "views": int | None,
      "likes": int | None,
      "comments": int | None
  },
  "media": {             # optional hints for downstream filtering
      "has_video": bool | None,
      "duration_sec": int | None
  },
  "raw": dict            # original raw object, for debugging/auditing
}
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timezone

HASHTAG_RE = re.compile(r"(?:^|[\s\(\)\[\]\{\}.,!?;:'\"/\\-])#([A-Za-z0-9_]{2,50})")

def _iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def _extract_hashtags(*texts: Optional[str]) -> List[str]:
    tags = []
    for t in texts:
        if not t:
            continue
        tags.extend([m.lower() for m in HASHTAG_RE.findall(t)])
    # dedupe preserving order
    seen = set()
    out = []
    for x in tags:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:30]

def _coalesce(*vals, default=None):
    for v in vals:
        if v is not None and v != "":
            return v
    return default

# --------------------------- Platform Normalizers -----------------------------

def _normalize_youtube(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts the combined item shape produced by oie_search.apis.youtube.search_videos
    which already merges search 'snippet' + 'statistics' + duration.
    """
    snippet = raw.get("snippet", {}) or {}
    stats = raw.get("statistics", {}) or {}
    content = raw.get("contentDetails", {}) or {}

    video_id = _coalesce(raw.get("id"), raw.get("videoId"))
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
    title = _coalesce(raw.get("title"), snippet.get("title"))
    desc  = _coalesce(raw.get("description"), snippet.get("description"))
    author = _coalesce(raw.get("channelTitle"), snippet.get("channelTitle"))
    # Prefer publishedAt if present
    published_at = _coalesce(raw.get("publishedAt"), snippet.get("publishedAt"))
    date = None
    if published_at:
        try:
            date = _iso(datetime.fromisoformat(published_at.replace("Z","+00:00")))
        except Exception:
            date = published_at

    # duration in ISO 8601 (PT#M#S). Keep seconds if provided by API client.
    duration_sec = raw.get("durationSec")

    hashtags = _extract_hashtags(title, desc)
    engagement = {
        "views": int(stats["viewCount"]) if "viewCount" in stats else None,
        "likes": int(stats["likeCount"]) if "likeCount" in stats else None,
        "comments": int(stats["commentCount"]) if "commentCount" in stats else None,
    }

    return {
        "platform": "youtube",
        "url": url,
        "title": title,
        "snippet": (desc or "")[:400],
        "author": author,
        "date": date,
        "hashtags": hashtags,
        "engagement": engagement,
        "media": {"has_video": True, "duration_sec": duration_sec},
        "raw": raw,
    }

def _normalize_reddit(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts Reddit items from either the public search.json or OAuth API (similar fields).
    """
    data = raw.get("data", raw)  # support both 'child' and flattened dict
    url = _coalesce(data.get("url_overridden_by_dest"), f"https://www.reddit.com{data.get('permalink')}")
    title = data.get("title")
    selftext = data.get("selftext") or ""
    author = data.get("author")
    created_utc = data.get("created_utc")
    date = _iso(datetime.fromtimestamp(created_utc, tz=timezone.utc)) if created_utc else None
    num_comments = data.get("num_comments")
    score = data.get("score")  # upvotes minus downvotes (approx)
    # Heuristic: likes ~ score if no better field is present
    engagement = {
        "views": None,  # not provided by API
        "likes": int(score) if isinstance(score, (int, float)) else None,
        "comments": int(num_comments) if isinstance(num_comments, (int, float)) else None,
    }
    snippet = _coalesce(selftext[:400], title)
    hashtags = _extract_hashtags(title, selftext)

    return {
        "platform": "reddit",
        "url": url,
        "title": title,
        "snippet": snippet,
        "author": author,
        "date": date,
        "hashtags": hashtags,
        "engagement": engagement,
        "media": {"has_video": "media" in data or "is_video" in data and data.get("is_video")},
        "raw": raw,
    }

# ------------------------------ Public API -----------------------------------

def normalize_preview(platform: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert platform-native preview objects into the common normalized schema.
    If 'raw' already looks normalized (has platform/url/title), this is idempotent.
    """
    if raw is None:
        raise ValueError("normalize_preview received None")

    # If already normalized, just return (idempotent)
    if isinstance(raw, dict) and "platform" in raw and "url" in raw and "title" in raw:
        return raw

    p = (platform or "").lower()
    if p in ("youtube", "yt"):
        return _normalize_youtube(raw)
    elif p == "reddit":
        return _normalize_reddit(raw)
    else:
        # Generic passthrough with best-effort fields
        title = raw.get("title") if isinstance(raw, dict) else None
        body = raw.get("description") or raw.get("body") or raw.get("text") if isinstance(raw, dict) else None
        url = raw.get("url") if isinstance(raw, dict) else None
        author = raw.get("author") if isinstance(raw, dict) else None
        hashtags = _extract_hashtags(title, body)
        return {
            "platform": p or "unknown",
            "url": url,
            "title": title,
            "snippet": (body or "")[:400],
            "author": author,
            "date": None,
            "hashtags": hashtags,
            "engagement": {"views": None, "likes": None, "comments": None},
            "media": {"has_video": None, "duration_sec": None},
            "raw": raw,
        }

def featurize_preview(seed: Dict[str, Any], normalized_preview: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional shim if you prefer a two-step pipeline (featurize -> score).

    Returns a compact feature dict that scoring.score_preview could accept
    if you later split it into (feats -> score). For now, we simply return
    the normalized preview with seed metadata attached for convenience.
    """
    return {
        "seed": seed,
        "preview": normalized_preview,
    }




# # Original implementation (old versions of normalize_preview)
# def normalize_preview(platform: str, raw: Dict[str, Any]) -> Dict[str, Any]:
#     p = {
#         "title": "",
#         "snippet": "",
#         "transcript_snippet": "",
#         "ocr": "",
#         "hashtags": [],
#         "author": None,
#         "date": None,
#         "engagement": {},
#         "url": None,
#     }

#     pl = platform.lower()
#     if pl == "youtube":
#         snip = raw.get("snippet", {})
#         p["title"] = snip.get("title") or ""
#         p["snippet"] = (snip.get("description") or "")[:400]
#         p["date"] = snip.get("publishedAt")
#         stats = raw.get("statistics", {})
#         p["engagement"] = {"views": stats.get("viewCount")}
#         vid = raw.get("id") if isinstance(raw.get("id"), str) else raw.get("id", {}).get("videoId")
#         p["url"] = f"https://www.youtube.com/watch?v={vid}" if vid else raw.get("url")
#         return p

#     if pl == "reddit":
#         data = raw.get("data", {})
#         p["title"] = data.get("title") or ""
#         p["snippet"] = (data.get("selftext") or "")[:400]
#         p["date"] = data.get("created_utc")
#         p["engagement"] = {"score": data.get("score"), "comments": data.get("num_comments")}
#         p["url"] = "https://reddit.com" + (data.get("permalink") or "")
#         return p

#     # Generic fallback
#     p["title"] = raw.get("title") or ""
#     p["snippet"] = (raw.get("description") or raw.get("content") or "")[:400]
#     p["date"] = raw.get("published") or raw.get("created_at")
#     p["engagement"] = raw.get("metrics", {})
#     p["url"] = raw.get("url")
#     p["hashtags"] = raw.get("hashtags", [])
#     p["author"] = raw.get("author")
#     return p

