from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import data_loader, history_store, notification_store


client = TestClient(app)


def use_temp_db(monkeypatch, tmp_path: Path) -> Path:
    db_path = tmp_path / "runtime.sqlite3"
    monkeypatch.setattr(notification_store, "DB_PATH", db_path)
    monkeypatch.setattr(history_store, "DB_PATH", db_path)
    notification_store.init_notification_store()
    history_store.init_history_store()
    return db_path


def test_notifications_are_seeded_and_filterable(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    response = client.get("/notifications")
    unread_response = client.get("/notifications?filter=unread")
    important_response = client.get("/notifications?filter=important")

    assert response.status_code == 200
    assert response.json()["summary"]["total"] == 2
    assert unread_response.status_code == 200
    assert unread_response.json()["summary"]["unread"] == 2
    assert important_response.status_code == 200
    assert important_response.json()["summary"]["important"] == 1


def test_notification_read_and_important_state_persists(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)
    notification_id = client.get("/notifications").json()["items"][0]["id"]

    read_response = client.post(f"/notifications/{notification_id}/read")
    important_response = client.post(f"/notifications/{notification_id}/important", json={"is_important": True})

    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True
    assert important_response.status_code == 200
    assert important_response.json()["is_important"] is True


def test_mark_all_notifications_read(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    response = client.post("/notifications/read-all")

    assert response.status_code == 200
    assert response.json()["summary"]["unread"] == 0


def test_score_request_creates_analysis_notification(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    score_response = client.post("/score/", json={"query": "지하수"})

    assert score_response.status_code == 200
    notifications = client.get("/notifications").json()["items"]
    assert any(item["category"] == "analysis" and "분석 #" in item["message"] for item in notifications)


def test_high_risk_score_creates_important_notification(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    score_response = client.post("/score/", json={"query": "지하수"})

    assert score_response.status_code == 200
    notifications = client.get("/notifications").json()["items"]
    assert any(item["category"] == "risk" and item["is_important"] is True for item in notifications)


def test_report_share_creates_notification(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)
    history_id = client.post("/score/", json={"query": "지하수"}).json()["history_id"]

    share_response = client.post(f"/reports/{history_id}/share", json={"shared": True})

    assert share_response.status_code == 200
    notifications = client.get("/notifications").json()["items"]
    assert any(item["category"] == "report" and "공유" in item["title"] for item in notifications)


def test_cache_reload_creates_data_update_notification(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    reload_response = client.post("/admin/cache/reload")

    assert reload_response.status_code == 200
    assert reload_response.json()["status"] == "reloaded"
    notifications = client.get("/notifications").json()["items"]
    assert any(item["category"] == "data" and "캐시 갱신" in item["title"] for item in notifications)


def test_unhandled_request_error_creates_system_notification(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    def fail_load_data():
        raise RuntimeError("forced readiness failure")

    monkeypatch.setattr(data_loader, "load_data", fail_load_data)
    error_client = TestClient(app, raise_server_exceptions=False)

    response = error_client.get("/health/ready")

    assert response.status_code == 500
    notifications = client.get("/notifications").json()["items"]
    assert any(
        item["category"] == "system"
        and item["is_important"] is True
        and "시스템 오류" in item["title"]
        and "/health/ready" in item["message"]
        for item in notifications
    )


def test_notification_archive_hides_notification(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)
    notification_id = client.get("/notifications").json()["items"][0]["id"]

    archive_response = client.delete(f"/notifications/{notification_id}")
    list_response = client.get("/notifications")

    assert archive_response.status_code == 200
    assert archive_response.json()["is_archived"] is True
    assert all(item["id"] != notification_id for item in list_response.json()["items"])


def test_notification_mutations_return_404_for_unknown_id(monkeypatch, tmp_path: Path) -> None:
    use_temp_db(monkeypatch, tmp_path)

    read_response = client.post("/notifications/999999/read")
    important_response = client.post("/notifications/999999/important", json={"is_important": True})
    archive_response = client.delete("/notifications/999999")

    assert read_response.status_code == 404
    assert important_response.status_code == 404
    assert archive_response.status_code == 404
