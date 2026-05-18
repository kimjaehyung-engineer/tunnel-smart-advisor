from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

from ..config import DB_PATH
from .history_store import utc_now_iso

NotificationFilter = Literal["all", "unread", "important"]


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_notification_store(db_path: Path | None = None, seed: bool = True) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_important INTEGER NOT NULL DEFAULT 0,
                is_archived INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(notifications)").fetchall()}
        if "is_archived" not in columns:
            connection.execute("ALTER TABLE notifications ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_flags ON notifications(is_read, is_important)")
        count = int(connection.execute("SELECT COUNT(*) FROM notifications").fetchone()[0])
        if seed and count == 0:
            create_notification(
                "system",
                "시스템 점검 알림",
                "알림 저장소가 초기화되었습니다. 운영 알림의 읽음/중요 상태가 저장됩니다.",
                is_important=True,
                db_path=db_path,
            )
            create_notification(
                "data",
                "데이터 갱신 알림",
                "온톨로지 CSV 변경 후 refresh_ontology.py와 cache reload 절차를 실행하세요.",
                db_path=db_path,
            )


def row_to_notification(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": int(row["id"]),
        "created_at": str(row["created_at"]),
        "category": str(row["category"]),
        "title": str(row["title"]),
        "message": str(row["message"]),
        "is_read": bool(row["is_read"]),
        "is_important": bool(row["is_important"]),
        "is_archived": bool(row["is_archived"]),
    }


def create_notification(
    category: str,
    title: str,
    message: str,
    is_important: bool = False,
    db_path: Path | None = None,
) -> dict[str, object]:
    init_notification_store(db_path, seed=False)
    created_at = utc_now_iso()
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO notifications (created_at, category, title, message, is_read, is_important)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (created_at, category, title, message, 1 if is_important else 0),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to persist notification")
        notification_id = int(cursor.lastrowid)
        row = connection.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
    return row_to_notification(row)


def list_notifications(filter_by: NotificationFilter = "all", db_path: Path | None = None) -> dict[str, object]:
    init_notification_store(db_path)
    where = " WHERE is_archived = 0"
    if filter_by == "unread":
        where = " WHERE is_archived = 0 AND is_read = 0"
    elif filter_by == "important":
        where = " WHERE is_archived = 0 AND is_important = 1"
    with connect(db_path) as connection:
        rows = connection.execute(f"SELECT * FROM notifications{where} ORDER BY created_at DESC LIMIT 100").fetchall()
        counts = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) AS unread,
                SUM(CASE WHEN is_important = 1 THEN 1 ELSE 0 END) AS important
            FROM notifications
            WHERE is_archived = 0
            """
        ).fetchone()
    return {
        "items": [row_to_notification(row) for row in rows],
        "summary": {
            "total": int(counts["total"] or 0),
            "unread": int(counts["unread"] or 0),
            "important": int(counts["important"] or 0),
        },
    }


def set_notification_read(notification_id: int, is_read: bool = True, db_path: Path | None = None) -> dict[str, object] | None:
    init_notification_store(db_path)
    with connect(db_path) as connection:
        connection.execute("UPDATE notifications SET is_read = ? WHERE id = ?", (1 if is_read else 0, notification_id))
        row = connection.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
    return row_to_notification(row) if row is not None else None


def archive_notification(notification_id: int, db_path: Path | None = None) -> dict[str, object] | None:
    init_notification_store(db_path)
    with connect(db_path) as connection:
        connection.execute("UPDATE notifications SET is_archived = 1 WHERE id = ?", (notification_id,))
        row = connection.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
    return row_to_notification(row) if row is not None else None


def set_notification_important(notification_id: int, is_important: bool, db_path: Path | None = None) -> dict[str, object] | None:
    init_notification_store(db_path)
    with connect(db_path) as connection:
        connection.execute("UPDATE notifications SET is_important = ? WHERE id = ?", (1 if is_important else 0, notification_id))
        row = connection.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
    return row_to_notification(row) if row is not None else None


def mark_all_read(db_path: Path | None = None) -> dict[str, object]:
    init_notification_store(db_path)
    with connect(db_path) as connection:
        connection.execute("UPDATE notifications SET is_read = 1 WHERE is_archived = 0")
    return list_notifications(db_path=db_path)
