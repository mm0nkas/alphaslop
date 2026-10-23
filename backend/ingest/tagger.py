"""
Классификация новостей БЕЗ LLM (правила по ключевым словам).

Интерфейс classify() потом заменим реализацией на Gemma с тем же выходом;
правила останутся запасным вариантом и baseline для сравнения качества.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.factors import FACTORS, TOPICS  # noqa: E402


def classify(title: str, text: str) -> tuple[str, list[str]]:
    """Возвращает (topic, factors). Заголовок весит втрое больше начала текста."""
    head = title.lower()
    body = text[:3000].lower()
    scores: dict[str, int] = {}
    for fid, spec in FACTORS.items():
        score = 0
        for kw in spec["keywords"]:
            score += 3 * head.count(kw) + body.count(kw)
        if score >= 2 or any(kw in head for kw in spec["keywords"]):
            scores[fid] = score
    factors = sorted(scores, key=scores.get, reverse=True)

    topic = "other"
    best = 0
    for t, fids in TOPICS.items():
        s = sum(scores.get(f, 0) for f in fids)
        if s > best:
            topic, best = t, s
    return topic, factors
