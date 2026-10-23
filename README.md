# Альфа-Будущее: новостная аналитика для крупного бизнеса

Хакатон-проект: персонализированные бизнес-инсайты из новостей и аналитики Альфа-Банка.

## Структура

```
alfa-news/
├── config/sources.yaml      # источники новостей (RSS)
├── shared/                  # ОБЩИЙ КОНТРАКТ между модулями
│   ├── factors.py           #   словарь факторов (согласовать с командой!)
│   └── schemas.py           #   структуры данных (Event, Claim, Evidence...)
├── backend/
│   └── ingest/              # модуль 2: сбор и обработка новостей (этот модуль готов)
│   (profile/, ranking/, agent/, api/, llm/ — модули других участников)
├── data/                    # БД, аналитика банка, снимок новостей
└── tests/
```

## Запуск (Windows, PowerShell, из корня проекта)

```
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m backend.ingest run        # собрать новости и построить события
python -m backend.ingest stats
python -m backend.ingest show -n 10
pytest
```

Если PowerShell запрещает запуск скриптов:
`Set-ExecutionPolicy -Scope Process Bypass`

## Аналитика банка (RAG)

1. Скачать архив по ссылке со слайда 17 кейса, положить PDF в `data/bank_analytics/`.
2. `python -m backend.ingest kb-build`
3. `python -m backend.ingest kb-search "ключевая ставка"`

## Снимок новостей (воспроизводимость демо)

```
python -m backend.ingest export     # data/news_snapshot/news.jsonl
python -m backend.ingest import     # загрузить снимок без интернета
```

## Как другим модулям брать данные из ingest

```python
from backend.ingest import db
import json
conn = db.connect()
for r in conn.execute("SELECT * FROM events ORDER BY published_at DESC"):
    factors = json.loads(r["factors"])   # id из shared/factors.py
```

Таблицы: `news_items`, `events` (см. `backend/ingest/db.py`).

## Переменные окружения
См. `.env.example` (ключи LLM понадобятся позже).
