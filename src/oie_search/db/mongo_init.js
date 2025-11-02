// MongoDB indexes for database: openie

const dbname = "openie";
const db = db.getSiblingDB(dbname);

// seeds
db.seeds.createIndex({ seed_topic: 1 });

// search_queries
db.search_queries.createIndex({ seed_id: 1 });
db.search_queries.createIndex({ platform: 1 });
db.search_queries.createIndex(
  { seed_id: 1, platform: 1, query_text: 1 },
  { unique: true }
);

// previews (optional)
db.previews.createIndex({ platform: 1, url: 1 }, { unique: true });
db.previews.createIndex({ seed_id: 1 });
db.previews.createIndex({ score: -1 });

print(`Indexes ensured for MongoDB database '${dbname}'.`);
