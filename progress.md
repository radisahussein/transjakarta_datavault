# DataVault — Progress Log

Project: dbt + DuckDB Analytics Engineering (NYC Taxi)
Repo: datavault
Branch strategy: `stage` → `phase/<N>-<description>` → PR → merge

---

## Phase Status

| Phase | Name | Status | Branch |
|-------|------|--------|--------|
| 1 | Project Foundation & Raw Data Pipeline | NOT STARTED | — |
| 2 | Staging Layer | NOT STARTED | — |
| 3 | Intermediate + Mart Layer | NOT STARTED | — |
| 4 | CI Pipeline & dbt Docs | NOT STARTED | — |
| 5 | Dashboard + Deploy | NOT STARTED | — |

---

## Phase 1: Project Foundation & Raw Data Pipeline — NOT STARTED

### What Must Be Done
- [ ] `uv init datavault`, add all deps
- [ ] Create full directory structure
- [ ] `dbt init datavault_dbt --skip-profile-setup`
- [ ] Create `profiles.yml` with dbt-duckdb config
- [ ] Update `datavault_dbt/dbt_project.yml` (profile, materializations)
- [ ] Create `datavault_dbt/packages.yml` with dbt-utils + dbt-expectations
- [ ] Run `dbt deps`
- [ ] Download taxi_zones.csv → `datavault_dbt/seeds/taxi_zones.csv`
- [ ] Create `scripts/download_data.py`
- [ ] Create `scripts/load_raw.py` (DuckDB view over Parquet glob)
- [ ] Create `data/sample/yellow_tripdata_sample.parquet` (10k rows, committed)
- [ ] Create `scripts/verify_raw.py` with assertions
- [ ] Create `tests/test_phase1.py`
- [ ] Run `dbt seed` → verify 265 rows
- [ ] Run `dbt debug` → all checks pass
- [ ] Run `pytest tests/test_phase1.py` → 5 passed
- [ ] Run `python scripts/verify_raw.py` → ALL CHECKS PASSED
- [ ] Update this file with results
- [ ] End session, wait for verification

---

<!-- Phases 2-5 will be filled in as they are completed -->
