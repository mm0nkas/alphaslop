"""Выделение ключевых фактов без LLM: первые предложения, числа, проценты, даты."""
from __future__ import annotations

import re

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[А-ЯA-Z«\"])")
_NUMBER = re.compile(
    r"\d[\d\s ]*(?:[.,]\d+)?\s?(?:%|проц\w*|млрд|млн|тыс\.?|трлн|руб\w*|долл\w*|евро|юан\w*|п\.п\.|базисн\w+ пункт\w*)",
    re.IGNORECASE,
)
_DATE = re.compile(
    r"\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)(?:\s\d{4})?",
    re.IGNORECASE,
)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text.replace("\n", " ")) if s.strip()]


def extract_key_facts(title: str, text: str, max_facts: int = 5) -> list[str]:
    """Первые 2 предложения + предложения с числами/датами (без дублей)."""
    sentences = split_sentences(text)
    facts: list[str] = []

    def add(s: str):
        s = s.strip()
        if 20 <= len(s) <= 400 and s not in facts and s.lower() != title.lower():
            facts.append(s)

    for s in sentences[:2]:
        add(s)
    for s in sentences[2:]:
        if len(facts) >= max_facts:
            break
        if _NUMBER.search(s) or _DATE.search(s):
            add(s)
    return facts[:max_facts]


def extract_numbers(text: str) -> list[str]:
    return [m.group(0).strip() for m in _NUMBER.finditer(text)][:10]
