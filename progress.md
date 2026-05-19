# DataVault — Progress Log

Project: dbt + DuckDB Analytics Engineering (TransJakarta BRT)
Repo: datavault
Branch strategy: `stage` → `phase/<N>-<description>` → PR → merge

---

## Phase Status

| Phase | Name | Status | Branch |
|-------|------|--------|--------|
| 1 | Project Foundation & Raw Data Pipeline | DONE | phase/1-foundation |
| 2 | Staging Layer | DONE | phase/2-staging |
| 3 | Intermediate + Mart Layer | DONE | phase/3-marts |
| 4 | CI Pipeline & dbt Docs | DONE | phase/4-ci |
| 5 | Dashboard + Deploy | DONE | phase/5-dashboard |

---

## Phase 1: Project Foundation & Raw Data Pipeline — DONE

**Completed:** 2026-05-19

### Test Results
```
dbt debug:   All checks passed.
dbt seed:    PASS=2 WARN=0 ERROR=0 (corridors: 221, stops: 5250)
pytest:      7 passed (run twice, deterministic)
verify_raw:  Row count: 189,500 | ALL CHECKS PASSED
```

---

## Phase 2: Staging Layer — DONE

**Completed:** 2026-05-19

### What Was Done

- `models/staging/sources.yml` — defines `transjakarta.raw_transjakarta` source (schema: main)
- `stg_transactions.sql` — casts all columns, derives `age_years` from birth year, adds `has_tap_out` flag, filters null corridorID (~6,980 rows removed)
- `stg_stops.sql` — from seed ref, filters null stop_id
- `stg_corridors.sql` — from seed ref, filters null corridor_id
- `_stg_transactions.yml` — 12 schema tests (not_null, unique, accepted_values, dbt_expectations ranges)
- `_stg_stops_corridors.yml` — 8 schema tests (not_null, unique, Jakarta lat/lon bounds)
- `tests/test_phase2.py` — 13 pytest assertions

**Data quality discoveries:**
- `payCardSex` = 'F'/'M' (not 'L'/'P' as assumed in plan)
- `payCardBirthDate` = birth year only (e.g. 1993), not YYYYMMDD
- `tapInStops` null in ~6,989 rows where `tapInStopsName` has value — upstream issue, rows retained with `tap_in_stop_id` test set to `warn` severity
- `payAmount` null in ~3,718 rows (free/transfer trips) — retained, threshold 5%

### Test Results
```
dbt build --select staging:  PASS=29 WARN=1 ERROR=0 SKIP=0 TOTAL=30
  (WARN: not_null_stg_transactions_tap_in_stop_id — documented data quality issue)
pytest tests/test_phase2.py: 13 passed in 1.18s (run twice, deterministic)
```

### Commits
- `1a0a411` feat: add sources.yml defining transjakarta.raw_transjakarta source
- `e0bb1fd` feat: add stg_transactions staging model
- `f7fa1e3` feat: add stg_stops and stg_corridors staging models from seed refs
- `37ad971` test: add schema tests for staging layer
- `33b9970` fix: downgrade tap_in_stop_id not_null to warn severity
- `5aca295` feat: add test_phase2.py - 13 assertions for staging layer quality

---

## Phase 3: Intermediate + Mart Layer — DONE

**Completed:** 2026-05-19

### What Was Done

- `models/intermediate/int_trips_enriched.sql` — joins stg_transactions + stg_stops; derives hour_of_day, day_of_week (ISODOW), trip_date, duration_min, distance_km (Haversine), is_complete_trip flag
- `models/marts/mart_daily_ridership.sql` — daily trips + revenue aggregated by corridor_id × trip_date (6,282 rows)
- `models/marts/mart_corridor_stats.sql` — per-corridor aggregates: total_trips, completion_rate_pct, avg_distance_km, avg_duration_min, total_revenue (221 rows)
- `models/marts/mart_stop_performance.sql` — stop-level boardings + revenue, normalized performance_score 0-100 (5,221 rows)
- `models/marts/mart_surge_analysis.sql` — hour × day_of_week × corridor demand_index relative to corridor hourly avg (21,462 rows)
- `_int_trips_enriched.yml` — 7 schema tests (not_null, unique, range checks on hour, day, distance, duration)
- `_marts.yml` — 26 schema tests across all 4 mart tables
- `datavault_dbt/tests/assert_positive_revenue.sql` — custom test: no negative revenue
- `datavault_dbt/tests/assert_stop_score_range.sql` — custom test: score 0-100
- `tests/test_phase3.py` — 21 pytest assertions (row counts, ranges, totals, performance)

**Data discoveries:**
- `corridor_name` is NULL for a small fraction of transactions — GROUP BY corridor_id only (MAX(corridor_name))
- 170,622 complete trips (has_tap_out=true AND geo data on both ends) out of 182,520 total
- Distance range: 0-22.6 km; duration: 15-180 min; demand_index peak: 6.09×

### Test Results
```
dbt build (full):   PASS=71 WARN=1 ERROR=0 SKIP=0 TOTAL=72 (run twice, deterministic)
  (WARN: not_null_stg_transactions_tap_in_stop_id — documented Phase 2 data quality issue)
pytest test_phase3.py: 21 passed in 1.42s (run twice, deterministic)
```

### Commits
- `feat: add int_trips_enriched intermediate model`
- `feat: add mart_daily_ridership, mart_corridor_stats, mart_stop_performance, mart_surge_analysis`
- `test: add schema tests for intermediate and mart layers`
- `test: add custom SQL generic tests assert_positive_revenue, assert_stop_score_range`
- `feat: add test_phase3.py - 21 assertions for intermediate and mart layer quality`

---

## Phase 4: CI Pipeline & dbt Docs — DONE

**Completed:** 2026-05-19

### What Was Done

- `.github/workflows/ci.yml` — triggers on every push + PRs to main/stage; steps: checkout → Python 3.11 → uv → `uv sync` → `load_raw.py` → `dbt deps` → `dbt build` → `pytest tests/ -v`
- `.github/workflows/docs.yml` — triggers on push to main; generates `dbt docs` artifacts (manifest.json, catalog.json, index.html) and deploys to GitHub Pages via `actions/deploy-pages`
- `dbt docs generate` verified locally — catalog.json + index.html produced cleanly
- Full suite re-verified on phase/4 branch: PASS=71 WARN=1 ERROR=0, 41 pytest passed (run twice, deterministic)

### Test Results
```
dbt build:  PASS=71 WARN=1 ERROR=0 SKIP=0 TOTAL=72 (run twice, deterministic)
pytest:     41 passed in 3.45s (all phases — run twice, deterministic)
```

### Commits
- `ci: add GitHub Actions CI workflow — dbt build + pytest on push/PR`
- `ci: add GitHub Actions docs workflow — dbt docs → GitHub Pages on main push`

---

## Phase 5: Dashboard + Deploy — DONE

**Completed:** 2026-05-19

### What Was Done

- `dashboard/app.py` — Streamlit dashboard with 4 tabs:
  - **Daily Ridership**: area chart of daily trips, top-10 corridor bar, completion rate histogram
  - **Corridors**: scatter (distance vs duration, bubble = volume), revenue bar, full stats table
  - **Stop Performance**: geo scatter map (lat/lon, bubble = boardings, color = score), top-20 table, score histogram
  - **Surge Analysis**: corridor selector → demand heatmap (day × hour), peak slots table, hourly bar
  - KPI header: total trips (182,520), total revenue (Rp 478.1M), active corridors (221), unique riders
  - Cold-start bootstrap: if `datavault.duckdb` absent, runs `load_raw.py` → `dbt deps` → `dbt build` automatically
- `requirements.txt` — pinned deps for Streamlit Cloud: dbt-core, dbt-duckdb, duckdb, pandas, plotly, streamlit
- `.streamlit/config.toml` — theme config + headless server for cloud deploy

**Deploy to Streamlit Cloud:**
1. Push repo to GitHub (public or private with access)
2. Go to share.streamlit.io → New app
3. Repo: this repo, Branch: `main`, Main file: `dashboard/app.py`
4. On first load: cold-start bootstrap runs (~30s), then dashboard is live

### Test Results
```
dbt build:  PASS=71 WARN=1 ERROR=0 SKIP=0 TOTAL=72 (run twice, deterministic)
pytest:     41 passed in 3.13s (all phases — run twice, deterministic)
Dashboard:  HTTP 200 on localhost:8501, all 4 data queries validated
```

### Commits
- `feat: add Streamlit dashboard with 4 tabs — ridership, corridors, stop performance, surge heatmap`
- `chore: add requirements.txt and Streamlit config for cloud deploy`
