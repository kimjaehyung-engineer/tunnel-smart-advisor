from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "tunnel_checklist"


def run_step(name: str, command: list[str], *, required: bool = True) -> bool:
    print(f"\n==> {name}")
    print(" ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode == 0:
        return True
    if required:
        raise SystemExit(result.returncode)
    print(f"Skipped failure for optional step: {name}", file=sys.stderr)
    return False


def smoke_ready(url: str) -> None:
    print(f"\n==> API readiness smoke: {url}")
    with urllib.request.urlopen(url, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("status") != "ready":
        raise SystemExit(f"Readiness smoke failed: {body}")
    print(json.dumps(body, ensure_ascii=False, indent=2))


def reload_backend_cache(url: str) -> None:
    print(f"\n==> Backend cache reload: {url}")
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("status") != "reloaded":
        raise SystemExit(f"Cache reload failed: {body}")
    print(json.dumps(body, ensure_ascii=False, indent=2))


def print_csv_diff() -> None:
    print("\n==> CSV diff summary")
    result = subprocess.run(
        ["git", "diff", "--stat", "--", str(DATA_DIR.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.stdout.strip():
        print(result.stdout)
    else:
        print("No CSV changes detected.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the tunnel ontology refresh quality gate.")
    parser.add_argument("--skip-build", action="store_true", help="Skip ontology rebuild and validate existing CSVs only.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip API readiness smoke test.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip backend pytest step.")
    parser.add_argument("--smoke-url", default="http://127.0.0.1:8080/health/ready")
    parser.add_argument("--reload-url", default="http://127.0.0.1:8080/admin/cache/reload")
    args = parser.parse_args()

    if not args.skip_build:
        run_step("Ontology build", [sys.executable, "scripts/ontology/build_master_ontology.py"])
    run_step("Schema validation", [sys.executable, "scripts/tools/validate_ontology.py"])
    if not args.skip_tests:
        run_step("Backend tests", [sys.executable, "-m", "pytest", "tests/backend", "-q"])
    if not args.skip_smoke:
        smoke_ready(args.smoke_url)
    reload_backend_cache(args.reload_url)
    print_csv_diff()
    print("\nOntology refresh procedure completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
