from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_readiness_loads_csv_data() -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["data"]["risk"] > 0
    assert body["data"]["strategy"] > 0
    assert body["data"]["rels"] > 0
