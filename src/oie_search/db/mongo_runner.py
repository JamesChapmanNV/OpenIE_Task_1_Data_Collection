import os
from dotenv import load_dotenv
from pymongo import MongoClient
from typing import Dict, List
from oie_search.query_generator import generate_queries_for_platform
from oie_search.config import PLATFORMS_PRIORITY, DEFAULT_QCFG

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "oie")

def generate_queries_mongo(seeds_collection="seeds", out_collection="search_queries", limit: int = 100) -> List[Dict]:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    seeds = db[seeds_collection].find().limit(limit)
    out_coll = db[out_collection]

    results = []
    for seed in seeds:
        for platform in PLATFORMS_PRIORITY:
            qset = generate_queries_for_platform(seed, platform, config={"include_author": DEFAULT_QCFG.include_author})
            doc = {
                "seed_id": seed["_id"],
                "platform": platform,
                "precise": qset["precise"],
                "broad": qset["broad"],
                "hashtag_phrase": qset["hashtag_phrase"]
            }
            out_coll.insert_one(doc)
            results.append(doc)
    return results
