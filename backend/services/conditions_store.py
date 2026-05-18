from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .history_store import connect, utc_now_iso


def init_conditions_store(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL,
                query TEXT NOT NULL,
                filters_json TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_saved_conditions_created_at ON saved_conditions(created_at DESC)")


def condition_title(filters: dict[str, str | None], query: str) -> str:
    parts = [value for value in filters.values() if value]
    if query.strip():
        parts.append(query.strip())
    return " / ".join(parts) if parts else "빈 분석 조건"


def row_to_condition(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "created_at": str(row["created_at"]),
        "title": str(row["title"]),
        "query": str(row["query"]),
        "filters": json.loads(str(row["filters_json"])),
    }


def save_condition(filters: dict[str, str | None], query: str, db_path: Path | None = None) -> dict[str, Any]:
    init_conditions_store(db_path)
    created_at = utc_now_iso()
    title = condition_title(filters, query)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO saved_conditions (created_at, title, query, filters_json)
            VALUES (?, ?, ?, ?)
            """,
            (created_at, title, query, json.dumps(filters, ensure_ascii=False)),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to persist saved condition")
        condition_id = int(cursor.lastrowid)
    return {
        "id": condition_id,
        "created_at": created_at,
        "title": title,
        "query": query,
        "filters": filters,
    }


def list_conditions(limit: int = 50, db_path: Path | None = None) -> list[dict[str, Any]]:
    init_conditions_store(db_path)
    bounded_limit = max(1, min(limit, 100))
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM saved_conditions ORDER BY created_at DESC LIMIT ?",
            (bounded_limit,),
        ).fetchall()
    return [row_to_condition(row) for row in rows]


def delete_condition(condition_id: int, db_path: Path | None = None) -> bool:
    init_conditions_store(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM saved_conditions WHERE id = ?", (condition_id,))
    return cursor.rowcount > 0
