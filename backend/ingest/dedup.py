"""Дедупликация: новости об одном и том же собираем в одно событие."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta

from rapidfuzz import fuzz

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def norm_title(title: str) -> str:
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", title.lower())).strip()


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def cluster_items(items: list[dict], threshold: int = 78, window_hours: int = 48) -> list[list[dict]]:
    """
    items: [{id, title, published_at, ...}]. Возвращает список групп (событий).
    Жадная кластеризация: новость присоединяется к первой группе, чей заголовок
    достаточно похож и вышел в пределах окна по времени.
    """
    ordered = sorted(items, key=lambda x: x["published_at"])
    groups: list[list[dict]] = []
    for it in ordered:
        nt = norm_title(it["title"])
        placed = False
        for g in groups:
            ref = g[0]
            if abs(_dt(it["published_at"]) - _dt(ref["published_at"])) > timedelta(hours=window_hours):
                continue
            score = fuzz.token_set_ratio(nt, norm_title(ref["title"]))
            if score >= threshold:
                g.append(it)
                placed = True
                break
        if not placed:
            groups.append([it])
    return groups


def event_id_for(group: list[dict]) -> str:
    key = "|".join(sorted(i["id"] for i in group))
    return "ev_" + hashlib.sha1(key.encode()).hexdigest()[:12]
