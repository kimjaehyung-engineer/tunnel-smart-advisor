from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import DB_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_history_store(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                query TEXT NOT NULL,
                filters_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                top_risk TEXT NOT NULL,
                total_risks INTEGER NOT NULL,
                critical_count INTEGER NOT NULL,
                max_score REAL NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at ON analysis_history(created_at DESC)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_analysis_history_query ON analysis_history(query)")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS report_shares (
                history_id INTEGER PRIMARY KEY,
                shared INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def save_analysis(selection: dict[str, str | None], query: str, result: dict[str, Any], db_path: Path | None = None) -> dict[str, Any]:
    init_history_store(db_path)
    risks = result.get("risks", [])
    top_risk = ""
    if isinstance(risks, list) and risks:
        first_risk = risks[0]
        if isinstance(first_risk, dict):
            top_risk = str(first_risk.get("description", ""))
    created_at = utc_now_iso()
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO analysis_history (
                created_at, query, filters_json, result_json, top_risk,
                total_risks, critical_count, max_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                query,
                json.dumps(selection, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                top_risk,
                int(result.get("total_risks", 0)),
                int(result.get("critical_count", 0)),
                float(result.get("max_score", 0.0)),
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to persist analysis history")
        history_id = int(cursor.lastrowid)
    return {"id": history_id, "created_at": created_at}


def row_to_summary(row: sqlite3.Row) -> dict[str, Any]:
    result = json.loads(str(row["result_json"]))
    data_version = result.get("data_version", {}) if isinstance(result, dict) else {}
    model_version = result.get("model_version", "unknown") if isinstance(result, dict) else "unknown"
    return {
        "id": int(row["id"]),
        "created_at": str(row["created_at"]),
        "query": str(row["query"]),
        "filters": json.loads(str(row["filters_json"])),
        "top_risk": str(row["top_risk"]),
        "total_risks": int(row["total_risks"]),
        "critical_count": int(row["critical_count"]),
        "max_score": float(row["max_score"]),
        "data_version": data_version,
        "model_version": model_version,
    }


def list_analyses(
    query: str = "",
    limit: int = 50,
    project: str = "",
    date_from: str = "",
    date_to: str = "",
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    init_history_store(db_path)
    bounded_limit = max(1, min(limit, 100))
    clauses: list[str] = []
    params: list[str | int] = []
    if query:
        clauses.append("(query LIKE ? OR top_risk LIKE ? OR filters_json LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    if project:
        clauses.append("result_json LIKE ?")
        params.append(f"%{project}%")
    if date_from:
        clauses.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("created_at <= ?")
        params.append(date_to)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(bounded_limit)
    with connect(db_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM analysis_history{where} ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        ).fetchall()
    return [row_to_summary(row) for row in rows]


def get_analysis(history_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    init_history_store(db_path)
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM analysis_history WHERE id = ?", (history_id,)).fetchone()
    if row is None:
        return None
    summary = row_to_summary(row)
    summary["result"] = json.loads(str(row["result_json"]))
    return summary


def shared_report_ids(db_path: Path | None = None) -> set[int]:
    init_history_store(db_path)
    with connect(db_path) as connection:
        rows = connection.execute("SELECT history_id FROM report_shares WHERE shared = 1").fetchall()
    return {int(row["history_id"]) for row in rows}


def is_report_shared(history_id: int, db_path: Path | None = None) -> bool:
    init_history_store(db_path)
    with connect(db_path) as connection:
        row = connection.execute("SELECT shared FROM report_shares WHERE history_id = ?", (history_id,)).fetchone()
    return bool(row["shared"]) if row is not None else False


def set_report_shared(history_id: int, shared: bool, db_path: Path | None = None) -> dict[str, object]:
    init_history_store(db_path)
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO report_shares (history_id, shared)
            VALUES (?, ?)
            ON CONFLICT(history_id) DO UPDATE SET shared = excluded.shared
            """,
            (history_id, 1 if shared else 0),
        )
    return {"history_id": history_id, "shared": shared}
