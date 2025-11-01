import os, json, uuid
import psycopg2
from dotenv import load_dotenv
from typing import Dict, List
from oie_search.query_generator import generate_queries_for_platform
from oie_search.config import PLATFORMS_PRIORITY, DEFAULT_QCFG

load_dotenv()

DSN = os.getenv("POSTGRES_DSN")
SEEDS_TABLE = os.getenv("SEEDS_TABLE", "seeds_table")
SEARCH_QUERIES_TABLE = os.getenv("SEARCH_QUERIES_TABLE", "search_queries")

def generate_queries_postgres(limit: int = 100) -> List[Dict]:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(f"SELECT id, data_json FROM {SEEDS_TABLE} ORDER BY id LIMIT %s;", (limit,))
    rows = cur.fetchall()

    output = []
    for rid, data_json in rows:
        seed = data_json if isinstance(data_json, dict) else json.loads(data_json)
        for platform in PLATFORMS_PRIORITY:
            qset = generate_queries_for_platform(seed, platform, config={"include_author": DEFAULT_QCFG.include_author})
            output.append({
                "seed_id": rid,
                "platform": platform,
                "precise": qset["precise"],
                "broad": qset["broad"],
                "hashtag_phrase": qset["hashtag_phrase"]
            })

    for item in output:
        cur.execute(
            f"INSERT INTO {SEARCH_QUERIES_TABLE}(id, seed_id, platform, precise, broad, hashtag_phrase) VALUES (%s,%s,%s,%s,%s,%s)",
            (str(uuid.uuid4()), item["seed_id"], item["platform"], item["precise"], item["broad"], item["hashtag_phrase"])
        )
    conn.commit()
    cur.close(); conn.close()
    return output

