"""Sanity checks on raw_transjakarta view. Fails fast if data is malformed."""

import duckdb
import os
import sys

DB_PATH = os.environ.get("DUCKDB_PATH", "datavault.duckdb")

REQUIRED_COLS = [
    "transID", "payCardBank", "payCardSex", "payCardBirthDate",
    "corridorID", "corridorName", "direction",
    "tapInStops", "tapInStopsName", "tapInStopsLat", "tapInStopsLon",
    "tapOutStops", "tapInTime", "tapOutTime", "payAmount",
]


def verify():
    con = duckdb.connect(DB_PATH, read_only=True)
    errors = []

    row_count = con.execute("SELECT COUNT(*) FROM raw_transjakarta").fetchone()[0]
    print(f"Row count: {row_count:,}")
    if row_count < 100_000:
        errors.append(f"Expected >30k rows, got {row_count}")

    cols = con.execute("DESCRIBE raw_transjakarta").fetchdf()["column_name"].tolist()
    missing = [c for c in REQUIRED_COLS if c not in cols]
    if missing:
        errors.append(f"Missing columns: {missing}")
    else:
        print("Required columns: PASS")

    for col in ["tapInTime", "payAmount"]:
        null_rate = con.execute(
            f"SELECT COUNT(*) FILTER (WHERE {col} IS NULL) * 1.0 / COUNT(*) FROM raw_transjakarta"
        ).fetchone()[0]
        print(f"Null rate {col}: {null_rate:.2%}")
        # payAmount can be null for free/transfer trips; tapInTime must be near-zero null
        threshold = 0.01 if col == "tapInTime" else 0.05
        if null_rate > threshold:
            errors.append(f"{col} null rate {null_rate:.2%} exceeds {threshold:.0%}")

    con.close()

    if errors:
        print("\nFAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    verify()
