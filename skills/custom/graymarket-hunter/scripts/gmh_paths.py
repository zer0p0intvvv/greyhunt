import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def data_dir() -> Path:
    d = os.environ.get("GMH_DATA_DIR", "").strip()
    p = Path(d) if d else _HERE / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def out_dir() -> Path:
    d = os.environ.get("GMH_OUT_DIR", "").strip()
    p = Path(d) if d else _HERE / "output"
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_glob() -> str:
    return os.environ.get("GMH_DATA_GLOB", "*.json").strip() or "*.json"
