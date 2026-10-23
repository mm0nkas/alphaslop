# scripts/demo.py
import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data/news.db")

def main():
    if not DB_PATH.exists():
        print("❌ База данных data/news.db не найдена. Запустите сбор новостей.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Ищем новость, у которой есть и теги, и банковский контекст
    cursor = conn.execute("""
        SELECT title, source, factors, bank_insights 
        FROM news_items 
        WHERE factors IS NOT NULL AND factors != '[]' AND bank_insights IS NOT NULL
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("❌ Не найдено подходящих новостей для демо.")
        print("💡 Попробуйте запустить полный пайплайн: python main.py all")
        return

    print("=" * 80)
    print("🚀 ДЕМОНСТРАЦИЯ РАБОТЫ СИСТЕМЫ АНАЛИТИКИ")
    print("=" * 80)
    
    print(f"\n📰 ВНЕШНЯЯ НОВОСТЬ:")
    print(f"   Заголовок: {row['title']}")
    print(f"   Источник:  {row['source'].upper()}")
    
    factors = json.loads(row['factors'])
    print(f"   🏷️  Определенные факторы: {', '.join(factors)}")
    
    print(f"\n🏦 КОНТЕКСТ И ПОЗИЦИЯ АЛЬФА-БАНКА:")
    insights = json.loads(row['bank_insights'])
    
    for i, insight in enumerate(insights[:2], 1): # Показываем топ-2 совпадения
        print(f"\n   🔹 Совпадение #{i} (Релевантность: {insight['score']:.2f})")
        print(f"      Документ: {insight['doc']}")
        # Очищаем вывод от артефактов OCR для красоты демо
        clean_text = insight['text'].replace("--- Страница", "\n      [Страница").strip()
        print(f"      Цитата: \"{clean_text}...\"")
        
    print("\n" + "=" * 80)
    print("✅ Система успешно связала внешнее событие с внутренней экспертизой банка!")
    print("=" * 80)

if __name__ == "__main__":
    main()