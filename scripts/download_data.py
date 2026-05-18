"""Download TransJakarta dataset from Kaggle.

Requires ~/.kaggle/kaggle.json with valid API credentials.
Get your token at: https://www.kaggle.com/settings → API → Create New Token
"""

import os
import zipfile
from pathlib import Path

DATASET = "dikasiganteng/transjakarta"
OUT_DIR = Path("data/raw")


def download():
    import kaggle  # noqa: F401 — triggers credential check on import
    from kaggle.api.kaggle_api_extended import KaggleApiExtended

    api = KaggleApiExtended()
    api.authenticate()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / "transjakarta.csv"

    if target.exists():
        print(f"Already exists: {target} ({target.stat().st_size // 1024}KB)")
        return

    print(f"Downloading {DATASET} ...")
    api.dataset_download_files(DATASET, path=str(OUT_DIR), unzip=False)

    # Unzip the downloaded archive
    zips = list(OUT_DIR.glob("*.zip"))
    if zips:
        with zipfile.ZipFile(zips[0]) as z:
            z.extractall(OUT_DIR)
        zips[0].unlink()

    # Rename to canonical name if needed
    csvs = [f for f in OUT_DIR.glob("*.csv") if f.name != "transjakarta.csv"]
    if csvs:
        csvs[0].rename(target)

    if target.exists():
        print(f"Saved: {target} ({target.stat().st_size // 1024}KB)")
    else:
        raise FileNotFoundError(f"Expected {target} after download — check Kaggle dataset contents")


if __name__ == "__main__":
    download()
