from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .history_store import connect, utc_now_iso
from .ontology_version import load_ontology_version


ALLOWED_ITEM_TYPES = {"risk", "strategy", "lesson", "project", "standard", "equipment", "method"}
ALLOWED_STATUSES = {"pending_review", "verified", "rejected"}


def init_knowledge_store(db_path: Path | None = None) -> None:
    with connect(db_path) as connection:
        _ = connection.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                source TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                data_version_json TEXT NOT NULL,
                reviewer TEXT NOT NULL DEFAULT '',
                review_note TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_submissions_type ON knowledge_submissions(item_type)")
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_submissions_status ON knowledge_submissions(verification_status)")
        _ = connection.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_submissions_updated ON knowledge_submissions(updated_at DESC)")


def row_to_knowledge_item(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": int(row["id"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "item_type": str(row["item_type"]),
        "title": str(row["title"]),
        "content": str(row["content"]),
        "tags": json.loads(str(row["tags_json"])),
        "source": str(row["source"]),
        "verification_status": str(row["verification_status"]),
        "data_version": json.loads(str(row["data_version_json"])),
        "reviewer": str(row["reviewer"]),
        "review_note": str(row["review_note"]),
    }


def normalize_tags(tags: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for tag in tags:
        value = tag.strip()
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized[:20]


def create_knowledge_submission(
    item_type: str,
    title: str,
    content: str,
    tags: list[str],
    source: str = "",
    db_path: Path | None = None,
) -> dict[str, object]:
    if item_type not in ALLOWED_ITEM_TYPES:
        raise ValueError("Unsupported knowledge item type")
    now = utc_now_iso()
    version = load_ontology_version()
    init_knowledge_store(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO knowledge_submissions (
                created_at, updated_at, item_type, title, content, tags_json,
                source, verification_status, data_version_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                now,
                item_type,
                title,
                content,
                json.dumps(normalize_tags(tags), ensure_ascii=False),
                source,
                "pending_review",
                json.dumps(version, ensure_ascii=False),
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to persist knowledge submission")
        row = connection.execute("SELECT * FROM knowledge_submissions WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
    if row is None:
        raise RuntimeError("Failed to load persisted knowledge submission")
    return row_to_knowledge_item(row)


def list_knowledge_submissions(
    item_type: str = "",
    verification_status: str = "",
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict[str, object]]:
    init_knowledge_store(db_path)
    bounded_limit = max(1, min(limit, 200))
    clauses: list[str] = []
    params: list[str | int] = []
    if item_type:
        clauses.append("item_type = ?")
        params.append(item_type)
    if verification_status:
        clauses.append("verification_status = ?")
        params.append(verification_status)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(bounded_limit)
    with connect(db_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM knowledge_submissions {where_sql} ORDER BY updated_at DESC, id DESC LIMIT ?",
            params,
        ).fetchall()
    return [row_to_knowledge_item(row) for row in rows]


def update_knowledge_status(
    submission_id: int,
    verification_status: str,
    reviewer: str = "",
    review_note: str = "",
    db_path: Path | None = None,
) -> dict[str, object] | None:
    if verification_status not in ALLOWED_STATUSES:
        raise ValueError("Unsupported verification status")
    init_knowledge_store(db_path)
    now = utc_now_iso()
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE knowledge_submissions
            SET updated_at = ?, verification_status = ?, reviewer = ?, review_note = ?
            WHERE id = ?
            """,
            (now, verification_status, reviewer, review_note, submission_id),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute("SELECT * FROM knowledge_submissions WHERE id = ?", (submission_id,)).fetchone()
    return row_to_knowledge_item(row) if row is not None else None
