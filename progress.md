# DataVault — Progress Log

Project: dbt + DuckDB Analytics Engineering (TransJakarta BRT)
Repo: datavault
Branch strategy: `stage` → `phase/<N>-<description>` → PR → merge

---

## Phase Status

| Phase | Name | Status | Branch |
|-------|------|--------|--------|
| 1 | Project Foundation & Raw Data Pipeline | DONE | phase/1-foundation |
| 2 | Staging Layer | NOT STARTED | — |
| 3 | Intermediate + Mart Layer | NOT STARTED | — |
| 4 | CI Pipeline & dbt Docs | NOT STARTED | — |
| 5 | Dashboard + Deploy | NOT STARTED | — |

---

## Phase 1: Project Foundation & Raw Data Pipeline — DONE

**Completed:** 2026-05-19

### What Was Done

- uv project initialized with dbt-core, dbt-duckdb, streamlit, plotly, pandas, pytest, httpx, kaggle
- Directory structure: `scripts/`, `dashboard/`, `tests/`, `data/raw/`, `datavault_dbt/`
- `dbt init datavault_dbt` — removed example models, created `models/staging/`, `models/intermediate/`, `models/marts/`
- `profiles.yml` — dbt-duckdb adapter, reads `DUCKDB_PATH` env var
- `datavault_dbt/dbt_project.yml` — profile=datavault, staging=view, intermediate=view, marts=table
- `datavault_dbt/packages.yml` — dbt-utils + dbt-expectations, `dbt deps` run
- `data/raw/transjakarta.csv` — April 2023, **189,500 rows**, 22 columns (committed to repo, ~42MB)
- `datavault_dbt/seeds/stops.csv` — 5,250 unique tap-in stops with lat/lon
- `datavault_dbt/seeds/corridors.csv` — 221 unique corridors
- `scripts/generate_seeds.py` — extracts stops + corridors from raw CSV
- `scripts/load_raw.py` — creates DuckDB view `raw_transjakarta` over CSV
- `scripts/verify_raw.py` — row count, null rate, column assertions
- `scripts/download_data.py` — Kaggle Bearer token download (via kaggle.json key)
- `tests/test_phase1.py` — 7 tests
- `.gitignore` — excludes *.duckdb, __pycache__, dbt target/

**Schema correction discovered:** dataset has `payCardBirthDate` (YYYYMMDD int), not `payCardAge`. All files updated accordingly. `payAmount` null rate is 1.96% (legitimate — free/transfer trips), threshold set to 5%.

### Test Results

```
dbt debug:   All checks passed.
dbt seed:    PASS=2 WARN=0 ERROR=0 (corridors: 221 rows, stops: 5250 rows)
pytest:      7 passed in 0.45s (run twice — deterministic)
verify_raw:  Row count: 189,500 | tapInTime null: 0.00% | payAmount null: 1.96% | ALL CHECKS PASSED
```

### Commits

- `8c678ff` chore: initial project setup - plans, progress tracker, CLAUDE.md
- `f2f90ba` chore: init uv project with dbt-core, dbt-duckdb, plotly, streamlit deps
- `d43f9eb` chore: init dbt project structure with profiles.yml and dbt_project.yml
- `ea9f494` feat: add data pipeline scripts for TransJakarta raw data
- `9114be8` feat: add test_phase1.py with 7 assertions for Phase 1 verification
- `927b129` feat: add raw TransJakarta CSV and generated seed files
- `62e8b1a` fix: update column refs from payCardAge to payCardBirthDate, adjust thresholds

---

## Phase 2: Staging Layer — NOT STARTED

### What Must Be Done
- [ ] Create `datavault_dbt/models/staging/sources.yml` — define `tlc.raw_transjakarta` source
- [ ] Create `stg_transactions.sql` — clean, cast, filter (remove null tap-out, invalid pay)
- [ ] Create `stg_stops.sql` — from seed ref, with surrogate key
- [ ] Create `stg_corridors.sql` — from seed ref
- [ ] Create `_stg_transactions.yml` — schema tests: not_null, unique, accepted_values, dbt_expectations ranges
- [ ] Create `_stg_stops.yml` and `_stg_corridors.yml` — not_null, unique tests
- [ ] Create `tests/test_phase2.py` — pytest on stg layer data quality
- [ ] Run `dbt build --select staging --project-dir datavault_dbt --profiles-dir .` → PASS=XX WARN=0 ERROR=0
- [ ] Run `pytest tests/test_phase2.py -v` → all passed
- [ ] Run both twice for determinism check
- [ ] Update progress.md
- [ ] End session, wait for verification
