"""
Minimal YouTube Search client.

Requires:
  - YOUTUBE_API_KEY in environment
Optional:
  - YOUTUBE_MAX_RESULTS (default 25)

Functions:
  search_videos(query: str, published_after: str|None, max_results: int|None)
    -> List[dict] (combined snippet + statistics + durationSec)

Notes:
- We perform a second call to videos.list to enrich statistics & duration.
- 'published_after' should be RFC3339 (e.g., "2025-10-01T00:00:00Z") or None.
"""

from __future__ import annotations
import os
import time
import requests
from typing import List, Dict, Any, Optional

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_MAX_RESULTS = int(os.getenv("YOUTUBE_MAX_RESULTS", "25"))

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def _get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def _iso8601_duration_to_seconds(s: Optional[str]) -> Optional[int]:
    # Very small parser; for full coverage use isodate.parse_duration
    if not s or not s.startswith("P"):
        return None
    # Parse patterns like PT#H#M#S
    hours = minutes = seconds = 0
    t = s.split("T")[-1] if "T" in s else ""
    num = ""
    for ch in t:
        if ch.isdigit():
            num += ch
        else:
            if ch == "H":
                hours = int(num or 0); num = ""
            elif ch == "M":
                minutes = int(num or 0); num = ""
            elif ch == "S":
                seconds = int(num or 0); num = ""
    return hours * 3600 + minutes * 60 + seconds

def search_videos(
    query: str,
    published_after: Optional[str] = None,
    max_results: Optional[int] = None,
    order: str = "relevance",
) -> List[Dict[str, Any]]:
    if not YOUTUBE_API_KEY:
        raise RuntimeError("Missing YOUTUBE_API_KEY in environment.")
    max_results = max_results or YOUTUBE_MAX_RESULTS

    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "type": "video",
        "maxResults": min(max_results, 50),
        "q": query,
        "order": order,
    }
    if published_after:
        params["publishedAfter"] = published_after

    data = _get(SEARCH_URL, params)
    items = data.get("items", [])

    # Batch fetch statistics + duration
    video_ids = [it["id"]["videoId"] for it in items if "id" in it and "videoId" in it["id"]]
    if not video_ids:
        return []
    stats_data = _get(VIDEOS_URL, {
        "key": YOUTUBE_API_KEY,
        "part": "statistics,contentDetails,snippet",
        "id": ",".join(video_ids),
        "maxResults": len(video_ids)
    })
    stats_by_id = {x["id"]: x for x in stats_data.get("items", [])}

    merged = []
    for it in items:
        vid = it["id"]["videoId"]
        snip = it.get("snippet", {})
        srec = stats_by_id.get(vid, {})
        merged_snip = srec.get("snippet", {}) or snip
        stat = srec.get("statistics", {}) or {}
        content = srec.get("contentDetails", {}) or {}
        duration_sec = _iso8601_duration_to_seconds(content.get("duration"))
        merged.append({
            "id": vid,
            "videoId": vid,
            "title": merged_snip.get("title"),
            "description": merged_snip.get("description"),
            "channelTitle": merged_snip.get("channelTitle"),
            "publishedAt": merged_snip.get("publishedAt"),
            "snippet": merged_snip,
            "statistics": stat,
            "contentDetails": content,
            "durationSec": duration_sec
        })

    return merged
