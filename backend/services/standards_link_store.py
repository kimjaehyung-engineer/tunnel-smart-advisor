from __future__ import annotations

import sqlite3
from pathlib import Path

from .history_store import connect, utc_now_iso
from .standards_evidence import normalize_standard_code


def init_standards_link_store(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        _ = connection.execute(
            """
            CREATE TABLE IF NOT EXISTS standards_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                standard_code TEXT NOT NULL,
                standard_name TEXT NOT NULL,
                clause_path TEXT NOT NULL,
                clause_label TEXT NOT NULL,
                clause_text TEXT NOT NULL,
                source_url TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                UNIQUE(target_type, target_id, standard_code, clause_path, clause_label)
            )
            """
        )
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_standards_links_target ON standards_links(target_type, target_id)")
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_standards_links_code ON standards_links(standard_code)")


def row_to_standards_link(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": int(row["id"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "target_type": str(row["target_type"]),
        "target_id": str(row["target_id"]),
        "standard_code": str(row["standard_code"]),
        "standard_name": str(row["standard_name"]),
        "clause_path": str(row["clause_path"]),
        "clause_label": str(row["clause_label"]),
        "clause_text": str(row["clause_text"]),
        "source_url": str(row["source_url"]),
        "note": str(row["note"]),
    }


def save_standards_link(
    target_type: str,
    target_id: str,
    standard_code: str,
    standard_name: str,
    clause_path: str,
    clause_label: str,
    clause_text: str,
    source_url: str,
    note: str = "",
    db_path: Path | None = None,
) -> dict[str, object]:
    init_standards_link_store(db_path)
    now = utc_now_iso()
    normalized_code = normalize_standard_code(standard_code)
    with connect(db_path) as connection:
        _ = connection.execute(
            """
            INSERT INTO standards_links (
                created_at, updated_at, target_type, target_id, standard_code,
                standard_name, clause_path, clause_label, clause_text, source_url, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(target_type, target_id, standard_code, clause_path, clause_label)
            DO UPDATE SET
                updated_at = excluded.updated_at,
                standard_name = excluded.standard_name,
                clause_text = excluded.clause_text,
                source_url = excluded.source_url,
                note = excluded.note
            """,
            (
                now,
                now,
                target_type,
                target_id,
                normalized_code,
                standard_name,
                clause_path,
                clause_label,
                clause_text,
                source_url,
                note,
            ),
        )
        row = connection.execute(
            """
            SELECT * FROM standards_links
            WHERE target_type = ? AND target_id = ? AND standard_code = ? AND clause_path = ? AND clause_label = ?
            """,
            (target_type, target_id, normalized_code, clause_path, clause_label),
        ).fetchone()
    if row is None:
        raise RuntimeError("Failed to persist standards link")
    return row_to_standards_link(row)


def list_standards_links(
    target_type: str = "",
    target_id: str = "",
    standard_code: str = "",
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict[str, object]]:
    init_standards_link_store(db_path)
    bounded_limit = max(1, min(limit, 200))
    clauses: list[str] = []
    params: list[str | int] = []
    if target_type:
        clauses.append("target_type = ?")
        params.append(target_type)
    if target_id:
        clauses.append("target_id = ?")
        params.append(target_id)
    if standard_code:
        clauses.append("standard_code = ?")
        params.append(normalize_standard_code(standard_code))
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(bounded_limit)
    with connect(db_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM standards_links {where_sql} ORDER BY updated_at DESC, id DESC LIMIT ?",
            params,
        ).fetchall()
    return [row_to_standards_link(row) for row in rows]
