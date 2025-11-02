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


# import os
# import configparser
# from pathlib import Path

# _cfg = configparser.ConfigParser()
# _cfg.read(Path(__file__).resolve().parents[2] / "OpenIE_Task_1_Data_Collection.ini")

# def get_app(key, default=None):     return _cfg.get("app", key, fallback=default)
# def get_pg(key, default=None):      return _cfg.get("postgres", key, fallback=default)
# def get_mongo(key, default=None):   return _cfg.get("mongo", key, fallback=default)
# def get_score(key, default=None):   return _cfg.get("scoring", key, fallback=default)
# def get_score_float(key, default):  return _cfg.getfloat("scoring", key, fallback=default)
# def get_score_int(key, default):    return _cfg.getint("scoring", key, fallback=default)
