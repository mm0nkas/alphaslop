"""CLI: python -m backend.ingest <команда>"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import db
from .bank_kb import BankKB, build_index
from .collector import collect_all
from .pipeline import build_events, export_jsonl, import_jsonl

SNAPSHOT = Path(__file__).resolve().parents[2] / "data" / "news_snapshot" / "news.jsonl"


def cmd_stats(conn):
    n_items = conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0]
    n_ev = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"новостей: {n_items}, событий: {n_ev}")
    for r in conn.execute("SELECT source, COUNT(*) c, SUM(text_complete) n_full FROM news_items GROUP BY source"):
        print(f"  {r['source']:<12} {r['c']:>5}  (полный текст: {r['n_full']})")
    print("топ тем:")
    for r in conn.execute("SELECT topic, COUNT(*) c FROM events GROUP BY topic ORDER BY c DESC"):
        print(f"  {r['topic']:<20} {r['c']}")


def cmd_show(conn, limit):
    for r in conn.execute("SELECT * FROM events ORDER BY published_at DESC LIMIT ?", (limit,)):
        print(f"\n[{r['topic']}] {r['title']}")
        print(f"  факторы: {json.loads(r['factors'])}")
        for f in json.loads(r["key_facts"])[:2]:
            print(f"  • {f[:160]}")
        print(f"  источники: {len(json.loads(r['source_urls']))}")


def main():
    p = argparse.ArgumentParser(prog="ingest")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collect", help="скачать новости из RSS")
    sub.add_parser("process", help="дедупликация + классификация -> события")
    sub.add_parser("run", help="collect + process")
    sub.add_parser("stats", help="статистика по базе")
    sh = sub.add_parser("show", help="показать последние события")
    sh.add_argument("-n", type=int, default=10)
    sub.add_parser("export", help="выгрузить снимок новостей в data/news_snapshot/news.jsonl")
    sub.add_parser("import", help="загрузить снимок (демо без интернета)")
    sub.add_parser("kb-build", help="построить индекс по PDF в data/bank_analytics/")
    kq = sub.add_parser("kb-search", help="поиск по аналитике банка")
    kq.add_argument("query")
    args = p.parse_args()

    if args.cmd == "kb-build":
        print(f"чанков: {build_index()}")
        return
    if args.cmd == "kb-search":
        for h in BankKB().search(args.query):
            print(f"[{h['doc']}, стр. {h['page']}, score {h['score']}] {h['text'][:200]}...")
        return

    conn = db.connect()
    if args.cmd in ("collect", "run"):
        collect_all(conn)
    if args.cmd in ("process", "run"):
        print(f"событий: {build_events(conn)}")
    if args.cmd == "stats":
        cmd_stats(conn)
    if args.cmd == "show":
        cmd_show(conn, args.n)
    if args.cmd == "export":
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        print(f"выгружено: {export_jsonl(conn, str(SNAPSHOT))}")
    if args.cmd == "import":
        print(f"загружено: {import_jsonl(conn, str(SNAPSHOT))}")
        print(f"событий: {build_events(conn)}")


if __name__ == "__main__":
    main()
