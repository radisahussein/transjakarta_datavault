"""Download TransJakarta dataset from Kaggle using Bearer token auth.

Reads token from ~/.kaggle/access_token (new OAuth format: KGAT_...).
Setup: mkdir -p ~/.kaggle && echo YOUR_TOKEN > ~/.kaggle/access_token
"""

import zipfile
from pathlib import Path
import httpx

DATASET_OWNER = "dikasiganteng"
DATASET_NAME = "transjakarta"
API_URL = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET_OWNER}/{DATASET_NAME}"
TOKEN_PATH = Path.home() / ".kaggle/access_token"
JSON_PATH = Path.home() / ".kaggle/kaggle.json"
OUT_DIR = Path("data/raw")
TARGET = OUT_DIR / "transjakarta.csv"


def _token() -> str:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()
    if JSON_PATH.exists():
        import json
        return json.loads(JSON_PATH.read_text())["key"]
    raise FileNotFoundError(
        "Kaggle credentials not found. Tried:\n"
        f"  {TOKEN_PATH}\n"
        f"  {JSON_PATH}\n"
        "Create one: mkdir -p ~/.kaggle && echo YOUR_KGAT_TOKEN > ~/.kaggle/access_token"
    )


def download():
    if TARGET.exists():
        print(f"Already exists: {TARGET} ({TARGET.stat().st_size // 1024}KB)")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    token = _token()

    print(f"Downloading {DATASET_OWNER}/{DATASET_NAME} ...")
    with httpx.stream(
        "GET",
        API_URL,
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=True,
        timeout=120,
    ) as r:
        r.raise_for_status()
        zip_path = OUT_DIR / f"{DATASET_NAME}.zip"
        with open(zip_path, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=8192):
                f.write(chunk)

    print("Extracting ...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(OUT_DIR)
    zip_path.unlink()

    # Rename to canonical name if the extracted file differs
    csvs = [f for f in OUT_DIR.glob("*.csv") if f.name != "transjakarta.csv"]
    if csvs and not TARGET.exists():
        csvs[0].rename(TARGET)

    if not TARGET.exists():
        raise FileNotFoundError(f"{TARGET} not found after extraction — check zip contents")

    print(f"Saved: {TARGET} ({TARGET.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    download()
