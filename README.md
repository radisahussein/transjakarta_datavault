# DataVault

Analytics engineering portfolio project. TransJakarta BRT tap-in/tap-out transaction data (April 2023) processed through a dbt + DuckDB medallion pipeline and served via a Streamlit dashboard.

---

## What This Is

A full analytics engineering stack built from scratch:

- **Raw layer** — CSV loaded as a DuckDB view via Python
- **Staging layer** — dbt models that cast, clean, and validate the raw data
- **Intermediate layer** — enriched records with derived features (distance, duration, time-of-day)
- **Mart layer** — four aggregated tables ready for the dashboard
- **Dashboard** — Streamlit app with four analytical tabs
- **CI** — GitHub Actions runs `dbt build` + `pytest` on every push
- **Docs** — `dbt docs` auto-deployed to GitHub Pages on merge to `main`

---

## Dataset

**Source:** [TransJakarta BRT Transactions — April 2023](https://www.kaggle.com/datasets/dikasiganteng/transjakarta) (Kaggle: `dikasiganteng/transjakarta`)

| Attribute | Value |
|-----------|-------|
| Rows | 189,500 raw; 182,520 after filtering null corridorID |
| Period | 2023-04-01 → 2023-04-30 (30 days) |
| Corridors | 221 |
| Stops | 5,250 |
| File size | ~43 MB CSV |

Each row is one tap-in event. Tap-out is nullable — ~6.5% of trips have no recorded tap-out (missed scan or free transfer).

**Raw schema (key columns):**

| Column | Type | Notes |
|--------|------|-------|
| `transID` | string | Unique transaction ID |
| `payCardID` | string | Anonymized card |
| `payCardBank` | string | Issuing bank (dki, emoney, brizzi, bni, online, flazz) |
| `payCardSex` | string | F / M |
| `payCardBirthDate` | integer | Birth year (e.g. 1993) |
| `corridorID` | string | Corridor code (e.g. "1", "JAK.1", "T11") |
| `corridorName` | string | Human-readable corridor name |
| `direction` | integer | 0 or 1 (travel direction on corridor) |
| `tapInStops` | string | Tap-in stop ID (null in ~3.7% of rows) |
| `tapInStopsLat/Lon` | float | Stop geolocation |
| `tapInTime` | timestamp | Tap-in datetime |
| `tapOutStops` | string | nullable — missed tap-out |
| `tapOutTime` | timestamp | nullable |
| `payAmount` | float | Fare in IDR; null for free/transfer trips (~2%) |

---

## Architecture

```
data/raw/transjakarta.csv
        │
        ▼ scripts/load_raw.py
DuckDB view: raw_transjakarta (main schema)
        │
        ▼ dbt staging (views, main_staging schema)
stg_transactions    — cast + clean + filter null corridorID
stg_stops           — from seed: 5,250 unique stops with lat/lon
stg_corridors       — from seed: 221 unique corridors
        │
        ▼ dbt intermediate (view, main_intermediate schema)
int_trips_enriched  — joins stops, derives distance/duration/temporal features
        │
        ▼ dbt marts (tables, main_marts schema)
mart_daily_ridership    — trips + revenue by corridor × date
mart_corridor_stats     — per-corridor aggregate stats
mart_stop_performance   — stop-level boarding volume + normalized score
mart_surge_analysis     — demand index by hour × day × corridor
        │
        ▼ dashboard/app.py
Streamlit (4 tabs)
```

### Layer Details

**`stg_transactions`** — 182,520 rows
- Casts all columns to correct types
- Lowercases `card_bank`
- Derives `age_years = 2023 - birth_year`
- Adds `has_tap_out` boolean flag
- Filters rows where `corridorID IS NULL` (~6,980 rows removed — upstream data quality issue)
- Known warn: 6,989 rows have null `tap_in_stop_id` with a valid stop name — retained for ridership counting

**`int_trips_enriched`** — 182,520 rows
- Left-joins `stg_stops` to get canonical lat/lon for tap-in stop
- Derives `trip_date`, `hour_of_day` (0–23), `day_of_week` (1=Mon, 7=Sun via ISODOW)
- `duration_min` — non-null only for complete trips (has_tap_out = true); max observed: 180 min
- `distance_km` — Haversine formula; non-null only for `is_complete_trip` rows with geo on both ends; range: 0–22.6 km
- `is_complete_trip` — true for 170,622 rows (93.5%)

**`mart_daily_ridership`** — 6,282 rows (corridor × date)
- `total_trips`, `complete_trips`, `incomplete_trips`, `total_revenue`, `avg_fare`, `unique_riders`
- Groups by `corridor_id` only (uses `MAX(corridor_name)` — some transactions have null corridor_name)

**`mart_corridor_stats`** — 221 rows (one per corridor)
- `total_trips`, `complete_trips`, `completion_rate_pct`, `active_days`, `unique_riders`, `total_revenue`, `avg_distance_km`, `avg_duration_min`

**`mart_stop_performance`** — 5,221 rows
- Only stops with at least one boarding with non-null `tap_in_stop_id`
- `volume_score` (0–100) — min-max normalized boarding count
- `revenue_score` (0–100) — min-max normalized revenue
- `performance_score` — 50% volume + 50% revenue composite; range observed: 0–68

**`mart_surge_analysis`** — 21,462 rows
- Groups by `corridor_id × day_of_week × hour_of_day`
- `demand_index` = trips in slot / average trips per slot for that corridor; range: 0.07–4.93

---

## Project Structure

```
datavault/
├── .github/workflows/
│   ├── ci.yml              # push/PR → dbt build + pytest
│   └── docs.yml            # main push → dbt docs → GitHub Pages
├── .streamlit/
│   └── config.toml         # theme + headless config
├── dashboard/
│   └── app.py              # Streamlit dashboard (4 tabs)
├── data/
│   └── raw/
│       └── transjakarta.csv
├── datavault_dbt/
│   ├── models/
│   │   ├── staging/        # stg_* models + schema YAMLs
│   │   ├── intermediate/   # int_trips_enriched
│   │   └── marts/          # mart_* models + schema YAMLs
│   ├── seeds/
│   │   ├── stops.csv       # 5,250 stops (generated from raw)
│   │   └── corridors.csv   # 221 corridors (generated from raw)
│   ├── tests/
│   │   ├── assert_positive_revenue.sql
│   │   └── assert_stop_score_range.sql
│   ├── dbt_project.yml
│   └── packages.yml
├── scripts/
│   ├── download_data.py    # Kaggle API download (Bearer token auth)
│   ├── generate_seeds.py   # extract stops + corridors from raw CSV
│   ├── load_raw.py         # create DuckDB view over CSV
│   └── verify_raw.py       # sanity checks on raw view
├── tests/
│   ├── test_phase1.py      # 7 pytest assertions (raw layer)
│   ├── test_phase2.py      # 13 pytest assertions (staging layer)
│   └── test_phase3.py      # 21 pytest assertions (intermediate + marts)
├── profiles.yml            # dbt DuckDB profile (repo-local)
├── pyproject.toml          # uv-managed deps
├── requirements.txt        # pinned deps for Streamlit Cloud
└── progress.md             # phase-by-phase build log
```

---

## Tech Stack

| Layer | Tool | Version |
|-------|------|---------|
| Package manager | uv | latest |
| Database | DuckDB | 1.5.2 |
| Transform | dbt-core + dbt-duckdb | 1.11.10 / 1.10.1 |
| dbt packages | dbt-utils, dbt-expectations | 1.x / 0.10.x |
| Dashboard | Streamlit | 1.57.0 |
| Charts | Plotly | 6.7.0 |
| Data frames | pandas | 3.0.3 |
| Tests | pytest | 9.0.3 |
| CI | GitHub Actions | — |
| Docs deploy | GitHub Pages | — |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or `brew install uv`)

### Setup

```bash
git clone <repo-url>
cd datavault

# Install all dependencies
uv sync

# Load raw CSV into DuckDB as a view
uv run python scripts/load_raw.py

# Install dbt packages
uv run dbt deps --project-dir datavault_dbt --profiles-dir .

# Build entire pipeline (staging → intermediate → marts) + run all tests
uv run dbt build --project-dir datavault_dbt --profiles-dir .

# Run pytest suite (41 assertions across all layers)
uv run pytest tests/ -v
```

### Run the Dashboard

```bash
uv run streamlit run dashboard/app.py
# → http://localhost:8501
```

### Verify Raw Data

```bash
uv run python scripts/verify_raw.py
```

### Generate dbt Docs

```bash
uv run dbt docs generate --project-dir datavault_dbt --profiles-dir .
uv run dbt docs serve --project-dir datavault_dbt --profiles-dir .
# → http://localhost:8080
```

---

## Tests

| Suite | Count | What It Covers |
|-------|-------|----------------|
| `dbt build` schema tests | 71 (PASS) + 1 (WARN) | not_null, unique, accepted_values, range checks via dbt-expectations |
| Custom SQL tests | 2 | assert_positive_revenue, assert_stop_score_range |
| `test_phase1.py` | 7 | raw view row count, column presence, null rates |
| `test_phase2.py` | 13 | staging row counts, uniqueness, value ranges, Jakarta geo bounds |
| `test_phase3.py` | 21 | intermediate features, mart aggregation totals, performance (<1s) |

Known warn: `not_null_stg_transactions_tap_in_stop_id` — 6,989 rows have null `tap_in_stop_id` with a valid stop name. Upstream data quality issue, documented and retained.

---

## CI / CD

**`ci.yml`** — triggers on every push and PRs to `main`/`stage`:

```
checkout → Python 3.11 → uv → uv sync → load_raw.py → dbt deps → dbt build → pytest
```

**`docs.yml`** — triggers on push to `main`:

```
(same build) → dbt docs generate → deploy to GitHub Pages
```

---

## Dashboard

Four tabs backed entirely by mart tables queried directly from DuckDB:

| Tab | Key Visuals |
|-----|-------------|
| **Daily Ridership** | Area chart (daily trips), top-10 corridor bar, completion rate histogram |
| **Corridors** | Distance vs duration scatter (bubble = volume), revenue bar, full stats table |
| **Stop Performance** | Geo scatter map (bubble = boardings, color = score), top-20 table, score distribution |
| **Surge Analysis** | Corridor selector → demand heatmap (day × hour), peak slots table, hourly bar |

Cold-start: if `datavault.duckdb` is absent (fresh Streamlit Cloud deploy), the app auto-runs `load_raw.py` → `dbt build` before serving (~30s).

**Deploy to Streamlit Cloud:**
1. Push repo to GitHub
2. [share.streamlit.io](https://share.streamlit.io) → New app
3. Repo: this repo, Branch: `main`, Main file: `dashboard/app.py`

---

## Key Numbers (April 2023)

| Metric | Value |
|--------|-------|
| Total trips | 182,520 |
| Complete trips (tap-in + tap-out) | 170,622 (93.5%) |
| Total revenue | Rp 478.1M |
| Active corridors | 221 |
| Unique stops with boardings | 5,221 |
| Avg distance (complete trips) | 2.71 km |
| Avg duration (complete trips) | ~45 min |
| Peak demand index | 4.93× above corridor average |
| Date range | 2023-04-01 → 2023-04-30 |

---

## Future Improvements

### Data Quality

- **Resolve 6,989 null `tap_in_stop_id` rows** — these rows have a valid `tap_in_stop_name` but no ID. Cross-reference stop names against the stops seed to back-fill IDs. Currently they are retained but cannot join to `stg_stops`, inflating incomplete trip counts.
- **103 corridors report zero revenue** — likely all free/transfer trips on those corridors. Flag them explicitly in `mart_corridor_stats` rather than surfacing `total_revenue = 0` as if it were real revenue.
- **16,535 riders aged under 15 or over 80** — `payCardBirthDate` is user-reported birth year; outliers exist. Consider a `birth_year_valid` flag in staging and exclude from age-based analyses rather than silently including them.
- **1 complete trip with `distance_km = 0`** — tap-in and tap-out at the same geo point. Add a `distance_km > 0` assertion at warn severity to surface these.
- **`corridor_name` is null in a fraction of transactions** — root cause unknown. Backfill from `stg_corridors` seed via `corridor_id` join in staging instead of working around it with `MAX(corridor_name)` in every mart.

### dbt Models

- **`mart_stop_performance` scoring is simplistic** — min-max normalization against a single month means the top stop always scores 68 (not 100) because no single stop dominates both volume and revenue. Consider z-score normalization or a percentile rank instead, which also handles outliers better.
- **No incremental models** — all models are full-refresh views or tables. For a multi-month dataset, `int_trips_enriched` and the mart tables should be `incremental` materialized on `trip_date` to avoid reprocessing historical data on every run.
- **Macros directory is empty** — the Haversine formula is inlined in `int_trips_enriched.sql`. Extract it to a `macros/haversine.sql` macro so it can be reused and unit-tested independently.
- **No dbt snapshots** — if the source data were live (e.g. daily feed), a snapshot on `raw_transjakarta` would capture slowly-changing dimensions like corridor route changes. Overkill for a static dataset but worth adding if extended to multi-month data.
- **No `analyses/` queries** — the `analyses/` directory exists but is empty. Add ad-hoc SQL (e.g. top corridors by revenue per km, rider demographics by corridor) as compiled-but-not-materialized analyses for documentation purposes.
- **`mart_surge_analysis` has no corridor-level baseline** — the `demand_index` is relative to a corridor's own average, which is correct, but there is no cross-corridor comparison. A second column showing each slot's rank within the system would help identify city-wide peak hours independent of per-corridor variance.

### Testing

- **No SQLFluff lint** — SQL style is consistent by convention but not enforced. Add `sqlfluff lint` as a CI step with a `datavault_dbt/.sqlfluff` config.
- **CI has no dependency cache** — `uv sync` and `dbt deps` run from scratch on every CI run. Add `actions/cache` on the uv cache dir and `datavault_dbt/dbt_packages/` to cut CI time significantly.
- **No dbt source freshness check** — `dbt source freshness` is not configured. For a static dataset this is moot, but adding a `loaded_at_field` on the source definition future-proofs the pipeline for scheduled ingestion.
- **No mutation testing** — the pytest suite has 41 assertions but their kill ratio is unknown. Run `mutmut` against `scripts/` to verify the tests actually catch logic regressions.
- **`test_phase3.py` performance thresholds are loose** — the `<1s` query time tests pass trivially because DuckDB is fast. Tighten thresholds (e.g. `<0.1s` for table scans) or switch to profiling row-counts-per-second for a more meaningful gate.

### Dashboard

- **No date range filter** — the ridership and surge tabs show April 2023 in full with no way to zoom in. A `st.date_input` range selector on the sidebar, passed as a query parameter, would make the heatmap far more readable for specific weeks.
- **No corridor filter on the ridership tab** — users cannot drill into a single corridor's daily trend. The surge tab has a corridor selector; the daily ridership chart should match.
- **Stop map requires internet** — `scatter_mapbox` with `carto-positron` tile loads tiles from the web. Replace with a static `scatter_geo` or embed a local tile server for offline/air-gapped use.
- **No CSV/Excel export** — add a `st.download_button` on the corridor stats and stop performance tables so analysts can pull data without direct DuckDB access.
- **KPI `unique_riders` is overcounted** — `SUM(unique_riders)` across `mart_daily_ridership` counts the same card on multiple days multiple times. The header should query `COUNT(DISTINCT card_id)` from `stg_transactions` directly, or add a `mart_rider_summary` table.

### Pipeline & Infrastructure

- **No multi-month support** — the pipeline is hardcoded for April 2023 (`age_years = 2023 - birth_year`). To extend to a multi-month dataset, `age_years` should use `EXTRACT(YEAR FROM tap_in_time)` instead of the literal `2023`.
- **`load_raw.py` has no idempotency guard** — `CREATE OR REPLACE VIEW` is idempotent, but if the CSV is missing it raises an unhandled `FileNotFoundError`. The script should exit with a clear user-facing error message and non-zero exit code.
- **No data contract between raw and staging** — if the upstream CSV adds or renames columns, `stg_transactions` silently drops them. A `dbt source` column list with `not_null` and type tests would catch schema drift on the next `dbt build`.
- **`dashboard/app.py` cold-start runs `dbt build` in-process** — this works on Streamlit Cloud but is fragile: the subprocess inherits the app's working directory and PATH, which may differ across environments. A better approach is to build the DuckDB file as a CI artifact and mount it at deploy time.
- **No `pre-commit` hooks** — SQL and Python formatting are not enforced locally. Add `pre-commit` with `sqlfluff`, `ruff`, and `pyright` to catch issues before they reach CI.
