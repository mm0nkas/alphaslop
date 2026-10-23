"""Сбор новостей из RSS: лента -> полный текст статьи -> SQLite."""
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import httpx
import trafilatura
import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


def load_config(path: str | Path | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_id(url: str) -> str:
    return hashlib.sha1(url.strip().encode("utf-8")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_date(entry) -> str:
    """Дата записи ленты -> ISO UTC. При ошибке берём текущее время."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
    return now_iso()


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_article_text(client: httpx.Client, url: str) -> str | None:
    """Полный текст статьи через trafilatura. None, если не получилось."""
    try:
        r = client.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        return trafilatura.extract(r.text, include_comments=False, include_tables=False)
    except Exception:
        return None


def collect_source(source: dict, conn: sqlite3.Connection, settings: dict,
                   client: httpx.Client) -> dict:
    """Собирает одну ленту. Ошибки отдельных статей не прерывают прогон."""
    stats = {"seen": 0, "new": 0, "skipped_short": 0, "errors": 0}
    # ленту качаем через httpx (свои сертификаты и таймаут), а разбирает feedparser
    try:
        resp = client.get(source["url"], timeout=20, follow_redirects=True)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        stats["errors"] += 1
        print(f"  [!] {source['name']}: лента не скачалась ({e})")
        return stats
    if not feed.entries:
        stats["errors"] += 1
        print(f"  [!] {source['name']}: в ленте нет записей (проверьте URL)")
        return stats

    min_chars = settings.get("min_text_chars", 200)
    for entry in feed.entries[: settings.get("per_source_limit", 50)]:
        stats["seen"] += 1
        url = entry.get("link")
        title = clean_text(entry.get("title", ""))
        if not url or not title:
            continue
        nid = make_id(url)
        if conn.execute("SELECT 1 FROM news_items WHERE id=?", (nid,)).fetchone():
            continue

        text = fetch_article_text(client, url)
        time.sleep(settings.get("delay_seconds", 1.0))
        complete = True
        if not text or len(text) < min_chars:
            # запасной вариант: анонс из ленты, помечаем как неполный
            text = clean_text(entry.get("summary", "") or entry.get("description", ""))
            complete = False
        text = clean_text(text)
        if len(text) < 40:
            stats["skipped_short"] += 1
            continue

        conn.execute(
            "INSERT INTO news_items(id,source,url,title,text,published_at,fetched_at,text_complete)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (nid, source["name"], url, title, text, parse_date(entry), now_iso(), int(complete)),
        )
        stats["new"] += 1
    conn.commit()
    return stats


def collect_all(conn: sqlite3.Connection, config: dict | None = None) -> dict:
    config = config or load_config()
    settings = config["settings"]
    total = {}
    with httpx.Client(headers={"User-Agent": settings["user_agent"]}) as client:
        for src in config["sources"]:
            print(f"-> {src['name']} ({src['url']})")
            try:
                total[src["name"]] = collect_source(src, conn, settings, client)
            except Exception as e:  # один источник не должен ронять остальные
                print(f"  [!] {src['name']}: {e}")
                total[src["name"]] = {"error": str(e)}
            print(f"  {total[src['name']]}")
    return total
