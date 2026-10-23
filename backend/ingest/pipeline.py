"""Обработка собранных новостей: дедупликация -> классификация -> события."""
from __future__ import annotations

import json
import sqlite3

from .dedup import cluster_items, event_id_for
from .facts import extract_key_facts
from .tagger import classify


def build_events(conn: sqlite3.Connection) -> int:
    """Пересобирает таблицу events из news_items. Возвращает число событий."""
    rows = [dict(r) for r in conn.execute("SELECT * FROM news_items")]
    groups = cluster_items(rows)

    conn.execute("DELETE FROM events")
    for g in groups:
        # главная новость группы: с полным текстом и самым длинным текстом
        main = max(g, key=lambda i: (i["text_complete"], len(i["text"])))
        topic, factors = classify(main["title"], main["text"])
        facts = extract_key_facts(main["title"], main["text"])
        eid = event_id_for(g)
        conn.execute(
            "INSERT INTO events(id,title,published_at,topic,factors,key_facts,source_urls)"
            " VALUES (?,?,?,?,?,?,?)",
            (
                eid,
                main["title"],
                min(i["published_at"] for i in g),
                topic,
                json.dumps(factors, ensure_ascii=False),
                json.dumps(facts, ensure_ascii=False),
                json.dumps([i["url"] for i in g], ensure_ascii=False),
            ),
        )
        conn.executemany("UPDATE news_items SET event_id=? WHERE id=?", [(eid, i["id"]) for i in g])
    conn.commit()
    return len(groups)


def export_jsonl(conn: sqlite3.Connection, path: str) -> int:
    """Снимок новостей для коммита в репозиторий (воспроизводимость демо)."""
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in conn.execute("SELECT * FROM news_items ORDER BY published_at"):
            f.write(json.dumps(dict(r), ensure_ascii=False) + "\n")
            n += 1
    return n


def import_jsonl(conn: sqlite3.Connection, path: str) -> int:
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            conn.execute(
                "INSERT OR IGNORE INTO news_items(id,source,url,title,text,published_at,fetched_at,text_complete)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (r["id"], r["source"], r["url"], r["title"], r["text"],
                 r["published_at"], r["fetched_at"], r.get("text_complete", 1)),
            )
            n += 1
    conn.commit()
    return n
