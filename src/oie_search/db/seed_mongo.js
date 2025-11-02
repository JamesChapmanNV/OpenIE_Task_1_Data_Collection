// Seed data for MongoDB database: openie
const dbname = "openie";
const db = db.getSiblingDB(dbname);

// ------------------------------
// (A) SEEDS
// ------------------------------
db.seeds.insertMany([
  {
    seed_id: NumberLong(101),
    seed_topic: "Neuroscience of Mental Health",
    title: "Clinical vs self-diagnosis of ADHD/ASD/AuDHD",
    description: "Contrast DSM-5/ICD clinical pathways against informal self-identification on social media.",
    transcript: null,
    ocr: null,
    body: "Clinician-led assessments vs self-tests; masking; late diagnosis; barriers to access; validity concerns.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(102),
    seed_topic: "Neuroscience of Mental Health",
    title: "Pop psychology coping strategies (ND daily management)",
    description: "Catalog common coping/management strategies spread by influencers and communities.",
    transcript: null,
    ocr: null,
    body: "Executive function scaffolding; sensory regulation; CBT/DBT-inspired tips; planner/automation hacks.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(103),
    seed_topic: "Neuroscience of Mental Health",
    title: "Neurodivergent identity and community discourse",
    description: "Map social framing of identity, belonging, and stigma across platforms.",
    transcript: null,
    ocr: null,
    body: "Identity-first vs person-first language; #ActuallyAutistic; workplace accommodations; community norms.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(104),
    seed_topic: "Neuroscience of Mental Health",
    title: "Ethics of hypothetical diagnosis and intervention",
    description: "Debate: early identification, neuroenhancement, and alteration of traits.",
    transcript: null,
    ocr: null,
    body: "Bioethics of altering traits; identity vs disorder; consent/assent in minors; equity/access.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(105),
    seed_topic: "Neuroscience of Mental Health",
    title: "Chemogenetics (DREADDs) & circuit modulation",
    description: "Track peer-reviewed findings on DREADDs and related neuromodulation relevant to ND phenotypes.",
    transcript: null,
    ocr: null,
    body: "Designer receptors; targeted circuit control; translational hurdles; specificity and off-target effects.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(106),
    seed_topic: "Neuroscience of Mental Health",
    title: "Genetic pathways and molecular targets in ND",
    description: "Summarize candidate genes/pathways and emerging molecular interventions for ADHD/ASD.",
    transcript: null,
    ocr: null,
    body: "Polygenic architecture; synaptic genes; dopamine/norepinephrine pathways; CRISPR prospects.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(107),
    seed_topic: "Neuroscience of Mental Health",
    title: "AI + neuroimaging/EEG for diagnostic support",
    description: "Survey ML applied to fMRI/EEG/eye-tracking for ADHD/ASD decision support.",
    transcript: null,
    ocr: null,
    body: "Biomarkers; model generalization; dataset shift; reproducibility; clinical utility.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(108),
    seed_topic: "Neuroscience of Mental Health",
    title: "Pharmaceutical innovation and clinical trials",
    description: "Repurposed and novel candidates for ADHD/ASD, trial endpoints, safety/efficacy.",
    transcript: null,
    ocr: null,
    body: "Guanfacine, modafinil, dopamine reuptake modulation; pediatric vs adult; comorbidities.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(109),
    seed_topic: "Neuroscience of Mental Health",
    title: "Genetic screening & early-childhood interventions",
    description: "Public and clinical discourse on predictive screening and early therapies.",
    transcript: null,
    ocr: null,
    body: "Polygenic risk scores; infant/toddler screening; ethical safeguards; early supports.",
    created_at: new Date()
  },
  {
    seed_id: NumberLong(110),
    seed_topic: "Neuroscience of Mental Health",
    title: "Cultural and social framing of neurodivergence",
    description: "How language, stigma, and representation evolve across platforms and media.",
    transcript: null,
    ocr: null,
    body: "Shifts in terminology; media portrayals; advocacy; policy debates; workplace discourse.",
    created_at: new Date()
  }
], { ordered: false });


// ------------------------------
// (B) SEARCH QUERIES
// ------------------------------

db.search_queries.insertMany([
  {
    seed_id: NumberLong(101),
    platform: "youtube",
    query_text: "\"clinical diagnosis\" ADHD ASD site:youtube.com",
    gen_meta: { prompt_version: "v1.0", k_terms: ["DSM-5","clinical diagnosis","ADHD","ASD","AuDHD"] },
    created_at: new Date()
  },
  {
    seed_id: NumberLong(101),
    platform: "reddit",
    query_text: "ADHD self-diagnosis experiences site:reddit.com",
    gen_meta: { prompt_version: "v1.0", k_terms: ["self-diagnosis","masking","assessment"] },
    created_at: new Date()
  },
  {
    seed_id: NumberLong(102),
    platform: "youtube",
    query_text: "ADHD coping strategies routines sensory regulation site:youtube.com",
    gen_meta: { prompt_version: "v1.0", k_terms: ["coping","executive function","sensory"] },
    created_at: new Date()
  },
  {
    seed_id: NumberLong(105),
    platform: "youtube",
    query_text: "DREADDs chemogenetics autism circuit modulation site:youtube.com",
    gen_meta: { prompt_version: "v1.0", k_terms: ["DREADDs","chemogenetics","circuit"] },
    created_at: new Date()
  },
  {
    seed_id: NumberLong(107),
    platform: "youtube",
    query_text: "EEG biomarkers ADHD ASD ML site:youtube.com",
    gen_meta: { prompt_version: "v1.0", k_terms: ["EEG","biomarkers","ML","ADHD","ASD"] },
    created_at: new Date()
  },
  {
    seed_id: NumberLong(108),
    platform: "youtube",
    query_text: "new ADHD drug trial 2024 2025 site:youtube.com",
    gen_meta: { prompt_version: "v1.0", k_terms: ["pharma","trial","ADHD","2024","2025"] },
    created_at: new Date()
  }
], { ordered: false });


// ------------------------------
// (C) PREVIEWS (examples)
// ------------------------------

db.previews.insertOne({
  seed_id: NumberLong(101),
  platform: "youtube",
  url: "https://www.youtube.com/watch?v=dummy123",
  title: "Clinical vs Self-Diagnosis: ADHD/ASD Explained",
  snippet: "Explainer discussing differences between clinical assessment and self-identification.",
  author: "Channel ND Insights",
  published_at: ISODate("2025-10-01T00:00:00Z"),
  raw_meta: { channelId: "demo-channel", viewCount: 12345 },
  score: 0.65,
  created_at: new Date()
});


// ------------------------------
// (D) Confirmation
// ------------------------------

print("Mongo seed complete for DB 'openie' (Neuroscience of Mental Health).");
