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

### Completed Steps (continued)
- [x] Create `scripts/download_data.py` (Kaggle API download)
- [x] Create `scripts/generate_seeds.py` (extract stops.csv + corridors.csv)
- [x] Create `scripts/load_raw.py` (DuckDB view over CSV)
- [x] Create `scripts/verify_raw.py` (row count + column assertions)
- [x] Create `tests/test_phase1.py` (7 tests)
- [x] Create `.gitignore`

### BLOCKED — Manual Step Required

**User must download the dataset before tests can run:**

```bash
# Option A: Kaggle CLI (set up credentials first)
# 1. Go to https://www.kaggle.com/settings → API → Create New Token
# 2. Place downloaded kaggle.json at ~/.kaggle/kaggle.json
# 3. chmod 600 ~/.kaggle/kaggle.json
uv run python scripts/download_data.py

# Option B: Manual browser download
# 1. Go to https://www.kaggle.com/datasets/dikasiganteng/transjakarta
# 2. Download the dataset ZIP
# 3. Unzip and rename the CSV to: data/raw/transjakarta.csv
```

### After Data Is Placed — Run These In Order

```bash
# Generate seeds from raw data
uv run python scripts/generate_seeds.py

# Commit seeds + raw CSV
git add data/raw/transjakarta.csv datavault_dbt/seeds/stops.csv datavault_dbt/seeds/corridors.csv

# Load raw view into DuckDB
uv run python scripts/load_raw.py

# Run dbt debug
uv run dbt debug --project-dir datavault_dbt --profiles-dir .

# Run dbt seed
uv run dbt seed --project-dir datavault_dbt --profiles-dir .

# Run tests
uv run pytest tests/test_phase1.py -v

# Verify raw data
uv run python scripts/verify_raw.py

# Run tests second time (determinism check)
uv run pytest tests/test_phase1.py -v
```

Expected: 7 passed, ALL CHECKS PASSED. Then commit progress.md + end session.

---

<!-- Phases 2-5 will be filled in as they are completed -->
