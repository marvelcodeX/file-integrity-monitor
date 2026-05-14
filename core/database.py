"""
core/database.py
SQLite-backed baseline snapshot storage.
Stores file paths and their trusted SHA-256 hashes.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "baseline.db")


def _get_connection() -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure the schema exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS baseline (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            directory   TEXT    NOT NULL,
            filepath    TEXT    NOT NULL,
            hash        TEXT    NOT NULL,
            recorded_at TEXT    NOT NULL,
            UNIQUE(directory, filepath)
        )
    """)
    conn.commit()


# ── Public API ────────────────────────────────────────────────────────────────

def save_baseline(directory: str, file_hashes: dict[str, str]) -> None:
    """
    Persist a full baseline snapshot for the given directory.
    Replaces any previous baseline for the same directory.
    """
    now = datetime.now().isoformat(timespec="seconds")
    conn = _get_connection()
    try:
        # Remove old entries for this directory first
        conn.execute("DELETE FROM baseline WHERE directory = ?", (directory,))
        conn.executemany(
            "INSERT INTO baseline (directory, filepath, hash, recorded_at) VALUES (?, ?, ?, ?)",
            [(directory, path, digest, now) for path, digest in file_hashes.items()],
        )
        conn.commit()
    finally:
        conn.close()


def load_baseline(directory: str) -> dict[str, str]:
    """
    Return the stored baseline for a directory as {relative_path: hash}.
    Returns an empty dict if no baseline exists.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT filepath, hash FROM baseline WHERE directory = ?", (directory,)
        ).fetchall()
        return {row["filepath"]: row["hash"] for row in rows}
    finally:
        conn.close()


def baseline_exists(directory: str) -> bool:
    """Return True if a baseline has been saved for this directory."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM baseline WHERE directory = ? LIMIT 1", (directory,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def clear_baseline(directory: str) -> None:
    """Delete the baseline for a specific directory."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM baseline WHERE directory = ?", (directory,))
        conn.commit()
    finally:
        conn.close()


def get_baseline_info(directory: str) -> dict:
    """Return metadata about the stored baseline (count, timestamp)."""
    conn = _get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) as file_count, MAX(recorded_at) as last_updated
            FROM baseline WHERE directory = ?
            """,
            (directory,),
        ).fetchone()
        return {
            "file_count": row["file_count"] if row else 0,
            "last_updated": row["last_updated"] if row else None,
        }
    finally:
        conn.close()