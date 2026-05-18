from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_standards_evidence_returns_kcsc_seed_clauses() -> None:
    response = client.get("/standards/evidence", params={"query": "기준", "limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "KCSC Standards MCP seed evidence"
    assert body["items"]
    first = body["items"][0]
    assert first["code"].startswith(("KCS", "KDS"))
    assert first["source_url"].startswith("https://kcsc.re.kr/OpenApi/CodeViewer/")
    assert first["section_path"]
    assert first["text"]


def test_standards_evidence_filters_by_tunnel_waterproofing() -> None:
    response = client.get("/standards/evidence", params={"query": "방수", "limit": 10})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert any(item["code"] == "KCS 27 50 05" for item in items)


def test_standards_search_returns_unique_standard_summaries() -> None:
    response = client.get("/standards/search", params={"query": "방수"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert any(item["code"] == "KCS 27 50 05" and item["clause_count"] >= 1 for item in body["items"])


def test_standards_clauses_filters_by_code_and_query() -> None:
    response = client.get("/standards/clauses", params={"code": "KCS 27 50 05", "query": "방수"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["code"] == "KCS 27 50 05" for item in items)
    assert any("방수" in item["text"] or "방수" in item["name"] for item in items)


def test_standards_verify_validates_seeded_codes() -> None:
    valid_response = client.get("/standards/verify", params={"code": "KCS-27-50-05"})
    invalid_response = client.get("/standards/verify", params={"code": "KCS 00 00 00"})

    assert valid_response.status_code == 200
    assert valid_response.json()["is_valid"] is True
    assert valid_response.json()["code"] == "KCS 27 50 05"
    assert invalid_response.status_code == 200
    assert invalid_response.json()["is_valid"] is False


def test_standards_revalidate_checks_current_ontology_standard_nodes() -> None:
    response = client.post("/standards/revalidate")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "KCSC Standards MCP seed evidence"
    assert body["total"] >= 1
    assert body["candidate_count"] >= 1
    assert body["items"]
    assert {"id", "doc_name", "status", "verified_code", "candidate_codes", "message"}.issubset(body["items"][0].keys())


def test_standards_links_persist_risk_clause_reference() -> None:
    target_id = "risk:test-standard-link"
    payload = {
        "target_type": "risk",
        "target_id": target_id,
        "standard_code": "KCS-27-50-05",
        "clause_path": "3. 시공 > 3.3 시공기준",
        "clause_label": "(7)",
        "clause_text": "지수판 설치 기준",
        "note": "방수 리스크 검토 근거",
    }

    create_response = client.post("/standards/links", json=payload)
    list_response = client.get("/standards/links", params={"target_type": "risk", "target_id": target_id})

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["target_type"] == "risk"
    assert created["target_id"] == target_id
    assert created["standard_code"] == "KCS 27 50 05"
    assert created["standard_name"] == "터널 배수 및 방수 공사"
    assert created["source_url"].startswith("https://kcsc.re.kr/OpenApi/CodeViewer/")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert any(item["id"] == created["id"] for item in items)


def test_standards_links_reject_unknown_standard_code() -> None:
    response = client.post(
        "/standards/links",
        json={
            "target_type": "strategy",
            "target_id": "strategy:test-standard-link",
            "standard_code": "KCS 00 00 00",
            "clause_path": "1. 일반사항",
        },
    )

    assert response.status_code == 400
