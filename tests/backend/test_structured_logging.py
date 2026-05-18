import logging

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_request_id_header_is_reused_from_request() -> None:
    response = client.get("/health", headers={"X-Request-ID": "req-test-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-test-1"


def test_request_id_header_is_generated_when_missing() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_score_endpoint_logs_request_summary(caplog) -> None:
    caplog.set_level(logging.INFO, logger="tunnel.score")

    response = client.post("/score/", json={}, headers={"X-Request-ID": "score-log-test"})

    assert response.status_code == 200
    matching_records = [
        record
        for record in caplog.records
        if getattr(record, "event", "") == "score_request"
    ]
    assert matching_records
    record = matching_records[-1]
    assert record.request_id == "score-log-test"
    assert record.result_count == 0
    assert record.filters == {
        "process": None,
        "ground": None,
        "location": None,
        "method": None,
        "equipment": None,
        "impact": None,
    }
    assert record.latency_ms >= 0
