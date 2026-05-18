from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.data_loader import data_row_counts, load_data


REQUIRED_DATASETS = (
    "equipment",
    "ground",
    "location",
    "method",
    "process",
    "rels",
    "risk",
    "strategy",
)


def smoke_load() -> dict[str, int]:
    data = load_data()
    counts = data_row_counts(data)
    missing = [name for name in REQUIRED_DATASETS if counts.get(name, 0) <= 0]
    if missing:
        raise ValueError(f"Required datasets are missing or empty: {', '.join(missing)}")
    return counts


def main() -> int:
    try:
        counts = smoke_load()
    except Exception as exc:
        print(f"Data load smoke failed: {exc}", file=sys.stderr)
        return 1

    print("Data load smoke passed")
    for name in REQUIRED_DATASETS:
        print(f"{name}: {counts[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
