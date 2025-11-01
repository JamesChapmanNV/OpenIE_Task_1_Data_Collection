import os
from oie_search.db.postgres_runner import generate_queries_postgres
from oie_search.db.mongo_runner import generate_queries_mongo

def main():
    target = os.getenv("QUERY_BACKEND", "postgres")  # "postgres" or "mongo"
    if target == "postgres":
        out = generate_queries_postgres(limit=int(os.getenv("QUERY_LIMIT", "100")))
    else:
        out = generate_queries_mongo(
            seeds_collection=os.getenv("MONGO_SEEDS_COLLECTION", "seeds"),
            out_collection=os.getenv("MONGO_OUT_COLLECTION", "search_queries"),
            limit=int(os.getenv("QUERY_LIMIT", "100"))
        )
    print(f"Generated {len(out)} queries.")

if __name__ == "__main__":
    main()
