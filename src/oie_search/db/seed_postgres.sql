-- Seed data for PostgreSQL database: openie
-- Topic focus: "Neuroscience of Mental Health"
-- Assumes tables from schema_postgres.sql already exist.

BEGIN;

-- 1) Insert Seeds (core topics)
WITH upsert AS (
  INSERT INTO public.seeds_table (seed_topic, title, description, transcript, ocr, body)
  VALUES
    (
      'Neuroscience of Mental Health',
      'Clinical vs self-diagnosis of ADHD/ASD/AuDHD',
      'Contrast DSM-5/ICD clinical pathways against informal self-identification on social media.',
      NULL, NULL,
      'Clinician-led assessments vs self-tests; masking; late diagnosis; barriers to access; validity concerns.'
    ),
    (
      'Neuroscience of Mental Health',
      'Pop psychology coping strategies (ND daily management)',
      'Catalog common coping/management strategies spread by influencers and communities.',
      NULL, NULL,
      'Executive function scaffolding; sensory regulation; CBT/DBT-inspired tips; planner/automation hacks.'
    ),
    (
      'Neuroscience of Mental Health',
      'Neurodivergent identity and community discourse',
      'Map social framing of identity, belonging, and stigma across platforms.',
      NULL, NULL,
      'Identity-first vs person-first language; #ActuallyAutistic; workplace accommodations; community norms.'
    ),
    (
      'Neuroscience of Mental Health',
      'Ethics of hypothetical diagnosis and intervention',
      'Debate: early identification, neuroenhancement, and alteration of traits.',
      NULL, NULL,
      'Bioethics of altering traits; identity vs disorder; consent/assent in minors; equity/access.'
    ),
    (
      'Neuroscience of Mental Health',
      'Chemogenetics (DREADDs) & circuit modulation',
      'Track peer-reviewed findings on DREADDs and related neuromodulation relevant to ND phenotypes.',
      NULL, NULL,
      'Designer receptors; targeted circuit control; translational hurdles; specificity and off-target effects.'
    ),
    (
      'Neuroscience of Mental Health',
      'Genetic pathways and molecular targets in ND',
      'Summarize candidate genes/pathways and emerging molecular interventions for ADHD/ASD.',
      NULL, NULL,
      'Polygenic architecture; synaptic genes; dopamine/norepinephrine pathways; CRISPR prospects.'
    ),
    (
      'Neuroscience of Mental Health',
      'AI + neuroimaging/EEG for diagnostic support',
      'Survey ML applied to fMRI/EEG/eye-tracking for ADHD/ASD decision support.',
      NULL, NULL,
      'Biomarkers; model generalization; dataset shift; reproducibility; clinical utility.'
    ),
    (
      'Neuroscience of Mental Health',
      'Pharmaceutical innovation and clinical trials',
      'Repurposed and novel candidates for ADHD/ASD, trial endpoints, safety/efficacy.',
      NULL, NULL,
      'Guanfacine, modafinil, dopamine reuptake modulation; pediatric vs adult; comorbidities.'
    ),
    (
      'Neuroscience of Mental Health',
      'Genetic screening & early-childhood interventions',
      'Public and clinical discourse on predictive screening and early therapies.',
      NULL, NULL,
      'Polygenic risk scores; infant/toddler screening; ethical safeguards; early supports.'
    ),
    (
      'Neuroscience of Mental Health',
      'Cultural and social framing of neurodivergence',
      'How language, stigma, and representation evolve across platforms and media.',
      NULL, NULL,
      'Shifts in terminology; media portrayals; advocacy; policy debates; workplace discourse.'
    )
  ON CONFLICT DO NOTHING
  RETURNING seed_id, seed_topic, title
)
SELECT 1;

-- 2) Generate example Search Queries for several seeds
--    We link by (seed_topic,title) to be stable across re-runs.

-- Helper CTE: pick seeds we’ll attach queries to
WITH targets AS (
  SELECT s.seed_id, s.title
  FROM public.seeds_table s
  WHERE s.seed_topic = 'Neuroscience of Mental Health'
    AND s.title IN (
      'Clinical vs self-diagnosis of ADHD/ASD/AuDHD',
      'Pop psychology coping strategies (ND daily management)',
      'Chemogenetics (DREADDs) & circuit modulation',
      'AI + neuroimaging/EEG for diagnostic support',
      'Pharmaceutical innovation and clinical trials'
    )
),
q AS (
  -- For each selected seed, create 2–3 platform-specific queries
  SELECT t.seed_id, 'youtube'::text AS platform,
         '"clinical diagnosis" ADHD ASD site:youtube.com'::text AS query_text,
         '{"prompt_version":"v1.0","k_terms":["DSM-5","clinical diagnosis","ADHD","ASD","AuDHD"]}'::jsonb AS gen_meta
  FROM targets t WHERE t.title = 'Clinical vs self-diagnosis of ADHD/ASD/AuDHD'

  UNION ALL
  SELECT t.seed_id, 'reddit', 'ADHD self-diagnosis experiences site:reddit.com',
         '{"prompt_version":"v1.0","k_terms":["self-diagnosis","masking","assessment"]}'::jsonb
  FROM targets t WHERE t.title = 'Clinical vs self-diagnosis of ADHD/ASD/AuDHD'

  UNION ALL
  SELECT t.seed_id, 'x', '"self diagnosis" ADHD OR ASD (thread OR Q&A) lang:en',
         '{"prompt_version":"v1.0","k_terms":["self diagnosis","ADHD","ASD"],"notes":"X/Twitter v2"}'::jsonb
  FROM targets t WHERE t.title = 'Clinical vs self-diagnosis of ADHD/ASD/AuDHD'

  UNION ALL
  SELECT t.seed_id, 'youtube', 'ADHD coping strategies routines sensory regulation site:youtube.com',
         '{"prompt_version":"v1.0","k_terms":["coping","executive function","sensory"]}'::jsonb
  FROM targets t WHERE t.title = 'Pop psychology coping strategies (ND daily management)'

  UNION ALL
  SELECT t.seed_id, 'reddit', 'CBT tips ADHD executive dysfunction site:reddit.com',
         '{"prompt_version":"v1.0","k_terms":["CBT","executive dysfunction","tips"]}'::jsonb
  FROM targets t WHERE t.title = 'Pop psychology coping strategies (ND daily management)'

  UNION ALL
  SELECT t.seed_id, 'youtube', 'DREADDs chemogenetics autism circuit modulation site:youtube.com',
         '{"prompt_version":"v1.0","k_terms":["DREADDs","chemogenetics","circuit"]}'::jsonb
  FROM targets t WHERE t.title = 'Chemogenetics (DREADDs) & circuit modulation'

  UNION ALL
  SELECT t.seed_id, 'x', 'DREADD OR chemogenetic autism trial (preprint OR paper) lang:en',
         '{"prompt_version":"v1.0","k_terms":["DREADD","chemogenetic","trial"],"notes":"paper/preprint surfacing"}'::jsonb
  FROM targets t WHERE t.title = 'Chemogenetics (DREADDs) & circuit modulation'

  UNION ALL
  SELECT t.seed_id, 'youtube', 'EEG biomarkers ADHD ASD ML site:youtube.com',
         '{"prompt_version":"v1.0","k_terms":["EEG","biomarkers","ML","ADHD","ASD"]}'::jsonb
  FROM targets t WHERE t.title = 'AI + neuroimaging/EEG for diagnostic support'

  UNION ALL
  SELECT t.seed_id, 'reddit', 'fMRI pattern ADHD ASD generalization site:reddit.com',
         '{"prompt_version":"v1.0","k_terms":["fMRI","pattern","generalization"]}'::jsonb
  FROM targets t WHERE t.title = 'AI + neuroimaging/EEG for diagnostic support'

  UNION ALL
  SELECT t.seed_id, 'youtube', 'new ADHD drug trial 2024 2025 site:youtube.com',
         '{"prompt_version":"v1.0","k_terms":["pharma","trial","ADHD","2024","2025"]}'::jsonb
  FROM targets t WHERE t.title = 'Pharmaceutical innovation and clinical trials'

  UNION ALL
  SELECT t.seed_id, 'x', '(guanfacine OR modafinil) ADHD randomized trial lang:en',
         '{"prompt_version":"v1.0","k_terms":["guanfacine","modafinil","randomized"],"notes":"trial mentions"}'::jsonb
  FROM targets t WHERE t.title = 'Pharmaceutical innovation and clinical trials'
)
INSERT INTO public.search_queries (seed_id, platform, query_text, gen_meta)
SELECT seed_id, platform, query_text, gen_meta
FROM q
ON CONFLICT (seed_id, platform, query_text) DO NOTHING;

-- 3) Optional: one placeholder preview row for traceability (YouTube example)
INSERT INTO public.previews (seed_id, platform, url, title, snippet, author, published_at, raw_meta, score)
SELECT s.seed_id,
       'youtube',
       'https://www.youtube.com/watch?v=dummy123',
       'Clinical vs Self-Diagnosis: ADHD/ASD Explained',
       'Explainer discussing differences between clinical assessment and self-identification.',
       'Channel ND Insights',
       NOW() - INTERVAL '10 days',
       '{"channelId":"demo-channel","viewCount": 12345}'::jsonb,
       0.65
FROM public.seeds_table s
WHERE s.seed_topic = 'Neuroscience of Mental Health'
  AND s.title = 'Clinical vs self-diagnosis of ADHD/ASD/AuDHD'
ON CONFLICT (platform, url) DO NOTHING;

COMMIT;
