"""SQLite-backed OCR history store: every run's date, file, engine,
confidence, timing and output path, plus aggregate statistics for the
Home dashboard and full-text/regex search for the History page.
"""
from __future__ import annotations

import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from app.config.constants import DEFAULT_CONFIG_DIR_NAME, DEFAULT_DATABASE_FILENAME
from app.core.models import HistoryRecord

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    date TEXT NOT NULL,
    engine TEXT NOT NULL,
    language TEXT,
    confidence REAL,
    processing_time REAL,
    output_path TEXT,
    status TEXT,
    page_count INTEGER DEFAULT 1,
    extracted_text TEXT
);
CREATE INDEX IF NOT EXISTS idx_history_date ON history(date);
CREATE INDEX IF NOT EXISTS idx_history_file_name ON history(file_name);
"""


def _regexp(pattern: str, value: str) -> bool:
    """SQLite REGEXP callback. Case sensitivity is controlled by the caller
    via an inline ``(?i)`` prefix on ``pattern`` (see :meth:`DBManager.search`).
    """
    if value is None:
        return False
    try:
        return re.search(pattern, value) is not None
    except re.error:
        return False


class DBManager:
    """Wraps a single SQLite connection with WAL mode for concurrent
    batch-writer / UI-reader access.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (Path.home() / DEFAULT_CONFIG_DIR_NAME / DEFAULT_DATABASE_FILENAME)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.create_function("REGEXP", 2, _regexp)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # -- writes ------------------------------------------------------------------
    def insert_record(self, record: HistoryRecord, extracted_text: str = "") -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO history
                   (file_name, file_path, date, engine, language, confidence,
                    processing_time, output_path, status, page_count, extracted_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.file_name,
                    record.file_path,
                    record.date,
                    record.engine,
                    record.language,
                    record.confidence,
                    record.processing_time,
                    record.output_path,
                    record.status,
                    record.page_count,
                    extracted_text,
                ),
            )
            return int(cursor.lastrowid)

    def delete_record(self, record_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (record_id,))

    def clear_all(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM history")

    # -- reads -------------------------------------------------------------------
    def get_recent(self, limit: int = 20) -> list[HistoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def search(
        self,
        query: str = "",
        use_regex: bool = False,
        case_sensitive: bool = False,
        whole_word: bool = False,
        engine: Optional[str] = None,
        limit: int = 200,
    ) -> list[HistoryRecord]:
        clauses: list[str] = []
        params: list = []

        if query:
            pattern = query if use_regex else re.escape(query)
            if whole_word:
                pattern = rf"\b{pattern}\b"
            if not case_sensitive:
                pattern = f"(?i){pattern}"
            clauses.append("(extracted_text REGEXP ? OR file_name REGEXP ?)")
            params.extend([pattern, pattern])

        if engine:
            clauses.append("engine = ?")
            params.append(engine)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM history {where} ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_record(r) for r in rows]

    def get_statistics(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            avg_conf = conn.execute("SELECT AVG(confidence) FROM history").fetchone()[0] or 0.0
            total_pages = conn.execute("SELECT SUM(page_count) FROM history").fetchone()[0] or 0
            by_engine = conn.execute(
                "SELECT engine, COUNT(*) as cnt FROM history GROUP BY engine"
            ).fetchall()
            avg_time = conn.execute("SELECT AVG(processing_time) FROM history").fetchone()[0] or 0.0
        return {
            "total_processed": total,
            "average_confidence": round(avg_conf, 1),
            "total_pages": total_pages,
            "average_processing_time": round(avg_time, 2),
            "by_engine": {row["engine"]: row["cnt"] for row in by_engine},
        }

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> HistoryRecord:
        return HistoryRecord(
            id=row["id"],
            file_name=row["file_name"],
            file_path=row["file_path"],
            date=row["date"],
            engine=row["engine"],
            language=row["language"],
            confidence=row["confidence"],
            processing_time=row["processing_time"],
            output_path=row["output_path"],
            status=row["status"],
            page_count=row["page_count"],
        )

    @staticmethod
    def now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


_db_instance: DBManager | None = None


def get_db() -> DBManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DBManager()
    return _db_instance
