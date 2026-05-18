from __future__ import annotations

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SRC = ROOT / "frontend" / "src"


def main() -> int:
    violations: list[Path] = []
    for path in FRONTEND_SRC.rglob("*"):
        if path.is_dir() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?:from|import)\s+['\"](?:\.\.?/)*mocks?/", text):
            violations.append(path.relative_to(ROOT))

    if violations:
        print("Mock references found outside frontend/src/mocks:", file=sys.stderr)
        for path in violations:
            print(f"- {path}", file=sys.stderr)
        return 1

    print("No production mock references found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
