# DataVault — Progress Log

Project: dbt + DuckDB Analytics Engineering (TransJakarta BRT)
Repo: datavault
Branch strategy: `stage` → `phase/<N>-<description>` → PR → merge

---

## Phase Status

| Phase | Name | Status | Branch |
|-------|------|--------|--------|
| 1 | Project Foundation & Raw Data Pipeline | IN PROGRESS | phase/1-foundation |
| 2 | Staging Layer | NOT STARTED | — |
| 3 | Intermediate + Mart Layer | NOT STARTED | — |
| 4 | CI Pipeline & dbt Docs | NOT STARTED | — |
| 5 | Dashboard + Deploy | NOT STARTED | — |

---

## Phase 1: Project Foundation & Raw Data Pipeline — IN PROGRESS

### Completed Steps
- [x] `uv init datavault`, add all deps (dbt-core, dbt-duckdb, streamlit, plotly, pandas, pytest, httpx)
- [x] Create directory structure: `scripts/`, `dashboard/`, `tests/`, `data/raw/`, `data/sample/`
- [x] `dbt init datavault_dbt --skip-profile-setup`
- [x] Remove dbt example models, create `models/staging/`, `models/intermediate/`, `models/marts/`
- [x] Create `profiles.yml` with dbt-duckdb config (reads `DUCKDB_PATH` env var, defaults to `datavault.duckdb`)
- [x] Update `datavault_dbt/dbt_project.yml` (profile=datavault, staging=view, intermediate=view, marts=table)
- [x] Create `datavault_dbt/packages.yml` with dbt-utils + dbt-expectations
- [x] Run `dbt deps` → dbt_utils, dbt_expectations, dbt_date installed

### What Must Be Done Next
- [ ] Place raw CSV: `data/raw/transjakarta.csv` (download from Kaggle, commit to repo)
- [ ] Create `scripts/generate_seeds.py` → extract stops.csv + corridors.csv → commit seeds
- [ ] Create `scripts/load_raw.py` (DuckDB view over transjakarta CSV)
- [ ] Create `scripts/verify_raw.py` with column + row assertions
- [ ] Create `tests/test_phase1.py` (7 tests)
- [ ] Run `dbt seed --project-dir datavault_dbt --profiles-dir .` → verify stops + corridors rows
- [ ] Run `dbt debug --project-dir datavault_dbt --profiles-dir .` → All checks passed
- [ ] Run `uv run pytest tests/test_phase1.py -v` → 7 passed
- [ ] Run `uv run python scripts/verify_raw.py` → ALL CHECKS PASSED
- [ ] Run tests second time to confirm deterministic
- [ ] Commit progress.md update
- [ ] End session, wait for verification

---

<!-- Phases 2-5 will be filled in as they are completed -->
