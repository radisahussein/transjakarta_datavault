import yaml
import duckdb
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW_CSV = ROOT / "data/raw/transjakarta.csv"
REQUIRED_COLS = [
    "transID", "payCardBank", "payCardSex", "payCardBirthDate",
    "corridorID", "corridorName", "direction",
    "tapInStops", "tapInStopsName", "tapInStopsLat", "tapInStopsLon",
    "tapOutStops", "tapInTime", "tapOutTime", "payAmount",
]


def test_raw_csv_exists():
    assert RAW_CSV.exists(), (
        "data/raw/transjakarta.csv not found. "
        "Run: uv run python scripts/download_data.py"
    )


def test_stops_seed_exists():
    assert (ROOT / "datavault_dbt/seeds/stops.csv").exists(), (
        "seeds/stops.csv missing. Run: uv run python scripts/generate_seeds.py"
    )


def test_corridors_seed_exists():
    assert (ROOT / "datavault_dbt/seeds/corridors.csv").exists(), (
        "seeds/corridors.csv missing. Run: uv run python scripts/generate_seeds.py"
    )


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
    assert cfg["models"]["datavault_dbt"]["staging"]["+materialized"] == "view"


def test_raw_csv_row_count():
    con = duckdb.connect()
    n = con.execute(
        f"SELECT COUNT(*) FROM read_csv('{RAW_CSV}', auto_detect=true)"
    ).fetchone()[0]
    con.close()
    assert n > 100_000, f"Expected >100k rows, got {n}"


def test_raw_csv_required_columns():
    con = duckdb.connect()
    df = con.execute(
        f"SELECT * FROM read_csv('{RAW_CSV}', auto_detect=true) LIMIT 1"
    ).fetchdf()
    con.close()
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"
