import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.ingest import db  # noqa: E402
from backend.ingest.bank_kb import BankKB, build_index, chunk_text  # noqa: E402
from backend.ingest.dedup import cluster_items  # noqa: E402
from backend.ingest.facts import extract_key_facts  # noqa: E402
from backend.ingest.pipeline import build_events  # noqa: E402
from backend.ingest.tagger import classify  # noqa: E402

RATE_TITLE = "Банк России сохранил ключевую ставку на уровне 14% годовых"
RATE_TEXT = (
    "Совет директоров Банка России принял решение сохранить ключевую ставку на уровне 14% годовых. "
    "Это первая пауза после серии снижений ставки. "
    "Регулятор ухудшил прогноз по инфляции на 2026 год и сообщил, что 11 сентября состоится заседание."
)


def test_classify_key_rate():
    topic, factors = classify(RATE_TITLE, RATE_TEXT)
    assert topic == "monetary_policy"
    assert "key_rate" in factors


def test_classify_irrelevant_is_other():
    topic, factors = classify("Футболисты выиграли матч", "Команда одержала победу со счётом 2:0.")
    assert topic == "other" and factors == []


def test_facts_contain_numbers_and_dates():
    facts = extract_key_facts(RATE_TITLE, RATE_TEXT)
    assert facts and any("14%" in f for f in facts)
    assert any("11 сентября" in f for f in facts)


def test_dedup_groups_same_event():
    items = [
        {"id": "a", "title": RATE_TITLE, "published_at": "2026-09-11T10:00:00+00:00"},
        {"id": "b", "title": "ЦБ сохранил ключевую ставку на уровне 14% годовых", "published_at": "2026-09-11T10:30:00+00:00"},
        {"id": "c", "title": "Курс юаня вырос на торгах", "published_at": "2026-09-11T11:00:00+00:00"},
    ]
    groups = cluster_items(items)
    sizes = sorted(len(g) for g in groups)
    assert sizes == [1, 2]


def test_build_events_end_to_end(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    for i, (src, title) in enumerate([("rbc", RATE_TITLE), ("interfax", "ЦБ сохранил ключевую ставку на уровне 14% годовых")]):
        conn.execute(
            "INSERT INTO news_items VALUES (?,?,?,?,?,?,?,?,NULL)",
            (f"id{i}", src, f"http://x/{i}", title, RATE_TEXT, f"2026-09-11T1{i}:00:00+00:00", "2026-10-21T00:00:00+00:00", 1),
        )
    conn.commit()
    assert build_events(conn) == 1
    ev = conn.execute("SELECT * FROM events").fetchone()
    assert "key_rate" in json.loads(ev["factors"])
    assert len(json.loads(ev["source_urls"])) == 2


def test_bm25_search(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "rate.txt").write_text("Ключевая ставка Банка России сохранена на уровне 14%, риторика стала жестче.", encoding="utf-8")
    (folder / "gold.txt").write_text("Цена золота обновила максимум на фоне геополитики.", encoding="utf-8")
    idx = tmp_path / "idx.json"
    assert build_index(folder, idx) == 2
    hits = BankKB(idx).search("ключевая ставка")
    assert hits and hits[0]["doc"] == "rate" and hits[0]["origin"] == "alfa_analytics"


def test_chunk_text_overlap():
    words = " ".join(str(i) for i in range(500))
    chunks = chunk_text(words, max_words=200, overlap=20)
    assert len(chunks) >= 3 and chunks[1].split()[0] == "180"
