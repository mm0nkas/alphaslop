"""SQLite-хранилище для ingest."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "news.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS news_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    text_complete INTEGER NOT NULL DEFAULT 1,
    event_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_items(published_at);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    published_at TEXT NOT NULL,
    topic TEXT NOT NULL,
    factors TEXT NOT NULL,      -- JSON-список factor_id
    key_facts TEXT NOT NULL,    -- JSON-список строк
    source_urls TEXT NOT NULL   -- JSON-список URL
);
"""


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else DEFAULT_DB
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
