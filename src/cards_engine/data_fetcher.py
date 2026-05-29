# src/cards_engine/data_fetcher.py

"""
Downloads the card data file from the json-against-humanity repository on
first run and caches it in data/  (which is .gitignore'd so it is never
committed).

Call ensure_data() once at startup — it is a no-op when the file already
exists.
"""

import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — change these if the upstream source ever moves
# ---------------------------------------------------------------------------

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "crhallberg/json-against-humanity/latest/cah-all-full.json"
)

_HERE = Path(__file__).parent
_PROJECT_ROOT = (_HERE / ".." / "..").resolve()
DATA_DIR = _PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "cah-all-full.json"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_data(
    url: str = DATA_URL,
    dest: Path = DATA_FILE,
    force: bool = False,
    quiet: bool = False,
) -> Path:
    """
    Ensure the card data file exists at *dest*.

    - If the file already exists and *force* is False, returns immediately.
    - Otherwise downloads from *url* and writes to *dest*.
    - Raises RuntimeError on download failure so the caller can decide how
      to handle it (crash loudly, fall back to a stub deck, etc.).

    Returns the path to the data file.
    """
    dest = Path(dest)

    if dest.exists() and not force:
        if not quiet:
            print(f"[DataFetcher] Card data already present at {dest}")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)

    _log(f"[DataFetcher] Downloading card data from {url} ...", quiet)
    tmp = dest.with_suffix(".tmp")
    try:
        _download(url, tmp)
        tmp.replace(dest)
        _log(f"[DataFetcher] Saved to {dest} ({dest.stat().st_size / 1_000_000:.1f} MB)", quiet)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"[DataFetcher] Failed to download card data from {url!r}.\n"
            f"  Error: {exc}\n"
            f"  You can manually place cah-all-full.json in {dest.parent}."
        ) from exc

    return dest


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _download(url: str, dest: Path) -> None:
    """Stream *url* to *dest*, showing a simple progress indicator."""
    req = urllib.request.Request(url, headers={"User-Agent": "cards-against-bubba/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 64 * 1024  # 64 KB

        with open(dest, "wb") as f:
            while True:
                data = response.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r[DataFetcher] {pct:5.1f}%  ({downloaded // 1024} KB)", end="", flush=True)
        if total:
            print()  # newline after progress bar


def _log(msg: str, quiet: bool) -> None:
    if not quiet:
        print(msg, flush=True)