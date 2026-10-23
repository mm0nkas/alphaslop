# link_to_bank.py
import sqlite3
import json
from pathlib import Path
from backend.ingest.bank_kb import BankKB

DB_PATH = Path("data/news.db")
INDEX_PATH = Path("data/kb_index.json")

def link_news_to_bank():
    print("🔗 Связывание новостей с аналитикой банка...\n")
    
    if not INDEX_PATH.exists():
        print("❌ Файл data/kb_index.json не найден!")
        print("   Сначала дождитесь завершения init_kb.py (OCR для PDF)")
        return
    
    print("📚 Загрузка индекса аналитики банка...")
    kb = BankKB()
    print("✅ Индекс загружен\n")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Добавляем колонку для связей, если её нет
    try:
        conn.execute("ALTER TABLE news_items ADD COLUMN bank_insights TEXT")
        conn.commit()
    except Exception:
        pass  # Колонка уже существует
    
    # Берём только те новости, у которых есть теги
    cursor = conn.execute("SELECT id, title, factors FROM news_items WHERE factors IS NOT NULL AND factors != '[]'")
    rows = cursor.fetchall()
    
    print(f"📰 Новостей с тегами для связывания: {len(rows)}\n")
    
    linked = 0
    for row in rows:
        factors = json.loads(row["factors"])
                # Умное расширение запроса: добавляем финансовые ключевые слова на основе тегов
        factor_boost = {
            "key_rate": "ключевая ставка денежно-кредитная политика ЦБ",
            "fx": "валютный курс рубль доллар юань",
            "inflation": "инфляция цены ипц рост стоимости",
            "commodities": "нефть газ золото металлы сырье",
            "regulation": "регулирование закон налоги пошлины",
            "sanctions": "санкции ограничения экспорт импорт",
            "consumption": "потребление спрос розница зарплаты"
        }
        
        # Собираем усиленный запрос
        boost_words = " ".join([factor_boost.get(f, "") for f in factors])
        query = f"{row['title']} {boost_words}"
        
        # Ищем топ-3 релевантных чанка в документах банка
        results = kb.search(query, top_k=3)
        
        if results:
            insights = [
                {
                    "text": res.get("text", "")[:300],
                    "score": round(res.get("score", 0), 3),
                    "doc": res.get("doc", "unknown")
                }
                for res in results
            ]
            
            conn.execute(
                "UPDATE news_items SET bank_insights = ? WHERE id = ?",
                (json.dumps(insights, ensure_ascii=False), row["id"])
            )
            linked += 1
            
            print(f"📰 {row['title'][:60]}...")
            print(f"   Теги: {factors}")
            print(f"   Топ-1 от банка: {results[0].get('text', '')[:80]}...\n")
    
    conn.commit()
    conn.close()
    print(f"✅ Связывание завершено! {linked} новостей получили контекст банка.")

if __name__ == "__main__":
    link_news_to_bank()