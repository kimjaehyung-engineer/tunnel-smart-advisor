from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import history_store


client = TestClient(app)


def test_dashboard_summary_includes_operational_status(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "dashboard.sqlite3"
    monkeypatch.setattr(history_store, "DB_PATH", db_path)
    history_store.init_history_store()

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    status_items = body["operationalStatus"]
    labels = {item["label"] for item in status_items}
    assert {
        "총 리스크 수",
        "최상위 위험 수",
        "데이터 최신성",
        "최근 데이터 업데이트",
        "시스템 오류 상태",
        "리포트 공유 현황",
    }.issubset(labels)
    assert all({"label", "value", "status", "description", "color"}.issubset(item.keys()) for item in status_items)
