from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import DATA_DIR, LESSON_RELS_FILE, NODE_FILES, ONTOLOGY_VERSION_FILE, RELS_FILE


REQUIRED_COLUMNS: dict[str, set[str]] = {
    "ground": {"id:ID", "condition_name", ":LABEL"},
    "method": {"id:ID", "method_name", ":LABEL"},
    "equipment": {"id:ID", "equip_name", ":LABEL"},
    "risk": {"id:ID", "description", "source_project", "source_version", "cause", "impact", "likelihood", "impact_score", "frequency", "recency", "confidence", "expert_weight", ":LABEL"},
    "strategy": {"id:ID", "action", "source_project", "target_risk", "expected_effect", "required_equipment", "related_standard", "responsible_role", ":LABEL"},
    "project": {"id:ID", "name", ":LABEL"},
    "lesson": {"id:ID", "content", ":LABEL"},
    "rels": {":START_ID", ":END_ID", ":TYPE"},
}

CONTENT_COLUMNS = {
    "risk": "description",
    "strategy": "action",
    "lesson": "content",
}

REQUIRED_VALUE_COLUMNS = {
    "risk": ("source_project", "source_version"),
    "strategy": ("source_project", "target_risk", "expected_effect"),
}

NUMERIC_COLUMNS = {
    "risk": ("likelihood", "impact_score", "frequency", "recency", "confidence", "expert_weight"),
}
NUMERIC_RANGES = {
    "risk": {
        "likelihood": (1.0, 5.0),
        "impact_score": (1.0, 5.0),
        "frequency": (0.0, None),
        "recency": (0.0, None),
        "confidence": (0.0, 1.0),
        "expert_weight": (0.0, None),
    },
}

REQUIRED_VERSION_FIELDS = {"source_file", "source_file_hash", "source_file_mtime", "ontology_build_at"}
ALLOWED_RELATION_TYPES = {
    "AFFECTS",
    "APPLIED_STRATEGY",
    "ASSIGNED_TO",
    "ASSOCIATED_WITH",
    "BASED_ON",
    "CHARACTERIZED_BY",
    "ENCOUNTERS",
    "HAS_RISK_CASE",
    "MITIGATED_BY",
    "OCCURS_AT",
    "REQUIRES",
    "TRIGGER",
    "USES",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ValueError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def assert_required_columns(name: str, frame: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS[name] - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {', '.join(sorted(missing))}")


def assert_unique_ids(name: str, frame: pd.DataFrame) -> None:
    if "id:ID" not in frame.columns:
        return
    duplicated = frame[frame["id:ID"].duplicated()]["id:ID"].astype(str).tolist()
    if duplicated:
        preview = ", ".join(duplicated[:5])
        raise ValueError(f"{name} has duplicate id:ID values: {preview}")


def assert_non_empty_content(name: str, frame: pd.DataFrame) -> None:
    content_column = CONTENT_COLUMNS.get(name)
    if not content_column:
        return
    blank_count = frame[content_column].isna().sum() + (frame[content_column].astype(str).str.strip() == "").sum()
    if int(blank_count) > 0:
        raise ValueError(f"{name}.{content_column} has {int(blank_count)} blank values")


def assert_required_values(name: str, frame: pd.DataFrame) -> None:
    for column in REQUIRED_VALUE_COLUMNS.get(name, ()):
        blank_count = frame[column].isna().sum() + (frame[column].astype(str).str.strip() == "").sum() + (frame[column].astype(str).str.strip() == "missing").sum()
        if int(blank_count) > 0:
            raise ValueError(f"{name}.{column} has {int(blank_count)} blank or missing values")


def assert_numeric_columns(name: str, frame: pd.DataFrame) -> None:
    for column in NUMERIC_COLUMNS.get(name, ()):
        numeric_values = pd.Series(pd.to_numeric(frame[column], errors="coerce"))
        invalid_count = int(numeric_values.isna().sum())
        if invalid_count > 0:
            raise ValueError(f"{name}.{column} has {invalid_count} non-numeric values")
        min_value, max_value = NUMERIC_RANGES.get(name, {}).get(column, (None, None))
        if min_value is not None:
            below_count = int((numeric_values < min_value).sum())
            if below_count > 0:
                raise ValueError(f"{name}.{column} has {below_count} values below {min_value}")
        if max_value is not None:
            above_count = int((numeric_values > max_value).sum())
            if above_count > 0:
                raise ValueError(f"{name}.{column} has {above_count} values above {max_value}")


def assert_ontology_version_metadata(version_path: Path = ONTOLOGY_VERSION_FILE) -> None:
    if not version_path.exists():
        raise ValueError(f"Missing ontology version metadata: {version_path}")
    try:
        raw = json.loads(version_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid ontology version metadata JSON: {version_path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Ontology version metadata must be a JSON object")
    missing = REQUIRED_VERSION_FIELDS - set(raw)
    if missing:
        raise ValueError(f"Ontology version metadata is missing fields: {', '.join(sorted(missing))}")
    blank_fields = [field for field in sorted(REQUIRED_VERSION_FIELDS) if not str(raw.get(field) or "").strip() or str(raw.get(field)) == "missing"]
    if blank_fields:
        raise ValueError(f"Ontology version metadata has blank or missing values: {', '.join(blank_fields)}")
    source_hash = str(raw["source_file_hash"])
    if len(source_hash) != 64 or any(character not in "0123456789abcdefABCDEF" for character in source_hash):
        raise ValueError("Ontology version source_file_hash must be a 64-character SHA-256 hex digest")


def assert_allowed_relation_types(rels: pd.DataFrame) -> None:
    relation_types = set(rels[":TYPE"].dropna().astype(str).tolist())
    unknown_types = sorted(relation_types - ALLOWED_RELATION_TYPES)
    if unknown_types:
        raise ValueError(f"Relationships contain unsupported :TYPE values: {', '.join(unknown_types[:10])}")


def assert_strategy_targets_exist(strategies: pd.DataFrame, risks: pd.DataFrame) -> None:
    risk_ids = set(risks["id:ID"].dropna().astype(str).tolist())
    target_ids = set(strategies["target_risk"].dropna().astype(str).tolist())
    missing_targets = sorted(target_ids - risk_ids)
    if missing_targets:
        raise ValueError(f"Strategy target_risk values reference unknown risks: {', '.join(missing_targets[:10])}")


def risk_id_aliases(risks: pd.DataFrame) -> set[str]:
    aliases: set[str] = set()
    for risk_id in risks["id:ID"].dropna().astype(str).tolist():
        aliases.add(risk_id)
        if risk_id.startswith("Risk_"):
            suffix = risk_id.removeprefix("Risk_")
            if suffix.isdigit():
                aliases.add(f"Risk_{int(suffix)}")
                aliases.add(f"Risk_{int(suffix):03d}")
    return aliases


def assert_lesson_relations_valid(lesson_rels: pd.DataFrame, lessons: pd.DataFrame, risks: pd.DataFrame) -> None:
    learned_rows = lesson_rels[lesson_rels[":TYPE"] == "LEARNED_AS"]
    if learned_rows.empty:
        raise ValueError("Lesson relationship seed has no LEARNED_AS rows")
    known_risks = risk_id_aliases(risks)
    known_lessons = set(lessons["id:ID"].dropna().astype(str).tolist())
    learned_start_ids = pd.Series(learned_rows[":START_ID"])
    missing_risks = sorted(set(learned_start_ids.dropna().astype(str).tolist()) - known_risks)
    if missing_risks:
        raise ValueError(f"LEARNED_AS relationships reference unknown risks: {', '.join(missing_risks[:10])}")
    learned_end_ids = pd.Series(learned_rows[":END_ID"])
    missing_lessons = sorted(set(learned_end_ids.dropna().astype(str).tolist()) - known_lessons)
    if missing_lessons:
        raise ValueError(f"LEARNED_AS relationships reference unknown lessons: {', '.join(missing_lessons[:10])}")


def validate() -> dict[str, int]:
    assert_ontology_version_metadata()
    frames: dict[str, pd.DataFrame] = {}
    for name, path in NODE_FILES.items():
        frames[name] = read_csv(path)
    frames["rels"] = read_csv(RELS_FILE)
    frames["lesson_rels"] = read_csv(LESSON_RELS_FILE)

    for name, frame in frames.items():
        if name in REQUIRED_COLUMNS:
            assert_required_columns(name, frame)
        assert_unique_ids(name, frame)
        assert_non_empty_content(name, frame)
        assert_required_values(name, frame)
        assert_numeric_columns(name, frame)

    node_ids = set()
    for name, frame in frames.items():
        if name in {"rels", "lesson_rels"} or "id:ID" not in frame.columns:
            continue
        node_ids.update(frame["id:ID"].dropna().astype(str).tolist())

    for path in DATA_DIR.glob("nodes_*.csv"):
        frame = read_csv(path)
        if "id:ID" in frame.columns:
            node_ids.update(frame["id:ID"].dropna().astype(str).tolist())

    rels = frames["rels"]
    assert_strategy_targets_exist(frames["strategy"], frames["risk"])
    assert_lesson_relations_valid(frames["lesson_rels"], frames["lesson"], frames["risk"])
    assert_allowed_relation_types(rels)
    referenced_ids = set(rels[":START_ID"].dropna().astype(str).tolist()) | set(rels[":END_ID"].dropna().astype(str).tolist())
    missing_references = sorted(referenced_ids - node_ids)
    if missing_references:
        preview = ", ".join(missing_references[:10])
        raise ValueError(f"Relationships reference unknown node ids: {preview}")

    return {name: len(frame) for name, frame in frames.items()}


def main() -> int:
    try:
        counts = validate()
    except ValueError as exc:
        print(f"Ontology validation failed: {exc}", file=sys.stderr)
        return 1

    print("Ontology validation passed")
    for name, count in sorted(counts.items()):
        print(f"{name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
