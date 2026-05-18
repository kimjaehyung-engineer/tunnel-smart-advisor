from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_admin_knowledge_submission_stores_status_and_data_version() -> None:
    response = client.post(
        "/admin/knowledge/items",
        json={
            "item_type": "lesson",
            "title": "도심지 지하수 유입 사례",
            "content": "NATM 굴착 중 지하수 유입이 증가하면 선배수와 보강 패턴을 함께 검토한다.",
            "tags": ["지하수", "NATM", "지하수"],
            "source": "운영자 수기 등록",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["item_type"] == "lesson"
    assert body["verification_status"] == "pending_review"
    assert body["tags"] == ["지하수", "NATM"]
    assert body["data_version"]["source_file"]
    assert body["data_version"]["source_file_hash"]

    list_response = client.get("/admin/knowledge/items", params={"item_type": "lesson", "verification_status": "pending_review"})
    assert list_response.status_code == 200
    assert any(item["id"] == body["id"] for item in list_response.json()["items"])


def test_admin_knowledge_submission_status_update() -> None:
    create_response = client.post(
        "/admin/knowledge/items",
        json={
            "item_type": "standard",
            "title": "KCS 방수 기준 보강 메모",
            "content": "터널 방수 공사 조항 검토 메모",
        },
    )
    submission_id = create_response.json()["id"]

    update_response = client.post(
        f"/admin/knowledge/items/{submission_id}/status",
        json={"verification_status": "verified", "reviewer": "admin", "review_note": "근거 확인"},
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["verification_status"] == "verified"
    assert body["reviewer"] == "admin"
    assert body["review_note"] == "근거 확인"


def test_admin_knowledge_rejects_unknown_type() -> None:
    response = client.post(
        "/admin/knowledge/items",
        json={"item_type": "sensor", "title": "센서", "content": "범위 제외"},
    )

    assert response.status_code == 422
