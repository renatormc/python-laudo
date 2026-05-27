import sqlite3
from pathlib import Path


_DB_NAME = "pics.sqlite"


def _laudo_dir() -> Path:
    return Path.cwd() / ".laudo"


def _db_path() -> Path:
    return _laudo_dir() / _DB_NAME


def _ensure_db() -> sqlite3.Connection:
    laudo = _laudo_dir()
    laudo.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_db_path()))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pics (
            filename TEXT PRIMARY KEY,
            caption TEXT NOT NULL DEFAULT '',
            original_size INTEGER NOT NULL DEFAULT 1,
            include INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.commit()
    return conn


def get_caption(filename: str) -> str:
    conn = _ensure_db()
    try:
        row = conn.execute(
            "SELECT caption FROM pics WHERE filename = ?", (filename,)
        ).fetchone()
        return row[0] if row else ""
    finally:
        conn.close()


def set_caption(filename: str, caption: str) -> None:
    conn = _ensure_db()
    try:
        conn.execute(
            """
            INSERT INTO pics (filename, caption, original_size, include)
            VALUES (?, ?, 1, 1)
            ON CONFLICT(filename) DO UPDATE SET caption = excluded.caption
            """,
            (filename, caption),
        )
        conn.commit()
    finally:
        conn.close()


def clear_caption(filename: str) -> None:
    set_caption(filename, "")


def has_caption(filename: str) -> bool:
    return bool(get_caption(filename))
