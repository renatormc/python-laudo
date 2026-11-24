import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import closing, contextmanager
from pathlib import Path


_DB_NAME = "pics.sqlite"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS pics (
    filename TEXT PRIMARY KEY,
    caption TEXT NOT NULL DEFAULT '',
    original_size INTEGER NOT NULL DEFAULT 1,
    include INTEGER NOT NULL DEFAULT 1
)
"""
_UPSERT = """
INSERT INTO pics (filename, caption, original_size, include)
VALUES (?, ?, 1, 1)
ON CONFLICT(filename) DO UPDATE SET caption = excluded.caption
"""


def _db_path(folder: Path | None) -> Path:
    return (folder or Path.cwd()) / ".laudo" / _DB_NAME


@contextmanager
def _connect(folder: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = _db_path(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(path))) as conn:
        conn.execute(_SCHEMA)
        with conn:  # commits on success, rolls back on error
            yield conn


def get_captions(folder: Path | None = None) -> dict[str, str]:
    """Return every stored caption in a single query (refname -> caption)."""
    if not _db_path(folder).is_file():
        return {}
    with _connect(folder) as conn:
        return dict(conn.execute("SELECT filename, caption FROM pics"))


def get_caption(filename: str, folder: Path | None = None) -> str:
    with _connect(folder) as conn:
        row = conn.execute("SELECT caption FROM pics WHERE filename = ?", (filename,)).fetchone()
    return row[0] if row else ""


def set_captions(captions: Iterable[tuple[str, str]], folder: Path | None = None) -> None:
    """Upsert several (filename, caption) pairs in one transaction."""
    with _connect(folder) as conn:
        conn.executemany(_UPSERT, captions)


def set_caption(filename: str, caption: str, folder: Path | None = None) -> None:
    set_captions([(filename, caption)], folder)


def clear_caption(filename: str, folder: Path | None = None) -> None:
    set_caption(filename, "", folder)


def has_caption(filename: str, folder: Path | None = None) -> bool:
    return bool(get_caption(filename, folder))
