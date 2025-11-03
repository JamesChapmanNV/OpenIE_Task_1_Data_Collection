"""
Minimal Reddit search client.

Two strategies supported:
  A) Public JSON endpoint (no OAuth) via https://www.reddit.com/search.json
     - Easiest to start; subject to tighter rate limits and may miss restricted posts.
     - Set REDDIT_USER_AGENT (required by Reddit).

  B) OAuth API (optional): set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME,
     REDDIT_PASSWORD to use the official API for better reliability.

Functions:
  search_posts(query: str, sort="relevance", limit=25, oauth=False) -> List[dict]
"""

from __future__ import annotations
import os
import time
import requests
from typing import List, Dict, Any, Optional
from requests.auth import HTTPBasicAuth

PUBLIC_SEARCH_URL = "https://www.reddit.com/search.json"
OAUTH_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_SEARCH_URL = "https://oauth.reddit.com/search"

REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "OpenIE/0.1 (by u/your_username)")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

def _ensure_user_agent(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = headers or {}
    headers.setdefault("User-Agent", REDDIT_USER_AGENT)
    return headers

def _oauth_token() -> str:
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        raise RuntimeError("OAuth requested but Reddit credentials are missing.")
    auth = HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {"grant_type": "password", "username": REDDIT_USERNAME, "password": REDDIT_PASSWORD}
    headers = _ensure_user_agent()
    r = requests.post(OAUTH_TOKEN_URL, data=data, headers=headers, auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def _public_search(query: str, sort: str, limit: int) -> List[Dict[str, Any]]:
    params = {"q": query, "sort": sort, "limit": min(limit, 100), "t": "all", "restrict_sr": "false"}
    headers = _ensure_user_agent()
    r = requests.get(PUBLIC_SEARCH_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    payload = r.json()
    children = payload.get("data", {}).get("children", [])
    return [ch for ch in children if isinstance(ch, dict)]

def _oauth_search(query: str, sort: str, limit: int) -> List[Dict[str, Any]]:
    token = _oauth_token()
    headers = _ensure_user_agent({"Authorization": f"bearer {token}"})
    params = {"q": query, "sort": sort, "limit": min(limit, 100), "t": "all", "restrict_sr": "false"}
    r = requests.get(OAUTH_SEARCH_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    payload = r.json()
    children = payload.get("data", {}).get("children", [])
    return [ch for ch in children if isinstance(ch, dict)]

def search_posts(query: str, sort: str = "relevance", limit: int = 25, oauth: bool = False) -> List[Dict[str, Any]]:
    if oauth:
        return _oauth_search(query, sort, limit)
    return _public_search(query, sort, limit)
