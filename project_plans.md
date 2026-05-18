# Portfolio Project Plans

Four production-quality portfolio projects. Each scoped for solo build, free tiers only, deployable, and signal-rich for HR/hiring managers.

---

## Project 1: TechPulse — HN Tech Trend Radar

### The Problem

Most "data pipeline" portfolio projects are either toy ETL scripts with no UI, or dashboards with no real pipeline behind them. Hiring managers cannot tell if you understand the full lifecycle: ingestion, transformation, storage, and serving. The gap is **end-to-end ownership** — plus analytical depth that proves you can extract signal from noise.

### The Solution

A tech trend intelligence platform that ingests Hacker News stories and comments daily via the Algolia HN API (free, no key required), runs keyword detection across a curated taxonomy of 150+ tech terms, computes weekly "hype scores" per technology, and serves a live dashboard showing which technologies are rising, peaking, or dying — with anomaly detection that flags overnight viral spikes.

**Why this beats WeatherFlow:** weather data is passive — the insight is obvious (temperature anomaly). TechPulse requires *building* the signal: defining what "trending" means, extracting keywords from unstructured text, combining frequency + engagement + recency into a composite score. That's analytical maturity, not just SQL.

**Why this beats a generic dashboard:** it has a defined data contract (raw stories → keyword events → weekly aggregates → trend scores), a daily scheduler proving unattended operation, an NLP layer proving text processing skills, and a feature (hype cycle visualization) that hiring managers at tech companies will actually use and share.

**Gaps to address:**
- HN Algolia API rate limit: 10,000 req/hr (generous). Solution: batch daily fetches by timestamp window, store `last_fetched_at` in DuckDB, always fetch incrementally.
- Backfill (2 years of HN = ~2M stories): Solution: run once with a date-range loop, ~200 API calls at 1,000 stories/call — completes in under 5 minutes.
- DuckDB is local-only by default. Solution: commit pre-loaded `.duckdb` file to repo (LFS), mount in Streamlit Cloud — or use MotherDuck free tier (10 GB).
- Streamlit redeploys kill in-memory state. Solution: write all state to DuckDB, never rely on session.
- Keyword false positives ("Go" matching "going", "Rust" matching "rusty"). Solution: word-boundary regex + context window (require adjacent tech noun within 5 tokens for ambiguous terms).

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Ingestion | Python + `httpx` (async) | Async HTTP, lightweight, same pattern as prod pipelines |
| Keyword detection | Custom taxonomy dict + regex | Fast, deterministic, fully auditable — no black-box NLP |
| Emerging term detection | sklearn TF-IDF on weekly corpus | Catches unlisted tech rising in comments before it's famous |
| Orchestration | Prefect Cloud (free tier) | Prod-grade scheduler, visual run history, impresses in screenshots |
| Transform | DuckDB SQL + Pandas | Weekly aggregation, hype score, rolling avg — all in SQL |
| Storage | DuckDB (file-based) | Zero infra, columnar, analytics-native |
| Anomaly detection | Z-score (scipy.stats) | Flags overnight viral spikes — same method, richer domain |
| UI | Streamlit | Fast to build, free cloud deploy |
| Deploy | Streamlit Cloud (free) | One-click from GitHub |

**Why not spaCy/BERT for keyword extraction?** Overkill. A curated regex taxonomy is faster, more predictable, and easier to explain in an interview. Add TF-IDF for discovery of unlisted terms — that's the smart layer, not the brute-force layer.

**Why not Postgres?** DuckDB runs analytical queries 10–100× faster on flat files. For a portfolio project, this is the correct tool.

**Why HN over Reddit?** HN Algolia API is cleaner, free without OAuth, and the audience (developers) makes keyword signal much higher quality. Reddit requires app registration, OAuth, and has lower signal-to-noise for tech terms.

### General Flow

```
[Prefect Scheduler — daily at 06:00 UTC]
        ↓
[Fetch: HN Algolia API → all stories since last_fetched_at]
        ↓
[Validate: schema check, dedup on story_id, drop null titles]
        ↓
[Detect: scan title + URL domain → match against 150+ tech keyword taxonomy]
        ↓
[Enrich: attach story score, comment_count, created_at to each keyword hit]
        ↓
[Write: DuckDB → raw_stories, keyword_events]
        ↓
[Aggregate: weekly rollup → mention_count, weighted_score, avg_comments per keyword]
        ↓
[Score: hype_score = 0.5×mentions + 0.3×weighted_score + 0.2×avg_comments (normalized 0–100)]
        ↓
[Anomaly: rolling 12-week avg + z-score → flag |z| > 2 as trending/crashing]
        ↓
[Write: DuckDB → weekly_mentions, keyword_velocity, anomalies]
        ↓
[Streamlit reads DuckDB → hype cycle chart, velocity heatmap, anomaly feed, keyword compare]
```

### DuckDB Schema

```sql
-- Raw layer
raw_stories (
  story_id      INTEGER PRIMARY KEY,
  title         TEXT NOT NULL,
  url           TEXT,
  score         INTEGER,        -- HN upvotes
  num_comments  INTEGER,
  created_at    TIMESTAMP,
  fetched_at    TIMESTAMP
)

-- Keyword event layer (one row per keyword hit per story)
keyword_events (
  story_id      INTEGER,
  keyword       TEXT,           -- e.g. "Rust", "Next.js", "Kubernetes"
  category      TEXT,           -- Language / Framework / Tool / AI / Company
  score         INTEGER,        -- story score at detection time
  created_at    TIMESTAMP
)

-- Aggregated layer
weekly_mentions (
  keyword       TEXT,
  iso_week      TEXT,           -- e.g. "2024-W03"
  mention_count INTEGER,
  weighted_score FLOAT,         -- sum(score) / mention_count
  avg_comments  FLOAT,
  hype_score    FLOAT           -- 0–100 composite
)

-- Trend/anomaly layer
keyword_velocity (
  keyword       TEXT,
  iso_week      TEXT,
  velocity      FLOAT,          -- week-over-week % change in hype_score
  rolling_avg   FLOAT,          -- 12-week rolling average
  z_score       FLOAT,
  is_trending   BOOLEAN,        -- z > 2
  is_crashing   BOOLEAN         -- z < -2
)
```

### Keyword Taxonomy (excerpt)

```python
TAXONOMY = {
    "Languages":   ["Python", "Rust", "Go", "TypeScript", "JavaScript", "Zig", "Kotlin", "Swift", "Elixir", "Haskell"],
    "Frameworks":  ["Next.js", "FastAPI", "Django", "Rails", "Spring", "Svelte", "Remix", "Astro", "Laravel"],
    "Tools":       ["Docker", "Kubernetes", "Terraform", "dbt", "Kafka", "Airflow", "Prefect", "Grafana"],
    "AI/ML":       ["LLM", "GPT", "Claude", "Gemini", "PyTorch", "JAX", "Ollama", "RAG", "fine-tuning"],
    "Platforms":   ["Supabase", "Vercel", "Railway", "Fly.io", "MotherDuck", "Neon", "PlanetScale"],
    "Companies":   ["Anthropic", "OpenAI", "Google DeepMind", "Mistral", "Hugging Face"],
}

# Ambiguous terms requiring word-boundary + context check
AMBIGUOUS = {"Go": r"\bGo\b(?!\s+(to|ahead|back|through))", "Rust": r"\bRust\b(?!y\b)"}
```

### Build Phases

---

**Phase 1 — Foundation & Ingestion (Days 1–2)**

Goal: raw stories flowing into DuckDB, incrementally, reliably.

1. Init project with `uv init hn-tech-radar`, add deps: `httpx`, `duckdb`, `pandas`, `prefect`, `scipy`, `sklearn`
2. Create `src/` layout: `ingestion/`, `transforms/`, `dashboard/`, `tests/`
3. Implement `HNClient` in `ingestion/client.py`:
   - Method: `fetch_stories(since_ts: int, page_size=1000) -> list[dict]`
   - Endpoint: `https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=created_at_i>{ts}&hitsPerPage={page_size}`
   - Handle pagination: loop until `nbPages` exhausted or `created_at` exceeds now
   - Retry: exponential backoff on 429/5xx (3 retries max)
4. Create `storage/db.py` — `DuckDBStore`:
   - Method: `init_schema()` — creates all 4 tables if not exist
   - Method: `get_last_fetched_at() -> int` — reads `max(created_at)` from `raw_stories`
   - Method: `insert_stories(stories: list[dict])` — bulk insert with `ON CONFLICT DO NOTHING`
5. Implement `ingestion/backfill.py`:
   - Fetch from 2 years ago to now in 7-day windows
   - Log progress: `Fetched week 2022-W01: 14,302 stories`
   - Run once, idempotent (dedup on `story_id`)
6. Implement `ingestion/incremental.py`:
   - Call `get_last_fetched_at()`, fetch only new stories, insert
   - Log: `Fetched 847 new stories since 2024-01-15 06:00 UTC`
7. Verify: `duckdb hn.duckdb -c "SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM raw_stories"`
8. Write `tests/test_client.py`: mock httpx → assert correct pagination, retry on 429, schema of returned dicts

---

**Phase 2 — Keyword Detection System (Days 3–4)**

Goal: every story tagged with matching tech keywords, false positives eliminated.

1. Create `transforms/taxonomy.py`:
   - Define `TAXONOMY` dict (6 categories, 150+ terms)
   - Define `AMBIGUOUS` dict with context-aware regex patterns
   - Export: `ALL_KEYWORDS: list[str]`, `KEYWORD_TO_CATEGORY: dict[str, str]`
2. Implement `transforms/detector.py`:
   - Function: `detect_keywords(title: str, url: str) -> list[str]`
   - For non-ambiguous terms: `re.search(r'\b{kw}\b', text, re.IGNORECASE)`
   - For ambiguous terms: use regex from `AMBIGUOUS` dict
   - URL domain extraction: `"github.com/rust-lang/rust"` → extract "Rust" from domain path
   - Return deduplicated list of matched keywords
3. Implement `transforms/keyword_pipeline.py`:
   - Read `raw_stories` where `story_id NOT IN (SELECT story_id FROM keyword_events)`
   - Batch process 10,000 stories at a time
   - For each story: call `detect_keywords(title, url)`
   - Write results to `keyword_events` (one row per keyword hit)
4. Implement emerging term detection (`transforms/tfidf_discovery.py`):
   - Weekly: collect all story titles from that week
   - Run `TfidfVectorizer(ngram_range=(1,2), min_df=5)` on corpus
   - Extract top-20 terms NOT already in taxonomy
   - Write to `emerging_terms` table (keyword, week, tfidf_score) for manual review
   - This shows up in dashboard as "Watch List" — terms gaining traction before they're famous
5. Write `tests/test_detector.py`:
   - `"Rust is memory safe"` → assert `["Rust"]` detected
   - `"Getting rusty at piano"` → assert `[]` (no false positive)
   - `"Going to use Go for this"` → assert `["Go"]` (word boundary, not "going")
   - `"github.com/astral-sh/uv"` → assert `["uv"]` via URL path
   - `"Next.js 14 released"` → assert `["Next.js"]`

---

**Phase 3 — Aggregation, Scoring & Anomaly Detection (Days 5–6)**

Goal: weekly hype scores and z-score anomaly flags in DuckDB.

1. Implement `transforms/weekly_agg.py` — SQL via DuckDB:
   ```sql
   INSERT OR REPLACE INTO weekly_mentions
   SELECT
     keyword,
     strftime(created_at, '%Y-W%W') AS iso_week,
     COUNT(*)                        AS mention_count,
     SUM(score) / COUNT(*)           AS weighted_score,
     AVG(num_comments)               AS avg_comments
   FROM keyword_events ke
   JOIN raw_stories rs USING (story_id)
   WHERE strftime(rs.created_at, '%Y-W%W') = ?  -- current ISO week
   GROUP BY keyword, iso_week
   ```
2. Implement `transforms/hype_score.py`:
   - Per keyword per week: normalize each metric to 0–100 across all keywords that week
   - `hype_score = 0.5 * norm_mentions + 0.3 * norm_weighted_score + 0.2 * norm_avg_comments`
   - Update `weekly_mentions.hype_score` column
   - Rationale for weights: mentions = volume signal, weighted_score = quality signal (high-score stories = HN community validation), avg_comments = engagement signal
3. Implement `transforms/velocity.py`:
   - For each keyword, read last 13 weeks of `hype_score`
   - Compute `velocity = (this_week - last_week) / last_week * 100` (% change)
   - Compute `rolling_avg = avg(hype_score over 12 weeks)`
   - Compute `z_score = (this_week - rolling_avg) / std(hype_score over 12 weeks)`
   - Write to `keyword_velocity`
   - Set `is_trending = z_score > 2`, `is_crashing = z_score < -2`
4. Write `tests/test_aggregation.py`:
   - Inject 10 known stories with known keywords and scores
   - Assert `weekly_mentions` row has correct `mention_count`, `weighted_score`
   - Assert `hype_score` within expected range (0–100)
5. Write `tests/test_anomaly.py`:
   - Inject 12 weeks of baseline data (hype_score ~20 each week)
   - Inject week 13 with hype_score 80 (spike)
   - Assert `z_score > 2` and `is_trending = True` for that keyword/week
   - Assert non-spiked keywords have `is_trending = False`

---

**Phase 4 — Orchestration (Day 7)**

Goal: fully automated daily pipeline with failure alerts.

1. Create `pipeline/flow.py` — Prefect flow:
   ```python
   @flow(name="hn-tech-radar-daily")
   def daily_pipeline():
       fetch_new_stories()        # task: incremental HN fetch
       run_keyword_detection()    # task: detect keywords on new stories
       recompute_weekly_agg()     # task: recompute last 2 weeks (current + previous)
       update_hype_scores()       # task: normalize + score
       update_velocity()          # task: z-score + anomaly flags
       run_quality_checks()       # task: assert data quality
   ```
2. Each step is a `@task` with `retries=3, retry_delay_seconds=60`
3. Implement `run_quality_checks()`:
   - Assert `new_stories_count > 0` (fail if HN API returned nothing)
   - Assert `keyword_events` count increased (fail if detector produced zero hits)
   - Assert `MAX(created_at)` in `raw_stories` is within 26 hours of now
   - On assertion failure: raise `ValueError` → Prefect marks run as FAILED
4. Deploy to Prefect Cloud:
   - `prefect deploy pipeline/flow.py:daily_pipeline --name prod`
   - Schedule: `0 6 * * *` (06:00 UTC daily)
5. Configure failure webhook:
   - Prefect → Automations → On flow run failure → POST to Discord/Slack webhook
   - Message: `"TechPulse pipeline FAILED at {step}. Run ID: {run_id}"`
6. Verify: trigger manual run in Prefect Cloud UI, confirm all tasks green, check DuckDB row counts increased

---

**Phase 5 — Dashboard (Days 8–9)**

Goal: a dashboard hiring managers actually want to explore.

1. Create `dashboard/app.py` — Streamlit layout:
   ```
   Sidebar:
     - Category filter: All / Languages / Frameworks / Tools / AI / Platforms
     - Time window: Last 4 weeks / 12 weeks / 1 year / All time
     - Last pipeline run: {timestamp} ({N} new stories)

   Main — 3 tabs:
     Tab 1: Trending Now
     Tab 2: Hype Cycles
     Tab 3: Emerging Terms
   ```

2. **Tab 1 — Trending Now:**
   - "This Week's Risers": top 5 keywords by `velocity`, shown as metric cards with sparkline (last 8 weeks)
   - "This Week's Fallers": bottom 5 by velocity, same format
   - Anomaly feed: table of all `is_trending=True` events this week — keyword, z_score, link to top 3 HN stories that drove the spike
   - Story links: join `keyword_events` back to `raw_stories` to get HN URLs (`https://news.ycombinator.com/item?id={story_id}`)

3. **Tab 2 — Hype Cycles:**
   - Multi-keyword selector (default: Python, Rust, Go, TypeScript)
   - Line chart: x=iso_week, y=hype_score, one line per keyword (Altair/Plotly)
   - Overlay anomaly markers: red dot on weeks where `is_trending=True`
   - "Compare" mode: select exactly 2 keywords → show their hype cycle overlaid, highlight divergence weeks
   - Insight box: auto-generated text: `"Rust peaked in W03 2024 (z=3.2) following Linus Torvalds' Linux kernel comment"`

4. **Tab 3 — Emerging Terms:**
   - Table of top TF-IDF discovered terms this week (not in taxonomy)
   - Columns: term, first_seen_week, mention_count, top 3 story titles
   - Purpose: show the "discovery" layer — you're detecting the next Zig before it's famous

5. Add `@st.cache_data(ttl=3600)` on all DuckDB query functions — Streamlit re-runs on interaction, caching prevents repeated DB hits

6. Write `tests/test_dashboard.py` (Streamlit testing is limited — test the query layer):
   - `get_trending_keywords(week="2024-W03")` → assert returns list of dicts with expected keys
   - `get_hype_cycle(keyword="Rust", n_weeks=12)` → assert 12 rows, no nulls in hype_score

---

**Phase 6 — Polish, Deploy & Portfolio Assets (Day 10)**

Goal: the thing that gets you interviews.

1. Run backfill for 2 full years of HN data — commit resulting `.duckdb` file to repo via Git LFS (or upload to GitHub Release as asset, download in Streamlit `startup.sh`)
2. Deploy to Streamlit Cloud:
   - Set `DUCKDB_PATH` env var
   - `startup.sh`: download pre-loaded DuckDB if not present
3. README must contain:
   - Mermaid architecture diagram (copy from General Flow above)
   - Screenshot of Trending Now tab with real data
   - Screenshot of Hype Cycles tab showing Rust vs Go vs Python (3-year view)
   - "How hype score works" section — explain the formula, justify weights
   - "Anomaly detection" section — explain z-score, show a real historical spike (e.g., ChatGPT launch week in HN data)
   - Live demo link + Prefect run history screenshot
4. Add `ARCHITECTURE.md`:
   - Data lineage: `raw_stories → keyword_events → weekly_mentions → keyword_velocity`
   - Keyword taxonomy design rationale
   - Why TF-IDF for emerging terms vs. pure taxonomy
5. Performance verification:
   - Query `weekly_mentions` for 2-year range: assert < 500ms
   - Dashboard cold load on Streamlit Cloud: assert < 3s
   - Run `pytest` — all tests green — screenshot for README

### Success Metrics / Test Suite

**Functional tests**
- `test_client.py`: mock HTTP → assert correct pagination, retry on 429, dedup on story_id
- `test_detector.py`: 20 known title/URL pairs → assert correct keywords, zero false positives on ambiguous terms
- `test_aggregation.py`: known input data → assert `mention_count`, `weighted_score`, `hype_score` correct
- `test_anomaly.py`: inject synthetic spike → assert flagged at |z| > 2, non-spikes not flagged

**Pipeline health metrics**
- Pipeline success rate: 95%+ over 30-day period (Prefect dashboard shows this)
- Data freshness: `MAX(created_at)` in `raw_stories` < 26 hours ago (shown in UI sidebar)
- Story count assertion: each daily run must produce ≥ 100 new stories (fail if API returns empty)
- Keyword hit rate: ≥ 15% of stories must match at least 1 keyword (fail if detector is broken)

**Performance**
- Dashboard cold load < 3s (Streamlit Cloud)
- `weekly_mentions` query over 2-year range < 500ms (DuckDB columnar)
- Keyword detection on 10,000 stories < 5s (regex on CPU)

**Portfolio signal**
- Architecture diagram in README (proves systems thinking)
- Prefect run history screenshot (proves it ran unattended — most candidates fake this)
- Hype score formula explanation (proves analytical thinking, not just plumbing)
- Anomaly example with real historical data (ChatGPT launch week is visible in the data — use it)
- TF-IDF "emerging terms" section in README (proves you layered an additional intelligence beyond the obvious approach)

---

## Project 2: DataVault — dbt + DuckDB Analytics Engineering Project

### The Problem

"Analytics engineer" and "data engineer" roles increasingly require **dbt** as table stakes. Most candidates list it on a resume but have no project proving they can model data correctly: staging, intermediate, mart layers; tests; documentation; incremental models. Hiring managers who know dbt will immediately check if you understand the medallion pattern.

### The Solution

Take a rich public dataset — **TransJakarta BRT transaction data** (Kaggle, public domain, April 2023, ~37k rows) — and build a full dbt project on top of DuckDB that models it correctly. The deliverable: a Streamlit analytics dashboard showing ridership patterns, corridor-level revenue, surge-hour demand analysis, and stop performance metrics.

**The creative angle:** build a `mart_stop_performance` model — a composite score (0–100) per tap-in bus stop using throughput volume, revenue density, and gender diversity index. Realistic transit operations metric, shows modeling maturity, and maps directly to columns available in the dataset.

**Why TransJakarta over NYC Taxi:**
- Real Indonesian data — differentiates portfolio from 10,000 identical taxi projects
- Has demographic context (age, gender per transaction) — richer analytical story
- Has geolocation (lat/lon per stop) — enables spatial analysis without external GeoJSON
- Dataset is ~5MB committed directly to repo — no download scripts needed in CI
- Stop → corridor → direction hierarchy mirrors real transit data structures hiring managers see

**Feasibility notes:**
- Full dataset is ~37k rows (small). It is committed directly to `data/raw/`. No download step needed in CI.
- Seeds (`stops.csv`, `corridors.csv`) are generated once via `scripts/generate_seeds.py` and committed.
- `dbt-expectations` replaces `Great Expectations` — same test vocabulary, zero extra infra, installs via `packages.yml`.
- `plotly` replaces `pydeck` — no Mapbox token required, scatter_mapbox works with open tiles.

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Package mgr | uv | Fast, lockfile-based, modern |
| Raw data | TransJakarta April 2023 CSV (Kaggle) | Free, real Indonesian data, committed to repo |
| Transform | dbt-core 1.8 + dbt-duckdb 1.8 | Industry standard AE stack |
| dbt packages | dbt-utils 1.x + dbt-expectations 0.10.x | Extended tests without extra infra |
| Storage | DuckDB 1.1 | Native Parquet reader, columnar, no server |
| Python tests | pytest 7.x | Unit tests on scripts/utilities |
| Charts | plotly 5.x | Choropleth + line + heatmap, zero API keys |
| Dashboard | Streamlit 1.39.x | Fast, free cloud deploy |
| CI | GitHub Actions (free tier) | `dbt build` on PR, sample data only |
| Docs | dbt docs → GitHub Pages | Free, impressive, shows documentation culture |
| Deploy | Streamlit Cloud (free) | One-click from GitHub |

**Why dbt-expectations over Great Expectations?** GE requires a separate context, checkpoint YAML, and often a data store. `dbt-expectations` is a dbt package — install in `packages.yml`, use in schema tests like native dbt tests. Zero extra infra, same vocabulary, easier to demonstrate.

**Why not Snowflake/BigQuery?** DuckDB is portable, zero-infra, runs in CI for free, and is production-used (MotherDuck). Correct tool, not the impressive-sounding tool.

### Data Schema (TransJakarta April 2023 — actual columns)

```
transID          — transaction ID
payCardID        — anonymized card ID
payCardBank      — issuing bank (BCA, BNI, BRI, DKI, MANDIRI, etc.)
payCardName      — cardholder name (anonymized)
payCardSex       — gender: L (Male) or P (Female)
payCardAge       — cardholder age
corridorID       — corridor code (e.g. "1", "T11", "JAK.1")
corridorName     — corridor full name (e.g. "Blok M - Kota")
direction        — 0 or 1 (travel direction on corridor)
tapInStops       — tap-in stop ID
tapInStopsName   — tap-in stop name
tapInStopsLat    — tap-in stop latitude
tapInStopsLon    — tap-in stop longitude
tapOutStops      — tap-out stop ID (nullable — missed tap-out)
tapOutStopsName  — tap-out stop name (nullable)
tapOutStopsLat   — tap-out stop latitude (nullable)
tapOutStopsLon   — tap-out stop longitude (nullable)
stopStartSeq     — sequence position of tap-in stop on corridor
stopEndSeq       — sequence position of tap-out stop (nullable)
tapInTime        — tap-in timestamp
tapOutTime       — tap-out timestamp (nullable)
payAmount        — fare paid (IDR)
```

### General Flow

```
[data/raw/transjakarta.csv — committed to repo, ~5MB]
        ↓ scripts/load_raw.py (DuckDB view via read_csv)
[raw_transjakarta — DuckDB view, ~37k rows]
        ↓ scripts/generate_seeds.py (run once, output committed)
[seeds/stops.csv — unique stops with lat/lon]
[seeds/corridors.csv — unique corridors]
        ↓ dbt seed
[stg_stops — from seeds/stops.csv]
[stg_corridors — from seeds/corridors.csv]
        ↓ dbt build staging/
[stg_transactions — cleaned, cast, filtered (null tap-out removed)]
        ↓ dbt build intermediate/
[int_trips_enriched — duration, distance (Haversine), hour/day features, gender/age]
        ↓ dbt build marts/
[mart_daily_ridership  — daily trips + revenue by corridor]
[mart_corridor_flow    — O-D matrix between corridors]
[mart_stop_performance — per-stop composite score 0-100]
[mart_surge_analysis   — hour × day × corridor demand heatmap]
        ↓ dbt test
[all schema + custom + dbt-expectations tests pass]
        ↓ GitHub Actions CI (same CSV, no download needed)
[dbt build exits 0 → upload mart DuckDB artifact]
        ↓ Streamlit reads mart tables
[dashboard: 4 tabs — Overview, Corridor Flow, Stop Score, Surge]
```

---

### Build Phases

---

#### Phase 1 — Project Foundation & Raw Data Pipeline (Days 1–2)

**Goal:** reproducible project scaffold, raw data loaded into DuckDB, `dbt debug` passes.

**Step-by-step:**

1. Init project:
   ```bash
   uv init datavault
   cd datavault
   uv add dbt-core dbt-duckdb dbt-utils dbt-expectations streamlit plotly pandas pytest httpx
   ```

2. Create directory structure:
   ```
   datavault_dbt/  scripts/  dashboard/  tests/  data/raw/  data/sample/
   ```

3. Init dbt project (run inside repo root):
   ```bash
   uv run dbt init datavault_dbt --skip-profile-setup
   ```

4. Create `profiles.yml` in repo root (not `~/.dbt/`):
   ```yaml
   datavault:
     target: dev
     outputs:
       dev:
         type: duckdb
         path: "{{ env_var('DUCKDB_PATH', 'datavault.duckdb') }}"
         threads: 4
   ```

5. Update `datavault_dbt/dbt_project.yml`:
   - `profile: datavault`
   - model materializations: staging → view, intermediate → view, marts → table
   - `model-paths: ["models"]`, `seed-paths: ["seeds"]`, `test-paths: ["tests"]`

6. Create `datavault_dbt/packages.yml`:
   ```yaml
   packages:
     - package: dbt-labs/dbt_utils
       version: [">=1.0.0", "<2.0.0"]
     - package: calogica/dbt_expectations
       version: [">=0.10.0", "<0.11.0"]
   ```
   Run `uv run dbt deps`

7. Place raw data:
   - Download from Kaggle: `kaggle datasets download -d dikasiganteng/transjakarta --unzip -p data/raw/`
   - Rename the downloaded CSV to `data/raw/transjakarta.csv`
   - Commit to repo: `git add data/raw/transjakarta.csv`

8. Create `scripts/generate_seeds.py`:
   - Read `data/raw/transjakarta.csv`
   - Extract unique stops → write `datavault_dbt/seeds/stops.csv` (columns: stop_id, stop_name, lat, lon)
   - Extract unique corridors → write `datavault_dbt/seeds/corridors.csv` (columns: corridor_id, corridor_name)
   - Commit both seed CSVs

9. Create `scripts/load_raw.py`:
   - Creates DuckDB view: `CREATE OR REPLACE VIEW raw_transjakarta AS SELECT * FROM read_csv('data/raw/transjakarta.csv', auto_detect=true)`
   - Logs row count, min/max tapInTime

10. Create `scripts/verify_raw.py`:
    - Connects to DuckDB
    - Asserts: row_count > 30_000
    - Asserts: null rate in tapInTime < 0.01
    - Asserts: null rate in payAmount < 0.01
    - Asserts: all expected columns present
    - Prints summary table

11. Run `uv run dbt seed --profiles-dir .` → verify stops + corridors rows
12. Run `uv run dbt debug --profiles-dir .` → all checks pass

**Commit breakdown (Phase 1):**
```
chore: init uv project with dbt-core, dbt-duckdb, plotly, streamlit deps
chore: init dbt project structure with profiles.yml and dbt_project.yml
chore: add dbt-utils and dbt-expectations packages, run dbt deps
feat: add raw TransJakarta CSV to data/raw/ (~37k rows, April 2023)
feat: add generate_seeds.py and commit stops.csv + corridors.csv seeds
feat: add load_raw.py creating DuckDB view over transjakarta CSV
feat: add verify_raw.py sanity check script with column + row assertions
feat: add test_phase1.py pytest suite
docs: update .gitignore for datavault.duckdb, __pycache__, dbt target/
```

**Phase 1 Test Suite & Expected Results:**

```bash
# Test 1: dbt debug
uv run dbt debug --project-dir datavault_dbt --profiles-dir .
# Expected: All checks passed.

# Test 2: dbt seed
uv run dbt seed --project-dir datavault_dbt --profiles-dir .
# Expected:
#   1 of 2 START seed file datavault_dbt.stops ...................... [RUN]
#   1 of 2 OK loaded seed file datavault_dbt.stops .................. [INSERT NNN in Xs]
#   2 of 2 START seed file datavault_dbt.corridors .................. [RUN]
#   2 of 2 OK loaded seed file datavault_dbt.corridors .............. [INSERT NN in Xs]
#   Completed successfully

# Test 3: verify raw data
uv run python scripts/verify_raw.py
# Expected output:
#   Raw view row count: 37,900 (approx)
#   Null rate tapInTime:   0.00%
#   Null rate payAmount:   0.00%
#   All expected columns:  PASS
#   Summary: ALL CHECKS PASSED

# Test 4: pytest
uv run pytest tests/test_phase1.py -v
# Expected:
#   tests/test_phase1.py::test_raw_csv_exists PASSED
#   tests/test_phase1.py::test_stops_seed_exists PASSED
#   tests/test_phase1.py::test_corridors_seed_exists PASSED
#   tests/test_phase1.py::test_profiles_yml_valid PASSED
#   tests/test_phase1.py::test_dbt_project_yml_valid PASSED
#   tests/test_phase1.py::test_raw_csv_row_count PASSED
#   tests/test_phase1.py::test_raw_csv_required_columns PASSED
#   7 passed in Xs
```

**pytest file `tests/test_phase1.py`:**
```python
import pytest
import yaml
import duckdb
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW_CSV = ROOT / "data/raw/transjakarta.csv"
REQUIRED_COLS = [
    "transID", "payCardBank", "payCardSex", "payCardAge",
    "corridorID", "corridorName", "direction",
    "tapInStops", "tapInStopsName", "tapInStopsLat", "tapInStopsLon",
    "tapOutStops", "tapInTime", "tapOutTime", "payAmount",
]

def test_raw_csv_exists():
    assert RAW_CSV.exists(), "data/raw/transjakarta.csv not found"

def test_stops_seed_exists():
    assert (ROOT / "datavault_dbt/seeds/stops.csv").exists()

def test_corridors_seed_exists():
    assert (ROOT / "datavault_dbt/seeds/corridors.csv").exists()

def test_profiles_yml_valid():
    p = ROOT / "profiles.yml"
    assert p.exists()
    cfg = yaml.safe_load(p.read_text())
    assert "datavault" in cfg
    assert cfg["datavault"]["outputs"]["dev"]["type"] == "duckdb"

def test_dbt_project_yml_valid():
    p = ROOT / "datavault_dbt/dbt_project.yml"
    cfg = yaml.safe_load(p.read_text())
    assert cfg["profile"] == "datavault"
    assert cfg["models"]["datavault_dbt"]["marts"]["+materialized"] == "table"

def test_raw_csv_row_count():
    con = duckdb.connect()
    n = con.execute(f"SELECT COUNT(*) FROM read_csv('{RAW_CSV}', auto_detect=true)").fetchone()[0]
    assert n > 30_000, f"Expected >30k rows, got {n}"

def test_raw_csv_required_columns():
    con = duckdb.connect()
    df = con.execute(f"SELECT * FROM read_csv('{RAW_CSV}', auto_detect=true) LIMIT 1").fetchdf()
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"
```

---

#### Phase 2 — Staging Layer (Days 3–4)

**Goal:** clean, typed, filtered staging models with full schema test coverage.

**Models to create:**

`models/staging/stg_yellow_trips.sql`:
```sql
WITH source AS (
    SELECT * FROM {{ source('tlc', 'raw_yellow_trips') }}
),
renamed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['VendorID', 'tpep_pickup_datetime', 'PULocationID', 'DOLocationID', 'total_amount']) }} AS trip_id,
        CAST(VendorID AS INTEGER)                  AS vendor_id,
        CAST(tpep_pickup_datetime AS TIMESTAMP)    AS pickup_at,
        CAST(tpep_dropoff_datetime AS TIMESTAMP)   AS dropoff_at,
        CAST(passenger_count AS INTEGER)           AS passenger_count,
        CAST(trip_distance AS DOUBLE)              AS trip_distance_miles,
        CAST(RatecodeID AS INTEGER)                AS rate_code_id,
        CAST(PULocationID AS INTEGER)              AS pickup_location_id,
        CAST(DOLocationID AS INTEGER)              AS dropoff_location_id,
        CAST(payment_type AS INTEGER)              AS payment_type,
        CAST(fare_amount AS DOUBLE)                AS fare_amount,
        CAST(tip_amount AS DOUBLE)                 AS tip_amount,
        CAST(tolls_amount AS DOUBLE)               AS tolls_amount,
        CAST(total_amount AS DOUBLE)               AS total_amount,
        CAST(congestion_surcharge AS DOUBLE)       AS congestion_surcharge,
        CAST(Airport_fee AS DOUBLE)                AS airport_fee
    FROM source
    WHERE
        tpep_pickup_datetime IS NOT NULL
        AND tpep_dropoff_datetime IS NOT NULL
        AND total_amount IS NOT NULL
        AND fare_amount > 0
        AND trip_distance > 0
        AND passenger_count BETWEEN 1 AND 9
        AND tpep_dropoff_datetime > tpep_pickup_datetime
        AND DATEDIFF('minute', tpep_pickup_datetime, tpep_dropoff_datetime) BETWEEN 1 AND 360
)
SELECT * FROM renamed
```

`models/staging/stg_taxi_zones.sql`:
```sql
SELECT
    CAST(location_id AS INTEGER)  AS location_id,
    borough,
    zone,
    service_zone
FROM {{ ref('taxi_zones') }}
WHERE location_id IS NOT NULL
```

`models/staging/_stg_yellow_trips.yml` (schema + tests):
```yaml
version: 2
models:
  - name: stg_yellow_trips
    description: "Cleaned yellow taxi trips Jan–Mar 2024. Filters invalid rows."
    columns:
      - name: trip_id
        description: "Surrogate key: vendor+pickup_ts+pu_loc+do_loc+amount"
        tests:
          - not_null
          - unique
      - name: vendor_id
        tests:
          - not_null
          - accepted_values:
              values: [1, 2]
      - name: pickup_at
        tests:
          - not_null
      - name: dropoff_at
        tests:
          - not_null
      - name: passenger_count
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 1
              max_value: 9
      - name: fare_amount
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0.01
              max_value: 1000
      - name: trip_distance_miles
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0.01
              max_value: 200
      - name: payment_type
        tests:
          - accepted_values:
              values: [1, 2, 3, 4, 5, 6]
      - name: pickup_location_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_taxi_zones')
              field: location_id
      - name: dropoff_location_id
        tests:
          - not_null

  - name: stg_taxi_zones
    columns:
      - name: location_id
        tests:
          - not_null
          - unique
      - name: borough
        tests:
          - not_null
          - accepted_values:
              values: ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island', 'EWR', 'Unknown']
```

`models/staging/sources.yml`:
```yaml
version: 2
sources:
  - name: tlc
    description: "NYC TLC raw data loaded via DuckDB read_parquet view"
    tables:
      - name: raw_yellow_trips
        description: "Yellow taxi trips Jan–Mar 2024"
```

**Commit breakdown (Phase 2):**
```
feat: add sources.yml defining tlc.raw_yellow_trips source
feat: add stg_yellow_trips staging model with type casting and invalid row filter
feat: add stg_taxi_zones staging model from seed reference
test: add not_null and unique schema tests for stg_yellow_trips
test: add accepted_values tests for vendor_id, payment_type, passenger_count
test: add dbt_expectations range tests for fare_amount and trip_distance
test: add relationships test linking pickup_location_id to stg_taxi_zones
docs: add column descriptions for staging layer schema YAML
```

**Phase 2 Test Suite & Expected Results:**

```bash
# Full staging build + test
uv run dbt build --select staging --profiles-dir .
# Expected output:
#   20+ of 20+ PASS schema test stg_yellow_trips_trip_id_not_null
#   20+ of 20+ PASS schema test stg_yellow_trips_trip_id_unique
#   20+ of 20+ PASS schema test stg_yellow_trips_vendor_id_accepted_values
#   20+ of 20+ PASS schema test stg_yellow_trips_payment_type_accepted_values
#   20+ of 20+ PASS dbt_expectations range test fare_amount
#   20+ of 20+ PASS relationships test pickup_location_id
#   Completed successfully
#   Done. PASS=XX WARN=0 ERROR=0 SKIP=0 TOTAL=XX

# Row count verification
uv run python -c "
import duckdb
con = duckdb.connect('datavault.duckdb')
n = con.execute('SELECT COUNT(*) FROM stg_yellow_trips').fetchone()[0]
print(f'stg_yellow_trips rows: {n:,}')
assert n > 8_000_000, f'Expected >8M rows after filtering, got {n}'
assert n < 9_500_000, f'Expected <9.5M rows, got {n}'
print('Row count: PASS')
zones = con.execute('SELECT COUNT(*) FROM stg_taxi_zones').fetchone()[0]
assert zones == 265, f'Expected 265 zone rows, got {zones}'
print('Zone count: PASS')
"

# pytest
uv run pytest tests/test_phase2.py -v
# Expected:
#   test_stg_yellow_trips_no_negative_fares PASSED
#   test_stg_yellow_trips_no_null_pickup_at PASSED
#   test_stg_yellow_trips_valid_duration PASSED
#   test_stg_taxi_zones_borough_coverage PASSED
#   4 passed in Xs
```

**pytest file `tests/test_phase2.py`:**
```python
import pytest
import duckdb

@pytest.fixture(scope="module")
def con():
    return duckdb.connect("datavault.duckdb")

def test_stg_yellow_trips_no_negative_fares(con):
    n = con.execute(
        "SELECT COUNT(*) FROM stg_yellow_trips WHERE fare_amount <= 0"
    ).fetchone()[0]
    assert n == 0, f"{n} rows with non-positive fare"

def test_stg_yellow_trips_no_null_pickup_at(con):
    n = con.execute(
        "SELECT COUNT(*) FROM stg_yellow_trips WHERE pickup_at IS NULL"
    ).fetchone()[0]
    assert n == 0

def test_stg_yellow_trips_valid_duration(con):
    n = con.execute("""
        SELECT COUNT(*) FROM stg_yellow_trips
        WHERE DATEDIFF('minute', pickup_at, dropoff_at) NOT BETWEEN 1 AND 360
    """).fetchone()[0]
    assert n == 0, f"{n} rows with invalid trip duration"

def test_stg_taxi_zones_borough_coverage(con):
    boroughs = con.execute(
        "SELECT DISTINCT borough FROM stg_taxi_zones ORDER BY 1"
    ).fetchdf()["borough"].tolist()
    expected = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}
    assert expected.issubset(set(boroughs)), f"Missing boroughs: {expected - set(boroughs)}"
```

---

#### Phase 3 — Intermediate + Mart Layer (Days 5–6)

**Goal:** full analytical layer — 4 mart tables ready for dashboard consumption.

**Intermediate model:**

`models/intermediate/int_trips_enriched.sql`:
```sql
WITH trips AS (
    SELECT * FROM {{ ref('stg_yellow_trips') }}
),
zones AS (
    SELECT * FROM {{ ref('stg_taxi_zones') }}
),
enriched AS (
    SELECT
        t.trip_id,
        t.vendor_id,
        t.pickup_at,
        t.dropoff_at,
        DATE_TRUNC('day', t.pickup_at)              AS trip_date,
        EXTRACT(hour FROM t.pickup_at)              AS pickup_hour,
        EXTRACT(isodow FROM t.pickup_at)            AS day_of_week,  -- 1=Mon, 7=Sun
        t.passenger_count,
        t.trip_distance_miles,
        t.fare_amount,
        t.tip_amount,
        t.total_amount,
        t.payment_type,
        t.pickup_location_id,
        t.dropoff_location_id,
        DATEDIFF('minute', t.pickup_at, t.dropoff_at)       AS trip_duration_min,
        CASE WHEN t.tip_amount > 0
             THEN t.tip_amount / NULLIF(t.total_amount, 0)
             ELSE 0 END                                      AS tip_rate,
        t.total_amount / NULLIF(t.trip_distance_miles, 0)   AS revenue_per_mile,
        CASE WHEN t.pickup_location_id IN (132, 138, 1)
             THEN TRUE ELSE FALSE END                        AS is_airport_trip,
        pu.borough                                           AS pickup_borough,
        pu.zone                                              AS pickup_zone,
        do_.borough                                          AS dropoff_borough,
        do_.zone                                             AS dropoff_zone
    FROM trips t
    LEFT JOIN zones pu ON t.pickup_location_id = pu.location_id
    LEFT JOIN zones do_ ON t.dropoff_location_id = do_.location_id
)
SELECT * FROM enriched
```

**Mart models:**

`models/marts/mart_daily_trips.sql`:
```sql
SELECT
    trip_date,
    pickup_borough,
    COUNT(*)                            AS trip_count,
    SUM(total_amount)                   AS total_revenue,
    AVG(fare_amount)                    AS avg_fare,
    AVG(trip_duration_min)              AS avg_duration_min,
    AVG(passenger_count)                AS avg_passengers,
    SUM(CASE WHEN is_airport_trip THEN 1 ELSE 0 END) AS airport_trip_count
FROM {{ ref('int_trips_enriched') }}
WHERE pickup_borough IS NOT NULL
GROUP BY trip_date, pickup_borough
ORDER BY trip_date, pickup_borough
```

`models/marts/mart_borough_revenue.sql`:
```sql
SELECT
    pickup_borough,
    dropoff_borough,
    COUNT(*)                  AS trip_count,
    SUM(total_amount)         AS total_revenue,
    AVG(fare_amount)          AS avg_fare,
    AVG(tip_rate)             AS avg_tip_rate,
    AVG(trip_distance_miles)  AS avg_distance_miles
FROM {{ ref('int_trips_enriched') }}
WHERE pickup_borough IS NOT NULL AND dropoff_borough IS NOT NULL
GROUP BY pickup_borough, dropoff_borough
```

`models/marts/mart_zone_performance.sql`:
```sql
-- Zone composite score: revenue density (40%) + trip volume (40%) + tip rate (20%)
WITH base AS (
    SELECT
        pickup_location_id  AS location_id,
        pickup_zone         AS zone,
        pickup_borough      AS borough,
        COUNT(*)            AS trip_count,
        SUM(total_amount)   AS total_revenue,
        AVG(tip_rate)       AS avg_tip_rate
    FROM {{ ref('int_trips_enriched') }}
    WHERE pickup_borough IS NOT NULL
    GROUP BY pickup_location_id, pickup_zone, pickup_borough
),
normalized AS (
    SELECT
        *,
        -- min-max normalize each metric to 0-100
        100.0 * (total_revenue - MIN(total_revenue) OVER ()) /
            NULLIF(MAX(total_revenue) OVER () - MIN(total_revenue) OVER (), 0)  AS norm_revenue,
        100.0 * (trip_count - MIN(trip_count) OVER ()) /
            NULLIF(MAX(trip_count) OVER () - MIN(trip_count) OVER (), 0)        AS norm_trips,
        100.0 * (avg_tip_rate - MIN(avg_tip_rate) OVER ()) /
            NULLIF(MAX(avg_tip_rate) OVER () - MIN(avg_tip_rate) OVER (), 0)    AS norm_tip_rate
    FROM base
)
SELECT
    location_id,
    zone,
    borough,
    trip_count,
    ROUND(total_revenue, 2)    AS total_revenue,
    ROUND(avg_tip_rate, 4)     AS avg_tip_rate,
    ROUND(
        0.40 * norm_revenue +
        0.40 * norm_trips +
        0.20 * norm_tip_rate,
        2
    )                          AS zone_score
FROM normalized
ORDER BY zone_score DESC
```

`models/marts/mart_surge_analysis.sql`:
```sql
SELECT
    pickup_hour,
    day_of_week,
    pickup_borough,
    COUNT(*)            AS trip_count,
    AVG(fare_amount)    AS avg_fare,
    AVG(total_amount)   AS avg_total,
    -- demand index: normalize trip_count within each borough
    100.0 * COUNT(*) / MAX(COUNT(*)) OVER (PARTITION BY pickup_borough) AS demand_index
FROM {{ ref('int_trips_enriched') }}
WHERE pickup_borough IS NOT NULL
GROUP BY pickup_hour, day_of_week, pickup_borough
ORDER BY pickup_borough, day_of_week, pickup_hour
```

`models/marts/_marts.yml` (tests):
```yaml
version: 2
models:
  - name: mart_daily_trips
    columns:
      - name: trip_date
        tests: [not_null]
      - name: pickup_borough
        tests: [not_null]
      - name: trip_count
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 1
      - name: total_revenue
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0.01

  - name: mart_zone_performance
    columns:
      - name: location_id
        tests: [not_null, unique]
      - name: zone_score
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 100

  - name: mart_borough_revenue
    columns:
      - name: pickup_borough
        tests: [not_null]
      - name: dropoff_borough
        tests: [not_null]
      - name: total_revenue
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0.01
      - name: avg_tip_rate
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1

  - name: mart_surge_analysis
    columns:
      - name: pickup_hour
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 23
      - name: day_of_week
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 1
              max_value: 7
      - name: demand_index
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 100
```

Custom SQL generic test `tests/assert_positive_revenue.sql`:
```sql
-- Fails if any mart row has negative revenue
SELECT *
FROM {{ ref('mart_daily_trips') }}
WHERE total_revenue < 0
```

Custom test `tests/assert_zone_score_range.sql`:
```sql
SELECT *
FROM {{ ref('mart_zone_performance') }}
WHERE zone_score NOT BETWEEN 0 AND 100
   OR zone_score IS NULL
```

**Commit breakdown (Phase 3):**
```
feat: add int_trips_enriched intermediate model with zone join and derived columns
feat: add mart_daily_trips model - daily borough aggregates
feat: add mart_borough_revenue model - O-D revenue matrix
feat: add mart_zone_performance model - composite zone score (0-100)
feat: add mart_surge_analysis model - hour x day x borough demand heatmap
test: add schema tests for all mart models via _marts.yml
test: add custom SQL generic tests for positive revenue and zone score bounds
docs: add model descriptions and column docs for intermediate and mart layers
```

**Phase 3 Test Suite & Expected Results:**

```bash
# Full build all models
uv run dbt build --profiles-dir .
# Expected:
#   Done. PASS=XX WARN=0 ERROR=0 SKIP=0 TOTAL=XX
#   (XX = all schema tests + model runs combined, 0 failures)

# Row count spot checks
uv run python -c "
import duckdb
con = duckdb.connect('datavault.duckdb')

# mart_daily_trips: expect ~270 rows (90 days × 5 boroughs + EWR)
n = con.execute('SELECT COUNT(*) FROM mart_daily_trips').fetchone()[0]
assert 200 < n < 400, f'mart_daily_trips unexpected count: {n}'
print(f'mart_daily_trips: {n} rows - PASS')

# mart_zone_performance: expect <=265 rows (one per zone that had trips)
n = con.execute('SELECT COUNT(*) FROM mart_zone_performance').fetchone()[0]
assert 200 < n <= 265, f'mart_zone_performance unexpected count: {n}'
print(f'mart_zone_performance: {n} rows - PASS')

# zone_score range
bad = con.execute(
    'SELECT COUNT(*) FROM mart_zone_performance WHERE zone_score NOT BETWEEN 0 AND 100'
).fetchone()[0]
assert bad == 0, f'{bad} zones outside 0-100 score range'
print('zone_score range: PASS')

# mart_surge_analysis: expect 24 hours × 7 days × 5+ boroughs rows
n = con.execute('SELECT COUNT(*) FROM mart_surge_analysis').fetchone()[0]
assert n >= 24 * 7 * 5, f'mart_surge_analysis too few rows: {n}'
print(f'mart_surge_analysis: {n} rows - PASS')
"

# Query performance (all mart queries must complete < 1s)
uv run python -c "
import duckdb, time
con = duckdb.connect('datavault.duckdb')
queries = [
    'SELECT * FROM mart_daily_trips',
    'SELECT * FROM mart_borough_revenue',
    'SELECT * FROM mart_zone_performance',
    'SELECT * FROM mart_surge_analysis',
]
for q in queries:
    t0 = time.time()
    con.execute(q).fetchdf()
    elapsed = time.time() - t0
    assert elapsed < 1.0, f'Query took {elapsed:.2f}s (limit: 1s): {q}'
    print(f'{elapsed:.3f}s: {q[:50]} - PASS')
"

# pytest
uv run pytest tests/test_phase3.py -v
# Expected: all tests passed
```

**pytest file `tests/test_phase3.py`:**
```python
import pytest
import duckdb

@pytest.fixture(scope="module")
def con():
    return duckdb.connect("datavault.duckdb")

def test_zone_score_in_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM mart_zone_performance WHERE zone_score NOT BETWEEN 0 AND 100"
    ).fetchone()[0]
    assert bad == 0

def test_no_null_trip_dates(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM mart_daily_trips WHERE trip_date IS NULL"
    ).fetchone()[0]
    assert bad == 0

def test_no_negative_revenue(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM mart_daily_trips WHERE total_revenue < 0"
    ).fetchone()[0]
    assert bad == 0

def test_borough_revenue_tip_rate_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM mart_borough_revenue WHERE avg_tip_rate NOT BETWEEN 0 AND 1"
    ).fetchone()[0]
    assert bad == 0

def test_surge_hour_range(con):
    bad = con.execute(
        "SELECT COUNT(*) FROM mart_surge_analysis WHERE pickup_hour NOT BETWEEN 0 AND 23"
    ).fetchone()[0]
    assert bad == 0

def test_mart_query_performance(con):
    import time
    for table in ["mart_daily_trips", "mart_borough_revenue", "mart_zone_performance", "mart_surge_analysis"]:
        t0 = time.time()
        con.execute(f"SELECT * FROM {table}").fetchdf()
        elapsed = time.time() - t0
        assert elapsed < 1.0, f"{table} query took {elapsed:.2f}s, limit 1s"

def test_top_zone_is_midtown_or_jfk(con):
    top = con.execute(
        "SELECT zone FROM mart_zone_performance ORDER BY zone_score DESC LIMIT 5"
    ).fetchdf()["zone"].tolist()
    # At minimum, high-traffic zones should appear in top 5
    assert len(top) == 5
```

---

#### Phase 4 — CI Pipeline & dbt Docs (Day 7)

**Goal:** every PR triggers `dbt build` on sample data; docs auto-deploy to GitHub Pages.

**`.github/workflows/ci.yml`:**
```yaml
name: dbt CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main, stage]

jobs:
  dbt-build:
    name: dbt build (sample data)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Create DuckDB raw view (sample)
        run: |
          uv run python -c "
          import duckdb
          con = duckdb.connect('datavault.duckdb')
          con.execute(\"CREATE OR REPLACE VIEW raw_yellow_trips AS SELECT * FROM read_parquet('data/sample/yellow_tripdata_sample.parquet')\")
          con.close()
          "

      - name: dbt seed
        run: uv run dbt seed --profiles-dir .

      - name: dbt build
        run: uv run dbt build --profiles-dir .

      - name: Run pytest
        run: uv run pytest tests/ -v --tb=short

      - name: Upload mart DuckDB artifact
        if: github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v4
        with:
          name: datavault-mart-${{ github.sha }}
          path: datavault.duckdb
          retention-days: 30
```

**`.github/workflows/docs.yml`:**
```yaml
name: dbt Docs

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy-docs:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install uv && uv sync

      - name: Create sample DuckDB
        run: |
          uv run python -c "
          import duckdb
          con = duckdb.connect('datavault.duckdb')
          con.execute(\"CREATE OR REPLACE VIEW raw_yellow_trips AS SELECT * FROM read_parquet('data/sample/yellow_tripdata_sample.parquet')\")
          con.close()
          "

      - run: uv run dbt seed --profiles-dir .
      - run: uv run dbt docs generate --profiles-dir .

      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: datavault_dbt/target/

      - id: deployment
        uses: actions/deploy-pages@v4
```

**Commit breakdown (Phase 4):**
```
chore: add .github/workflows/ci.yml - dbt build on every PR with sample data
chore: add .github/workflows/docs.yml - dbt docs deploy to GitHub Pages
chore: add uv.lock to ensure reproducible CI installs
docs: add CI badge to README.md
docs: update README with architecture diagram (Mermaid) and data lineage
```

**Phase 4 Test Suite & Expected Results:**

```bash
# Local simulation of CI (use sample data)
uv run python -c "
import duckdb
con = duckdb.connect('datavault_ci_test.duckdb')
con.execute(\"CREATE OR REPLACE VIEW raw_yellow_trips AS SELECT * FROM read_parquet('data/sample/yellow_tripdata_sample.parquet')\")
con.close()
"
DUCKDB_PATH=datavault_ci_test.duckdb uv run dbt seed --profiles-dir .
DUCKDB_PATH=datavault_ci_test.duckdb uv run dbt build --profiles-dir .
# Expected: Done. PASS=XX WARN=0 ERROR=0 SKIP=0 (all pass on 10k-row sample)

# dbt docs generation
uv run dbt docs generate --profiles-dir .
# Expected: datavault_dbt/target/index.html generated
ls datavault_dbt/target/index.html
# Expected: file exists

# Verify CI workflow YAML is valid
python -c "
import yaml
with open('.github/workflows/ci.yml') as f:
    cfg = yaml.safe_load(f)
assert 'jobs' in cfg
assert 'dbt-build' in cfg['jobs']
print('ci.yml valid: PASS')
"

# pytest
uv run pytest tests/test_phase4.py -v
```

**pytest file `tests/test_phase4.py`:**
```python
import pytest
import yaml
import duckdb
from pathlib import Path

ROOT = Path(__file__).parent.parent

def test_ci_workflow_exists():
    assert (ROOT / ".github/workflows/ci.yml").exists()

def test_docs_workflow_exists():
    assert (ROOT / ".github/workflows/docs.yml").exists()

def test_ci_workflow_valid_yaml():
    cfg = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert "jobs" in cfg
    jobs = cfg["jobs"]
    assert "dbt-build" in jobs
    steps = jobs["dbt-build"]["steps"]
    step_names = [s.get("name", s.get("uses", "")) for s in steps]
    assert any("dbt build" in n.lower() for n in step_names)

def test_sample_dbt_build_on_sample_data(tmp_path):
    import subprocess
    db_path = str(tmp_path / "ci_test.duckdb")
    con = duckdb.connect(db_path)
    con.execute("CREATE OR REPLACE VIEW raw_yellow_trips AS "
                "SELECT * FROM read_parquet('data/sample/yellow_tripdata_sample.parquet')")
    con.close()

    env = {"DUCKDB_PATH": db_path}
    import os
    env.update(os.environ)

    result = subprocess.run(
        ["uv", "run", "dbt", "build", "--profiles-dir", "."],
        capture_output=True, text=True, env=env
    )
    assert result.returncode == 0, f"dbt build failed:\n{result.stdout}\n{result.stderr}"
    assert "ERROR" not in result.stdout or "0 error" in result.stdout.lower()
```

---

#### Phase 5 — Dashboard + Deploy (Days 8–9)

**Goal:** 4-tab Streamlit dashboard, deployed to Streamlit Cloud, loads in < 3s.

**`dashboard/app.py` structure:**
```python
import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

st.set_page_config(page_title="DataVault — NYC Taxi Analytics", layout="wide")

DB_PATH = os.environ.get("DUCKDB_PATH", "datavault.duckdb")

@st.cache_resource
def get_db():
    return duckdb.connect(DB_PATH, read_only=True)

@st.cache_data(ttl=3600)
def query(sql: str) -> pd.DataFrame:
    return get_db().execute(sql).fetchdf()

# --- Sidebar ---
st.sidebar.title("DataVault")
st.sidebar.caption("NYC Yellow Taxi — Jan–Mar 2024")
boroughs = ["All"] + query("SELECT DISTINCT pickup_borough FROM mart_daily_trips ORDER BY 1")["pickup_borough"].tolist()
selected_borough = st.sidebar.selectbox("Borough", boroughs)
last_date = query("SELECT MAX(trip_date) FROM mart_daily_trips")["max(trip_date)"][0]
st.sidebar.caption(f"Data through: {last_date}")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Borough Revenue", "Zone Performance", "Surge Analysis"])

# Tab 1: Overview
with tab1:
    df = query("SELECT * FROM mart_daily_trips ORDER BY trip_date")
    if selected_borough != "All":
        df = df[df["pickup_borough"] == selected_borough]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Trips", f"{df['trip_count'].sum():,.0f}")
    col2.metric("Total Revenue", f"${df['total_revenue'].sum():,.0f}")
    col3.metric("Avg Fare", f"${df['avg_fare'].mean():.2f}")
    fig = px.line(df, x="trip_date", y="trip_count", color="pickup_borough",
                  title="Daily Trip Volume by Borough")
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.bar(df.groupby("pickup_borough")["total_revenue"].sum().reset_index(),
                  x="pickup_borough", y="total_revenue", title="Total Revenue by Borough")
    st.plotly_chart(fig2, use_container_width=True)

# Tab 2: Borough Revenue
with tab2:
    df = query("SELECT * FROM mart_borough_revenue")
    pivot = df.pivot_table(index="pickup_borough", columns="dropoff_borough",
                           values="total_revenue", aggfunc="sum")
    fig = px.imshow(pivot, title="Revenue O-D Matrix (Pickup → Dropoff Borough)",
                    color_continuous_scale="Blues", text_auto=".0f")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.sort_values("total_revenue", ascending=False), use_container_width=True)

# Tab 3: Zone Performance
with tab3:
    df = query("SELECT * FROM mart_zone_performance ORDER BY zone_score DESC")
    if selected_borough != "All":
        df = df[df["borough"] == selected_borough]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Zones by Composite Score")
        st.dataframe(df[["zone", "borough", "trip_count", "total_revenue", "avg_tip_rate", "zone_score"]].head(20),
                     use_container_width=True)
    with col2:
        fig = px.scatter(df, x="trip_count", y="total_revenue", color="borough",
                         size="zone_score", hover_name="zone",
                         title="Zone Performance: Volume vs Revenue")
        st.plotly_chart(fig, use_container_width=True)

# Tab 4: Surge Analysis
with tab4:
    df = query("SELECT * FROM mart_surge_analysis")
    day_labels = {1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat",7:"Sun"}
    df["day_name"] = df["day_of_week"].map(day_labels)
    if selected_borough != "All":
        df = df[df["pickup_borough"] == selected_borough]
    pivot = df.groupby(["day_name", "pickup_hour"])["demand_index"].mean().reset_index()
    pivot_wide = pivot.pivot(index="day_name", columns="pickup_hour", values="demand_index")
    day_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    pivot_wide = pivot_wide.reindex([d for d in day_order if d in pivot_wide.index])
    fig = px.imshow(pivot_wide, title="Demand Index by Hour × Day of Week",
                    color_continuous_scale="RdYlGn", aspect="auto",
                    labels={"x": "Hour of Day", "y": "Day"})
    st.plotly_chart(fig, use_container_width=True)
```

**`dashboard/startup.sh`** (for Streamlit Cloud):
```bash
#!/bin/bash
# Download pre-built mart DuckDB from GitHub Releases (set RELEASE_URL in secrets)
if [ ! -f datavault.duckdb ] && [ -n "$RELEASE_URL" ]; then
    curl -L "$RELEASE_URL" -o datavault.duckdb
fi
```

**`dashboard/requirements.txt`** (Streamlit Cloud reads this):
```
dbt-core==1.8.*
dbt-duckdb==1.8.*
streamlit==1.39.*
plotly==5.*
pandas==2.*
duckdb==1.1.*
```

**Commit breakdown (Phase 5):**
```
feat: add Streamlit app skeleton with DB connection and caching layer
feat: add Overview tab with daily volume line chart and revenue bar chart
feat: add Borough Revenue tab with O-D heatmap matrix
feat: add Zone Performance tab with scatter plot and ranked table
feat: add Surge Analysis tab with hour x day demand heatmap
chore: add dashboard/startup.sh and requirements.txt for Streamlit Cloud deploy
docs: add Streamlit Cloud deploy instructions and secrets config to README
docs: finalize README with architecture diagram, screenshots placeholder, formula docs
```

**Phase 5 Test Suite & Expected Results:**

```bash
# Streamlit import check (no runtime errors on import)
uv run python -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('app', 'dashboard/app.py')
# Just check it parses without import error
import ast
with open('dashboard/app.py') as f:
    ast.parse(f.read())
print('dashboard/app.py syntax: PASS')
"

# All DB queries in dashboard run without error
uv run python -c "
import duckdb
con = duckdb.connect('datavault.duckdb', read_only=True)
queries = [
    'SELECT * FROM mart_daily_trips ORDER BY trip_date',
    'SELECT * FROM mart_borough_revenue',
    'SELECT * FROM mart_zone_performance ORDER BY zone_score DESC',
    'SELECT * FROM mart_surge_analysis',
    'SELECT DISTINCT pickup_borough FROM mart_daily_trips ORDER BY 1',
    'SELECT MAX(trip_date) FROM mart_daily_trips',
]
for q in queries:
    df = con.execute(q).fetchdf()
    assert len(df) > 0, f'Empty result: {q}'
    print(f'OK ({len(df)} rows): {q[:60]}')
print('All dashboard queries: PASS')
"

# pytest
uv run pytest tests/test_phase5.py -v
```

**pytest file `tests/test_phase5.py`:**
```python
import pytest
import ast
import duckdb
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent

def test_dashboard_syntax():
    src = (ROOT / "dashboard/app.py").read_text()
    ast.parse(src)  # raises SyntaxError if broken

def test_requirements_txt_exists():
    assert (ROOT / "dashboard/requirements.txt").exists()

def test_startup_sh_exists():
    assert (ROOT / "dashboard/startup.sh").exists()

@pytest.fixture(scope="module")
def con():
    return duckdb.connect("datavault.duckdb", read_only=True)

DASHBOARD_QUERIES = [
    "SELECT * FROM mart_daily_trips ORDER BY trip_date",
    "SELECT * FROM mart_borough_revenue",
    "SELECT * FROM mart_zone_performance ORDER BY zone_score DESC",
    "SELECT * FROM mart_surge_analysis",
]

@pytest.mark.parametrize("sql", DASHBOARD_QUERIES)
def test_dashboard_query_non_empty(con, sql):
    df = con.execute(sql).fetchdf()
    assert len(df) > 0

@pytest.mark.parametrize("sql", DASHBOARD_QUERIES)
def test_dashboard_query_performance(con, sql):
    t0 = time.time()
    con.execute(sql).fetchdf()
    elapsed = time.time() - t0
    assert elapsed < 1.0, f"Query exceeded 1s ({elapsed:.2f}s): {sql}"

def test_overview_tab_columns(con):
    df = con.execute("SELECT * FROM mart_daily_trips LIMIT 1").fetchdf()
    required = ["trip_date", "pickup_borough", "trip_count", "total_revenue", "avg_fare"]
    assert all(c in df.columns for c in required), f"Missing columns: {set(required) - set(df.columns)}"

def test_surge_hour_coverage(con):
    hours = con.execute(
        "SELECT DISTINCT pickup_hour FROM mart_surge_analysis ORDER BY 1"
    ).fetchdf()["pickup_hour"].tolist()
    assert len(hours) == 24, f"Expected 24 hours, got {len(hours)}"
```

---

### Full Test Matrix (All Phases)

| Phase | Command | Expected Result |
|-------|---------|----------------|
| 1 | `dbt debug` | `All checks passed` |
| 1 | `dbt seed` | `INSERT 265` rows in taxi_zones |
| 1 | `pytest tests/test_phase1.py` | 5 passed |
| 1 | `python scripts/verify_raw.py` | ALL CHECKS PASSED |
| 2 | `dbt build --select staging` | PASS=XX WARN=0 ERROR=0 |
| 2 | `pytest tests/test_phase2.py` | 4 passed |
| 3 | `dbt build` (full) | PASS=XX WARN=0 ERROR=0 |
| 3 | `pytest tests/test_phase3.py` | 7 passed |
| 3 | all mart queries | < 1s each |
| 4 | `dbt build` on sample data | PASS=XX WARN=0 ERROR=0 |
| 4 | `pytest tests/test_phase4.py` | 4 passed |
| 5 | `pytest tests/test_phase5.py` | 9 passed |
| 5 | all dashboard queries | < 1s, non-empty |

### Success Metrics

**dbt health**
- `dbt build` exits 0 on both full data and sample data
- 0 test failures across all phases
- `dbt docs generate` produces valid HTML site

**Data quality**
- stg_yellow_trips: 0 rows with negative fare, invalid duration, null required cols
- mart_zone_performance: all scores in [0, 100]
- mart_surge_analysis: all hours in [0, 23], all days in [1, 7]
- mart_borough_revenue: avg_tip_rate in [0, 1]

**Performance**
- All mart queries: < 1s (DuckDB columnar on tables)
- Dashboard cold load: < 3s on Streamlit Cloud (mart data is ~3MB)
- `dbt build` on sample (CI): < 2 minutes
- `dbt build` on full 3-month data: < 5 minutes

**Portfolio signal**
- dbt docs site on GitHub Pages — shows documentation culture
- CI badge (green) in README
- Mermaid architecture diagram in README
- `mart_zone_performance` formula explained in README (analytical maturity)
- Streamlit Cloud live demo link + Prefect-style pipeline screenshot
- pytest run screenshot showing all green

---

## Project 5: DocuMind — RAG Document Chat

### The Problem

Every company hiring AI engineers wants to see **RAG** (Retrieval-Augmented Generation) experience. The market is flooded with toy demos: upload PDF, ask question, get answer. They all use OpenAI (paid) and LangChain with zero engineering rigor. The gap: **production-quality retrieval** — proper chunking strategy, embedding quality evaluation, relevance scoring, citation support, and handling edge cases (questions with no relevant context).

### The Solution

A document intelligence platform where users upload research papers or technical docs, and get accurate answers **with citations** (which document, which page). The differentiating features:

1. **Hallucination guard**: if retrieved context relevance score < threshold, respond "I don't have enough information" instead of hallucinating
2. **Multi-document comparison**: "Compare the methodology in Doc A vs Doc B"
3. **Chunking strategy selector**: users can switch between fixed-size, sentence-boundary, and semantic chunking — and see how it affects answer quality

This turns a toy demo into an engineering project that demonstrates retrieval quality thinking.

**Gaps to address:**
- Local LLMs (Ollama) are slow on CPU-only machines. Solution: use Groq API (free tier: 30 req/min, Llama 3 70B) for inference, Ollama as local fallback.
- ChromaDB persistence in Streamlit Cloud is ephemeral. Solution: use `chromadb` with a local SQLite backend, commit the vector store to the repo for a pre-loaded demo dataset.
- PDF parsing quality varies. Solution: use `pdfplumber` (better than PyMuPDF for text-heavy docs), fallback to PyMuPDF for image-heavy PDFs.
- Embedding API costs. Solution: use `sentence-transformers` (local, free, `all-MiniLM-L6-v2` — fast, 384-dim, good quality).

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| LLM | Groq API (free: Llama 3.1 70B) | Fast inference, free tier, no vendor lock-in |
| LLM fallback | Ollama (local) | 100% free, offline capable |
| Embeddings | sentence-transformers (local) | Free, no API calls, runs on CPU |
| Vector DB | ChromaDB (local SQLite backend) | Zero infra, persistent, easy to inspect |
| PDF parsing | pdfplumber + PyMuPDF | Handles both text and scanned docs |
| Chunking | LangChain text splitters | Sentence, recursive, and semantic variants |
| Relevance scoring | Cosine similarity + MMR reranking | Reduces redundant chunks in retrieval |
| UI | Streamlit | Chat interface, file upload, citation display |
| Deploy | Streamlit Cloud (free) | One-click |
| Testing | pytest + ragas (free) | RAG evaluation framework |

**Why not LangChain for everything?** LangChain abstracts too much for a portfolio project. Use it only for chunking. Write the retrieval loop manually — it proves you understand the pipeline.

### General Flow

```
[User uploads PDF(s)]
        ↓
[Parse: pdfplumber → text + page numbers]
        ↓
[Chunk: RecursiveCharacterTextSplitter, 512 tokens, 50 overlap]
        ↓
[Embed: sentence-transformers all-MiniLM-L6-v2 → 384-dim vectors]
        ↓
[Store: ChromaDB collection with metadata: doc_name, page_num, chunk_id]
        ↓
[User asks question]
        ↓
[Embed question → cosine similarity search → top-5 chunks]
        ↓
[Relevance check: if max_score < 0.35 → "insufficient context" response]
        ↓
[Rerank: MMR (Maximal Marginal Relevance) to reduce redundancy]
        ↓
[Prompt: inject top-3 chunks as context → Groq LLM]
        ↓
[Response: answer + citations (doc name, page number)]
```

### Build Phases

**Phase 1 — Core Pipeline (Days 1–3)**
- PDF ingestion with pdfplumber, page metadata extraction
- Chunking with LangChain RecursiveCharacterTextSplitter
- Embedding with sentence-transformers
- ChromaDB store + query with metadata filter
- End-to-end test: upload 1 paper, ask 3 questions, verify citation accuracy

**Phase 2 — Retrieval Quality (Days 4–5)**
- Relevance threshold guard (cosine < 0.35 → refuse to answer)
- MMR reranking implementation (manual, ~30 lines)
- Multi-document query: retrieve from all docs, rank globally
- Test: questions with no relevant context must trigger the guard

**Phase 3 — LLM Integration (Days 6–7)**
- Groq API integration (Llama 3.1 70B)
- Ollama fallback (`llama3.2:3b` for local)
- Prompt template: strict "answer only from context" instruction
- Citation extraction: parse LLM response to link claims to source chunks

**Phase 4 — Chunking Comparison Feature (Day 8)**
- Add UI toggle: Fixed / Sentence / Semantic chunking
- Show chunk count and avg chunk size for each strategy
- Let user see retrieved chunks before the answer
- This feature alone differentiates from 99% of RAG demos

**Phase 5 — Evaluation + Deploy (Days 9–10)**
- ragas evaluation on 20 question-answer pairs (faithfulness, context_recall, answer_relevancy)
- Pre-load demo dataset: 3 ML papers (public domain) + 20 ground-truth Q&A pairs
- Deploy Streamlit Cloud with pre-loaded vector store
- README: evaluation metrics table, architecture diagram, chunking strategy comparison

### Success Metrics / Test Suite

**Retrieval quality (ragas)**
- Faithfulness score > 0.80 (answers grounded in context)
- Context recall > 0.75 (relevant chunks retrieved)
- Answer relevancy > 0.80 (answers the actual question)
- Measure before/after MMR reranking — show improvement in README

**Hallucination guard**
- `test_refusal.py`: 10 out-of-domain questions → assert all trigger refusal
- `test_citation_accuracy.py`: 10 known Q&As → assert citation page numbers correct

**Functional tests**
- `test_pdf_parse.py`: known PDF → assert expected text and page count
- `test_chunking.py`: known text → assert chunk count, no data loss between chunks
- `test_embedding.py`: two semantically similar sentences → cosine similarity > 0.85

**Performance**
- Embedding 100 chunks: < 10s on CPU
- Query latency (embed + retrieve + rerank): < 500ms
- LLM response (Groq): < 3s end-to-end

**Portfolio signal**
- ragas evaluation table in README (shows measurement culture)
- Chunking comparison screenshot
- "Hallucination guard" section in README (shows production thinking)

---

## Project 6: ShipFast — SaaS Starter Dashboard (No Billing)

### The Problem

Full-stack portfolio projects usually fall into two traps: (1) too simple — a CRUD todo app, or (2) fake "full-stack" — Next.js frontend with a single API route. Neither proves you can build a real multi-tenant product. The gap: **authentication architecture, row-level security, and real UX patterns** that appear in every SaaS product.

### The Solution

A multi-tenant team workspace tool — think a stripped-down Notion/Linear workspace. Users can create an organization, invite teammates, create projects, and assign tasks. Focus is entirely on **the infrastructure of SaaS**: auth flows, RLS policies, role-based access (admin/member), invitation email flow, and a dashboard that feels like a real product.

**Why this beats a generic dashboard:**
- Row-Level Security in Postgres (via Supabase) is a real skill — it appears in data privacy audits
- Invitation flow (send email → accept → join org) is a complete user journey, not just a login form
- Role-based access (admin can delete, member cannot) proves authorization thinking
- The project manager feature gives the app a real use case, not just "user settings"

**Gaps to address:**
- Supabase free tier: 500 MB storage, 50,000 monthly active users — more than enough.
- Resend free tier: 3,000 emails/month, 100/day — sufficient for a portfolio demo.
- Next.js + Supabase Auth SSR requires careful cookie handling. Solution: use `@supabase/ssr` (official, replaces deprecated `auth-helpers`).
- Multi-tenant RLS is complex to get right. Solution: design schema first, write RLS policies before any application code, verify with Supabase SQL editor.

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 14 App Router | Industry standard, SSR + RSC |
| Auth | Supabase Auth | Free, handles OAuth + email, SSR-ready |
| Database | Supabase Postgres | Free, RLS built-in, real-time subscriptions |
| Email | Resend (free: 3k/mo) | Best DX, React Email templates |
| Styling | Tailwind CSS + shadcn/ui | Fast, consistent, what companies actually use |
| State | Zustand (minimal) | Lightweight, no boilerplate |
| Forms | React Hook Form + Zod | Validation, type safety |
| Deploy | Vercel (free) | One-click, preview deployments |
| Testing | Vitest + Playwright | Unit + E2E |

**Why not Prisma?** Supabase has a JS client that's typed via generated types. Prisma adds complexity. For a portfolio, the Supabase client is the right tool.

**Why shadcn/ui?** Not a component library you install — it's copy-paste components you own. Hiring managers who know it respect it. It's what most modern Next.js projects use.

### General Flow

```
[User signs up → email verification]
        ↓
[Onboarding: create organization → become admin]
        ↓
[Admin: invite teammates by email → Resend sends invite link]
        ↓
[Invitee: clicks link → signs up / logs in → joins org]
        ↓
[Workspace: create projects → add tasks → assign to members]
        ↓
[RLS enforces: members only see their org's data]
        ↓
[Admin controls: remove members, delete projects, view all tasks]
        ↓
[Real-time: task status updates via Supabase subscriptions]
```

### Database Schema

```sql
-- Core multi-tenant pattern
organizations (id, name, created_at)
memberships (user_id, org_id, role: admin|member, joined_at)
invitations (id, org_id, email, token, expires_at, accepted_at)
projects (id, org_id, name, description, status, created_by)
tasks (id, project_id, org_id, title, status, assignee_id, due_date)

-- RLS: users only see rows where org_id matches their membership
```

### Build Phases

**Phase 1 — Auth & Database (Days 1–3)**
- Supabase project setup, schema creation
- Write all RLS policies before any app code (test in SQL editor)
- Next.js + `@supabase/ssr`: sign up, login, logout, email verification
- Middleware: protect all `/dashboard` routes, redirect unauthenticated users

**Phase 2 — Onboarding Flow (Days 4–5)**
- Create organization on first login
- Generate invitation token (UUID, 48h expiry)
- Resend email: React Email template for invitation
- Accept invitation: validate token, create membership, redirect to workspace

**Phase 3 — Core Workspace (Days 6–8)**
- Project CRUD (admin only: delete, all: create/read/update)
- Task management: create, assign, status (todo/in_progress/done), due date
- Member list page: show role badges, admin can remove members
- Real-time task updates via Supabase `on('postgres_changes')` subscription

**Phase 4 — Role-Based Access (Day 9)**
- Frontend: hide delete buttons for non-admins
- Backend: API routes check membership role before mutations
- Test: member account cannot call admin endpoints (expect 403)
- Audit: verify RLS policies block cross-org data access at DB level

**Phase 5 — Polish + Testing + Deploy (Days 10–11)**
- Playwright E2E: full invitation flow, task lifecycle, role enforcement
- Vitest unit tests: RLS policy logic, invitation token validation
- Seed script: demo org with 3 members and 10 tasks for portfolio demo
- Deploy Vercel, configure Supabase production project
- README: architecture diagram, feature list, RLS explanation

### Success Metrics / Test Suite

**Vitest unit tests**
- `invitation.test.ts`: token generation, expiry check, used-token rejection
- `auth.test.ts`: unauthenticated access returns redirect, not 200
- `rbac.test.ts`: admin vs member permission checks on all mutations

**Playwright E2E tests**
- `invite-flow.spec.ts`: full flow — admin invites → invitee accepts → appears in member list
- `task-lifecycle.spec.ts`: create project → add task → assign → complete → verify status
- `rbac.spec.ts`: login as member → attempt admin action → expect blocked UI + 403

**Security tests**
- Cross-org access test: user A cannot read user B's projects (test at API and DB level)
- Expired invitation test: token > 48h returns 410 Gone
- RLS verification: raw Supabase query from member account returns only their org's rows

**Performance**
- Dashboard first load < 1.5s (Vercel Edge, RSC)
- Real-time task update propagates in < 500ms
- Lighthouse score > 90 (performance, accessibility)

**Portfolio signal**
- RLS policy explanation in README (rare skill to document)
- Invitation flow recorded as a short screen recording (embedded in README)
- Role-based access architecture diagram
- Playwright test run screenshot in README

---

## Cross-Project Notes

### Build Order Recommendation

Start with **Project 6 (ShipFast)** if targeting full-stack/engineering roles — broadest HR appeal.
Start with **Project 2 (DataVault)** if targeting data engineering — most direct signal.
**Project 5 (DocuMind)** can be built in parallel since it has no dependencies on the others.
**Project 1 (WeatherFlow)** is the fastest to deploy and makes a good "warm-up" first project.

### Common Pitfalls to Avoid

1. **No README**: hiring managers decide in 30 seconds. Architecture diagram + 1 screenshot + live demo link is mandatory.
2. **No tests**: listing tests in a README without a test suite is worse than no mention. Every project above has a test suite — run them in CI.
3. **Broken demos**: a live demo that errors out is worse than no demo. Use seed data that always works.
4. **Overcomplicated infra**: none of these projects need Kubernetes, Redis, or a message queue. Adding them without justification signals bad judgment.
5. **No data**: a dashboard with no data is useless. Every project has a strategy for pre-loaded demo data.

### Shared Tooling

- All Python projects: use `uv` for dependency management (faster than pip, modern)
- All Next.js projects: use `pnpm` (faster installs, Vercel recommends it)
- All projects: Conventional Commits + GitHub Actions CI badge in README
- All projects: `pre-commit` hooks for linting/formatting
