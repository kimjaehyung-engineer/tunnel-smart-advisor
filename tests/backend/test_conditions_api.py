from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import conditions_store
from backend.services import history_store


client = TestClient(app)


def use_temp_conditions_db(monkeypatch, tmp_path: Path) -> Path:
    db_path = tmp_path / "conditions.sqlite3"
    monkeypatch.setattr(history_store, "DB_PATH", db_path)
    conditions_store.init_conditions_store(db_path)
    return db_path


def test_saved_condition_can_be_created_and_listed(monkeypatch, tmp_path: Path) -> None:
    use_temp_conditions_db(monkeypatch, tmp_path)

    create_response = client.post("/conditions", json={"ground": "파쇄대", "method": "NATM", "impact": "침하", "query": "지하수"})

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "파쇄대 / NATM / 침하 / 지하수"
    assert created["filters"]["ground"] == "파쇄대"
    assert created["filters"]["impact"] == "침하"
    assert created["query"] == "지하수"

    list_response = client.get("/conditions")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == created["id"]


def test_saved_condition_can_be_deleted(monkeypatch, tmp_path: Path) -> None:
    use_temp_conditions_db(monkeypatch, tmp_path)
    created = client.post("/conditions", json={"query": "굴착"}).json()

    delete_response = client.delete(f"/conditions/{created['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"id": created["id"], "deleted": True}
    assert client.get("/conditions").json()["items"] == []


def test_delete_unknown_saved_condition_returns_404(monkeypatch, tmp_path: Path) -> None:
    use_temp_conditions_db(monkeypatch, tmp_path)

    response = client.delete("/conditions/999999")

    assert response.status_code == 404
