from __future__ import annotations

from app.core.models import HistoryRecord
from app.database.db_manager import DBManager


def _make_record(**overrides) -> HistoryRecord:
    base = dict(
        id=None,
        file_name="invoice.png",
        file_path="/tmp/invoice.png",
        date="2026-08-01 10:00:00",
        engine="tesseract",
        language="en",
        confidence=91.5,
        processing_time=1.23,
        output_path="/tmp/invoice.txt",
        status="done",
        page_count=1,
    )
    base.update(overrides)
    return HistoryRecord(**base)


def test_insert_and_get_recent(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    record_id = db.insert_record(_make_record(), extracted_text="INVOICE total $668.52")
    assert record_id > 0

    recent = db.get_recent(limit=5)
    assert len(recent) == 1
    assert recent[0].file_name == "invoice.png"


def test_search_by_extracted_text(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    db.insert_record(_make_record(file_name="a.png"), extracted_text="apple banana cherry")
    db.insert_record(_make_record(file_name="b.png"), extracted_text="date elderberry fig")

    results = db.search(query="banana")
    assert len(results) == 1
    assert results[0].file_name == "a.png"


def test_search_case_sensitivity(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    db.insert_record(_make_record(file_name="a.png"), extracted_text="Hello World")

    assert len(db.search(query="hello", case_sensitive=False)) == 1
    assert len(db.search(query="hello", case_sensitive=True)) == 0
    assert len(db.search(query="Hello", case_sensitive=True)) == 1


def test_search_regex(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    db.insert_record(_make_record(file_name="a.png"), extracted_text="invoice number 12345")

    results = db.search(query=r"\d{5}", use_regex=True)
    assert len(results) == 1


def test_search_filters_by_engine(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    db.insert_record(_make_record(file_name="a.png", engine="tesseract"), extracted_text="hi")
    db.insert_record(_make_record(file_name="b.png", engine="easyocr"), extracted_text="hi")

    results = db.search(engine="easyocr")
    assert len(results) == 1
    assert results[0].file_name == "b.png"


def test_delete_record(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    record_id = db.insert_record(_make_record())
    db.delete_record(record_id)
    assert db.get_recent() == []


def test_get_statistics(tmp_path):
    db = DBManager(db_path=tmp_path / "history.db")
    db.insert_record(_make_record(confidence=80.0, page_count=2))
    db.insert_record(_make_record(confidence=90.0, page_count=3))

    stats = db.get_statistics()
    assert stats["total_processed"] == 2
    assert stats["average_confidence"] == 85.0
    assert stats["total_pages"] == 5
