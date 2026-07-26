"""Persistent scan history backed by SQLite.

Stores every scan result with a timestamp so the dashboard can show
trend data and the API can serve ``GET /history``.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

LOGGER = logging.getLogger(__name__)

_DB_PATH = os.getenv("SCAN_HISTORY_DB", "scan_history.db")
_MAX_ROWS = int(os.getenv("SCAN_HISTORY_MAX_ROWS", "5000"))

_local = threading.local()
_initialized = False


def _ensure_db() -> None:
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def init_db() -> None:
    global _initialized
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            endpoint    TEXT    NOT NULL,
            state       TEXT    NOT NULL,
            state_label TEXT    NOT NULL,
            evidence    TEXT    NOT NULL,
            recommendations TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scan_history_endpoint ON scan_history(endpoint)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scan_history_timestamp ON scan_history(timestamp)"
    )
    conn.commit()
    _initialized = True
    LOGGER.info("Scan history database initialized at %s", _DB_PATH)


def store_scan(result: dict[str, Any]) -> None:
    _ensure_db()
    conn = _conn()
    conn.execute(
        """
        INSERT INTO scan_history (timestamp, endpoint, state, state_label, evidence, recommendations)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            result.get("endpoint", ""),
            result.get("state", ""),
            result.get("state_label", ""),
            json.dumps(result.get("evidence", {}), default=str),
            json.dumps(result.get("recommendations", []), default=str),
        ),
    )
    conn.commit()
    _trim_old()


def _trim_old() -> None:
    conn = _conn()
    count = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]
    if count > _MAX_ROWS:
        conn.execute(
            """
            DELETE FROM scan_history WHERE id IN (
                SELECT id FROM scan_history ORDER BY id ASC LIMIT ?
            )
            """,
            (count - _MAX_ROWS,),
        )
        conn.commit()


def get_history(
    limit: int = 100,
    endpoint: str | None = None,
) -> list[dict[str, Any]]:
    _ensure_db()
    conn = _conn()
    if endpoint:
        rows = conn.execute(
            "SELECT * FROM scan_history WHERE endpoint = ? ORDER BY id DESC LIMIT ?",
            (endpoint, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scan_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_history_stats() -> dict[str, Any]:
    _ensure_db()
    conn = _conn()
    total = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]
    endpoints = conn.execute(
        "SELECT DISTINCT endpoint FROM scan_history"
    ).fetchall()
    latest = conn.execute(
        "SELECT timestamp FROM scan_history ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return {
        "total_scans": total,
        "tracked_endpoints": [r[0] for r in endpoints],
        "latest_scan": latest[0] if latest else None,
    }


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "endpoint": row["endpoint"],
        "state": row["state"],
        "state_label": row["state_label"],
        "evidence": json.loads(row["evidence"]),
        "recommendations": json.loads(row["recommendations"]),
    }
