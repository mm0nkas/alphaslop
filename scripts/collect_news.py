# collect_news.py
import sqlite3
import hashlib
import time
import feedparser
import httpx
import trafilatura
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# --- Конфигурация ---
DB_PATH = Path("data/news.db")
DB_PATH.parent.mkdir(exist_ok=True)

SOURCES = [
    {"name": "cbr", "url": "http://www.cbr.ru/rss/press_release.asp"},
    {"name": "interfax", "url": "https://www.interfax.ru/rss.asp"},
    {"name": "rbc", "url": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"},
    {"name": "kommersant", "url": "https://www.kommersant.ru/RSS/news.xml"},
]

HEADERS = {"User-Agent": "Alfa-Hackathon-Bot/1.0 (academic research)"}

# --- Вспомогательные функции ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_items (
            id TEXT PRIMARY KEY,
            source TEXT,
            url TEXT UNIQUE,
            title TEXT,
            text TEXT,
            published_at TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()
    return conn

def make_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16]

def parse_date(entry) -> str:
    raw = entry.get("published") or entry.get("updated")
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def fetch_full_text(url: str) -> str:
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        return trafilatura.extract(resp.text, include_comments=False, include_tables=False) or ""
    except Exception:
        return ""

# --- Основной цикл ---
def main():
    print("🚀 Запуск сбора новостей...\n")
    conn = init_db()
    total_new = 0

    for source in SOURCES:
        print(f"📡 Источник: {source['name']} ({source['url']})")
        try:
            feed = feedparser.parse(source["url"], request_headers=HEADERS)
            count = 0
            
            for entry in feed.entries[:30]: # Берём последние 30 новостей из ленты
                if not entry.get("link"):
                    continue
                    
                nid = make_id(entry.link)
                
                # Проверка на дубликаты
                if conn.execute("SELECT 1 FROM news_items WHERE id=?", (nid,)).fetchone():
                    continue
                
                print(f"   ⬇️  {entry.title[:60]}...")
                
                # Скачиваем полный текст
                text = fetch_full_text(entry.link)
                if len(text) < 100:
                    text = entry.get("summary", "") # Фоллбэк на анонс
                
                conn.execute(
                    "INSERT INTO news_items(id, source, url, title, text, published_at, fetched_at) VALUES (?,?,?,?,?,?,?)",
                    (nid, source["name"], entry.link, entry.title.strip(), text, parse_date(entry), datetime.now(timezone.utc).isoformat())
                )
                count += 1
                time.sleep(1.5) # Вежливая пауза, чтобы не заблокировали
                
            print(f"   ✅ Добавлено: {count}\n")
            total_new += count
            
        except Exception as e:
            print(f"   ❌ Ошибка источника: {e}\n")

    conn.commit()
    conn.close()
    print(f" Сбор завершён! Всего новых статей: {total_new}")
    print(f"📁 База данных сохранена в: {DB_PATH}")

if __name__ == "__main__":
    main()