from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .history_store import connect, utc_now_iso
from .ontology_version import load_ontology_version


def init_comparison_report_store(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        _ = connection.execute(
            """
            CREATE TABLE IF NOT EXISTS comparison_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                before_json TEXT NOT NULL,
                after_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                title TEXT NOT NULL,
                data_version_json TEXT NOT NULL,
                model_version TEXT NOT NULL
            )
            """
        )
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_comparison_reports_created_at ON comparison_reports(created_at DESC)")
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_comparison_reports_title ON comparison_reports(title)")


def row_to_comparison_report(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "created_at": str(row["created_at"]),
        "before": json.loads(str(row["before_json"])),
        "after": json.loads(str(row["after_json"])),
        "result": json.loads(str(row["result_json"])),
        "title": str(row["title"]),
        "data_version": json.loads(str(row["data_version_json"])),
        "model_version": str(row["model_version"]),
    }


def save_comparison_report(
    before: dict[str, object],
    after: dict[str, object],
    result: dict[str, object],
    db_path: Path | None = None,
) -> dict[str, Any]:
    init_comparison_report_store(db_path)
    created_at = utc_now_iso()
    data_version = load_ontology_version()
    model_version = str(result.get("model_version") or "unknown")
    title = f"설계변경 비교 리포트 - {created_at[:10]}"
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO comparison_reports (
                created_at, before_json, after_json, result_json, title,
                data_version_json, model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                json.dumps(before, ensure_ascii=False),
                json.dumps(after, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                title,
                json.dumps(data_version, ensure_ascii=False),
                model_version,
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to persist comparison report")
        row = connection.execute("SELECT * FROM comparison_reports WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
    if row is None:
        raise RuntimeError("Failed to load persisted comparison report")
    return row_to_comparison_report(row)


def get_comparison_report(report_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    init_comparison_report_store(db_path)
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM comparison_reports WHERE id = ?", (report_id,)).fetchone()
    return row_to_comparison_report(row) if row is not None else None


def list_comparison_reports(query: str = "", limit: int = 50, db_path: Path | None = None) -> list[dict[str, Any]]:
    init_comparison_report_store(db_path)
    bounded_limit = max(1, min(limit, 100))
    params: list[str | int] = []
    where_sql = ""
    if query.strip():
        where_sql = "WHERE title LIKE ? OR before_json LIKE ? OR after_json LIKE ? OR result_json LIKE ?"
        params.extend([f"%{query.strip()}%"] * 4)
    params.append(bounded_limit)
    with connect(db_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM comparison_reports {where_sql} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [row_to_comparison_report(row) for row in rows]
