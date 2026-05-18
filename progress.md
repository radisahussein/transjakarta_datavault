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
| 3 | Intermediate + Mart Layer | NOT STARTED | — |
| 4 | CI Pipeline & dbt Docs | NOT STARTED | — |
| 5 | Dashboard + Deploy | NOT STARTED | — |

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

## Phase 3: Intermediate + Mart Layer — NOT STARTED

### What Must Be Done
- [ ] `int_trips_enriched.sql` — join stg_transactions + stg_stops (tap-in), derive: duration_min, distance_km (Haversine), hour_of_day, day_of_week, is_complete_trip
- [ ] `mart_daily_ridership.sql` — daily trip count + revenue by corridor
- [ ] `mart_corridor_flow.sql` — O-D matrix between corridors (complete trips only)
- [ ] `mart_stop_performance.sql` — composite score 0-100 per stop (volume 40% + revenue 40% + tip-equivalent 20%)
- [ ] `mart_surge_analysis.sql` — trips by hour × day × corridor demand index
- [ ] `_int_trips_enriched.yml` — schema tests
- [ ] `_marts.yml` — schema tests for all 4 mart tables
- [ ] Custom SQL generic tests: `assert_positive_revenue.sql`, `assert_stop_score_range.sql`
- [ ] `tests/test_phase3.py` — row counts, ranges, performance (<1s queries)
- [ ] Run `dbt build --project-dir datavault_dbt --profiles-dir .` → PASS=XX WARN=1 ERROR=0
- [ ] Run `pytest tests/test_phase3.py -v` → all passed
- [ ] Run both twice for determinism
- [ ] Update progress.md
- [ ] End session, wait for verification
