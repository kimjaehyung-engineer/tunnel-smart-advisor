from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from ..config import ONTOLOGY_VERSION_FILE, SOURCE_EXCEL_PATH


class OntologyVersion(TypedDict):
    source_file: str
    source_file_hash: str
    source_file_mtime: str
    ontology_build_at: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_ontology_version(source_path: Path = SOURCE_EXCEL_PATH) -> OntologyVersion:
    if source_path.exists():
        stat = source_path.stat()
        source_hash = file_sha256(source_path)
        source_mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        source_name = source_path.name
    else:
        source_hash = "missing"
        source_mtime = "missing"
        source_name = source_path.name
    return {
        "source_file": source_name,
        "source_file_hash": source_hash,
        "source_file_mtime": source_mtime,
        "ontology_build_at": datetime.now(timezone.utc).isoformat(),
    }


def write_ontology_version(version_path: Path = ONTOLOGY_VERSION_FILE, source_path: Path = SOURCE_EXCEL_PATH) -> OntologyVersion:
    version = build_ontology_version(source_path)
    version_path.parent.mkdir(parents=True, exist_ok=True)
    version_path.write_text(json.dumps(version, ensure_ascii=False, indent=2), encoding="utf-8")
    return version


def load_ontology_version(version_path: Path = ONTOLOGY_VERSION_FILE, source_path: Path = SOURCE_EXCEL_PATH) -> OntologyVersion:
    if version_path.exists():
        try:
            raw = json.loads(version_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                fallback = build_ontology_version(source_path)
                return {
                    "source_file": str(raw.get("source_file") or fallback["source_file"]),
                    "source_file_hash": str(raw.get("source_file_hash") or fallback["source_file_hash"]),
                    "source_file_mtime": str(raw.get("source_file_mtime") or fallback["source_file_mtime"]),
                    "ontology_build_at": str(raw.get("ontology_build_at") or fallback["ontology_build_at"]),
                }
        except (OSError, json.JSONDecodeError):
            pass
    return build_ontology_version(source_path)
