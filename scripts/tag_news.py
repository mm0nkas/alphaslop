# tag_news.py
import sqlite3
import json
#import yaml
from pathlib import Path

DB_PATH = Path("data/news.db")
FACTORS_PATH = Path("shared/factors.py")  # или config/factors.yaml

# Загружаем факторы (адаптируйте под вашу структуру)
def load_factors():
    # yaml_path = Path("config/factors.yaml")
    # if yaml_path.exists():
    #     with open(yaml_path, "r", encoding="utf-8") as f:
    #         return yaml.safe_load(f)["factors"]
    
    try:
        from shared.factors import load_factors as lf
        return lf()
    except:
        return {
            "key_rate": ["ключевая ставка", "ставк", "денежно-кредитн", "цб рф"],
            "fx": ["курс", "рубл", "доллар", "юан", "валют"],
            "inflation": ["инфляц", "цен", "ипц"],
            "commodities": ["нефт", "газ", "золот", "металл"],
            "regulation": ["закон", "налог", "пошлин"],
            "sanctions": ["санкц", "ограничен"],
            "consumption": ["потреблен", "розниц", "спрос"],
        }

def tag_news():
    print("️  Запуск тегирования новостей...\n")
    
    factors = load_factors()
    print(f"📋 Загружено факторов: {len(factors)}")
    for f_name, keywords in factors.items():
        print(f"   - {f_name}: {len(keywords)} ключевых слов")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Добавляем колонку для тегов, если её нет
    try:
        conn.execute("ALTER TABLE news_items ADD COLUMN factors TEXT")
        conn.commit()
    except:
        pass  # Колонка уже есть
    
    # Берём все новости
    cursor = conn.execute("SELECT id, title, text FROM news_items")
    rows = cursor.fetchall()
    
    print(f"\n📰 Всего новостей: {len(rows)}")
    
    updated = 0
    for row in rows:
        # Объединяем заголовок и начало текста для анализа
        content = (row["title"] + " " + (row["text"] or "")[:2000]).lower()
        
        # Ищем совпадения с факторами
        found_factors = []
        for factor_name, keywords in factors.items():
            if any(kw in content for kw in keywords):
                found_factors.append(factor_name)
        
        # Сохраняем теги
        if found_factors:
            conn.execute(
                "UPDATE news_items SET factors = ? WHERE id = ?",
                (json.dumps(found_factors, ensure_ascii=False), row["id"])
            )
            updated += 1
            print(f"   ✅ {row['title'][:50]}... → {found_factors}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Тегирование завершено! Обновлено {updated} из {len(rows)} новостей")

if __name__ == "__main__":
    tag_news()