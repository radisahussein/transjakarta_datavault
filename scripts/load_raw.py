"""Create DuckDB view over raw TransJakarta CSV."""

import duckdb
import os
from pathlib import Path

RAW_CSV = Path("data/raw/transjakarta.csv")
DB_PATH = os.environ.get("DUCKDB_PATH", "datavault.duckdb")


def load():
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"{RAW_CSV} not found. Run download_data.py first.")

    con = duckdb.connect(DB_PATH)
    con.execute(f"""
        CREATE OR REPLACE VIEW raw_transjakarta AS
        SELECT * FROM read_csv('{RAW_CSV}', auto_detect=true)
    """)

    row_count = con.execute("SELECT COUNT(*) FROM raw_transjakarta").fetchone()[0]
    min_ts = con.execute("SELECT MIN(tapInTime) FROM raw_transjakarta").fetchone()[0]
    max_ts = con.execute("SELECT MAX(tapInTime) FROM raw_transjakarta").fetchone()[0]

    print(f"raw_transjakarta view created → {DB_PATH}")
    print(f"  rows:        {row_count:,}")
    print(f"  tapInTime:   {min_ts} → {max_ts}")

    con.close()


if __name__ == "__main__":
    load()
