from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import history_store
from backend.services.risk_scoring import MODEL_VERSION


client = TestClient(app)


def use_temp_history_db(monkeypatch, tmp_path: Path) -> Path:
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr(history_store, "DB_PATH", db_path)
    history_store.init_history_store()
    return db_path


def test_score_request_is_saved_to_history(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.post("/score/", json={"query": "지하수"})

    assert response.status_code == 200
    body = response.json()
    assert "history_id" in body

    history_response = client.get("/history/analyses")
    assert history_response.status_code == 200
    items = history_response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == body["history_id"]
    assert items[0]["query"] == "지하수"
    assert items[0]["model_version"] == MODEL_VERSION


def test_history_detail_returns_full_result_snapshot(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    score_response = client.post("/score/", json={"query": "파쇄대"})
    history_id = score_response.json()["history_id"]

    response = client.get(f"/history/analyses/{history_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == history_id
    assert body["query"] == "파쇄대"
    assert "result" in body
    assert body["result"]["total_risks"] >= 0
    assert body["model_version"] == MODEL_VERSION
    assert body["result"]["model_version"] == MODEL_VERSION


def test_history_list_filters_by_query(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    client.post("/score/", json={"query": "지하수"})
    client.post("/score/", json={"query": "장비"})

    response = client.get("/history/analyses?query=지하수")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["query"] == "지하수"


def test_history_list_filters_by_project_and_date(monkeypatch, tmp_path: Path) -> None:
    db_path = use_temp_history_db(monkeypatch, tmp_path)
    result = {
        "total_risks": 1,
        "critical_count": 0,
        "max_score": 3.0,
        "risks": [{"description": "Alpha 위험", "project": "Alpha Project"}],
        "graph": {"nodes": [], "edges": []},
    }
    monkeypatch.setattr(history_store, "utc_now_iso", lambda: "2026-05-10T00:00:00+00:00")
    history_store.save_analysis({"process": None, "ground": "파쇄대"}, "alpha", result, db_path=db_path)
    monkeypatch.setattr(history_store, "utc_now_iso", lambda: "2026-05-15T00:00:00+00:00")
    history_store.save_analysis({"process": None, "ground": "풍화암"}, "beta", result | {"risks": [{"description": "Beta 위험", "project": "Beta Project"}]}, db_path=db_path)

    response = client.get("/history/analyses?project=Beta%20Project&date_from=2026-05-14T00:00:00+00:00")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["query"] == "beta"


def test_history_detail_returns_404_for_unknown_id(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.get("/history/analyses/999999")

    assert response.status_code == 404


def test_history_rerun_reexecutes_saved_request(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)
    original_response = client.post("/score/", json={"ground": "파쇄대", "query": "지하수"})
    original_id = original_response.json()["history_id"]

    rerun_response = client.post(f"/history/analyses/{original_id}/rerun")

    assert rerun_response.status_code == 200
    body = rerun_response.json()
    assert body["history_id"] != original_id
    assert "total_risks" in body

    history_response = client.get("/history/analyses")
    assert history_response.status_code == 200
    assert len(history_response.json()["items"]) == 2


def test_history_rerun_returns_404_for_unknown_id(monkeypatch, tmp_path: Path) -> None:
    use_temp_history_db(monkeypatch, tmp_path)

    response = client.post("/history/analyses/999999/rerun")

    assert response.status_code == 404
