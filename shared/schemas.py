"""
Общие структуры данных (контракт между модулями).
Намеренно на стандартной библиотеке (dataclasses), без внешних зависимостей.
Позже можно заменить на pydantic без изменения полей.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

# Происхождение утверждения — требование критериев 03 и 12
Origin = Literal["confirmed", "alfa_analytics", "ai_inference"]
EvidenceKind = Literal["company_feature", "news", "bank_analytics"]


@dataclass
class NewsItem:
    id: str                    # sha1(url)[:16]
    source: str                # cbr / interfax / rbc / kommersant
    url: str
    title: str
    text: str
    published_at: str          # ISO 8601, UTC
    fetched_at: str
    text_complete: bool = True  # False, если удалось получить только анонс


@dataclass
class Event:
    """Событие = одна или несколько новостей об одном и том же."""
    id: str
    title: str
    published_at: str
    topic: str                       # ключ из TOPICS или "other"
    factors: list[str]               # id из FACTORS
    key_facts: list[str]             # короткие факты без LLM (числа, даты, первые предложения)
    item_ids: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    kind: EvidenceKind
    ref: str                   # поле профиля / URL / "документ, стр. N"
    quote: str = ""


@dataclass
class Claim:
    text: str
    origin: Origin
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class KBChunk:
    """Фрагмент аналитики банка для RAG."""
    id: str
    doc: str
    page: int
    text: str


def to_dict(obj) -> dict:
    return asdict(obj)
