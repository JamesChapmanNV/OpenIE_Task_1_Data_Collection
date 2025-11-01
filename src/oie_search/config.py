from pydantic import BaseModel
from typing import List, Optional

PLATFORMS_PRIORITY: List[str] = [
    "youtube","reddit","bluesky","mastodon","spotify",
    "apple podcasts","instagram","threads","facebook","x"
]

class QueryGenConfig(BaseModel):
    include_author: bool = True
    max_preview_results: int = 50
    time_window: Optional[str] = None  # e.g. "last_30_days"
    language_priority: Optional[List[str]] = None  # e.g. ["en"]

DEFAULT_QCFG = QueryGenConfig()
