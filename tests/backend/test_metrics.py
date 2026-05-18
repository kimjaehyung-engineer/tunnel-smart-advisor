from fastapi.testclient import TestClient

from backend.main import app
from backend.services.metrics import metrics


client = TestClient(app)


def test_metrics_endpoint_reports_request_counts() -> None:
    metrics.reset()

    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    body = metrics_response.json()
    assert body["request_count"] >= 1
    assert body["error_count"] == 0
    assert body["request_latency_ms"]["count"] >= 1


def test_score_request_records_score_latency() -> None:
    metrics.reset()

    response = client.post("/score/", json={})

    assert response.status_code == 200
    body = client.get("/metrics").json()
    assert body["score_latency_ms"]["count"] == 1
    assert body["score_latency_ms"]["p95"] >= 0
