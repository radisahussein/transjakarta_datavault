"""Extract unique stops and corridors from raw CSV → write as dbt seed files."""

import pandas as pd
from pathlib import Path

RAW_CSV = Path("data/raw/transjakarta.csv")
SEEDS_DIR = Path("datavault_dbt/seeds")


def generate():
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"{RAW_CSV} not found. Run download_data.py first.")

    df = pd.read_csv(RAW_CSV)

    # stops seed — unique tap-in stops (use tap-in side; tap-out may have nulls)
    stops = (
        df[["tapInStops", "tapInStopsName", "tapInStopsLat", "tapInStopsLon"]]
        .dropna()
        .drop_duplicates(subset=["tapInStops"])
        .rename(columns={
            "tapInStops": "stop_id",
            "tapInStopsName": "stop_name",
            "tapInStopsLat": "lat",
            "tapInStopsLon": "lon",
        })
        .sort_values("stop_id")
        .reset_index(drop=True)
    )
    stops_path = SEEDS_DIR / "stops.csv"
    stops.to_csv(stops_path, index=False)
    print(f"stops.csv: {len(stops)} rows → {stops_path}")

    # corridors seed — unique corridors
    corridors = (
        df[["corridorID", "corridorName"]]
        .dropna()
        .drop_duplicates(subset=["corridorID"])
        .rename(columns={"corridorID": "corridor_id", "corridorName": "corridor_name"})
        .sort_values("corridor_id")
        .reset_index(drop=True)
    )
    corridors_path = SEEDS_DIR / "corridors.csv"
    corridors.to_csv(corridors_path, index=False)
    print(f"corridors.csv: {len(corridors)} rows → {corridors_path}")


if __name__ == "__main__":
    generate()
