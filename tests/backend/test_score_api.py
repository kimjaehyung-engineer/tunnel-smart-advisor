from fastapi.testclient import TestClient

from backend.main import app
from backend.services.data_loader import load_data
from backend.services.risk_scoring import MODEL_VERSION


client = TestClient(app)


def test_score_empty_request_returns_expected_shape() -> None:
    response = client.post("/score/", json={})

    assert response.status_code == 200
    body = response.json()
    history_id = body.pop("history_id")
    data_version = body.pop("data_version")
    assert isinstance(history_id, int)
    assert data_version["source_file"]
    assert data_version["source_file_hash"]
    assert body.pop("model_version") == MODEL_VERSION
    assert body.pop("banding_model_version") == "p1_gap_bands_v1"
    assert body.pop("banding_method") == "gap_analysis"
    assert body.pop("band_boundaries") == []
    assert body.pop("band_fallback_reason") == "empty_scores"
    assert body.pop("recommendations") == []
    assert body == {
        "total_risks": 0,
        "critical_count": 0,
        "max_score": 0.0,
        "risks": [],
        "graph": {"nodes": [], "edges": []},
    }


def test_score_normal_request_returns_risks() -> None:
    data = load_data()
    trigger = data["rels"][data["rels"][":TYPE"] == "TRIGGER"].iloc[0]
    ground_name = data["ground"].loc[data["ground"]["id:ID"] == trigger[":START_ID"], "condition_name"].iloc[0]

    response = client.post("/score/", json={"ground": str(ground_name), "query": ""})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["history_id"], int)
    assert body["data_version"]["source_file"]
    assert body["total_risks"] > 0
    assert body["risks"]
    assert body["model_version"] == MODEL_VERSION
    first_risk = body["risks"][0]
    assert "likelihood" in first_risk
    assert "impact_score" in first_risk
    assert "confidence" in first_risk
    assert first_risk["score_explanation"]["model_version"] == MODEL_VERSION
    assert first_risk["score_explanation"]["rationale"]
    assert first_risk["score_explanation"]["source_evidence"]["source_version"]
    assert first_risk["source_evidence"]["source_version"]
    assert "standards" in first_risk
    assert "roles" in first_risk
    assert first_risk["cluster_band"].startswith("B")
    assert first_risk["cluster_label"]
    assert body["banding_model_version"] == "p1_gap_bands_v1"
    assert set(body["graph"].keys()) == {"nodes", "edges"}


def test_score_accepts_impact_filter() -> None:
    data = load_data()
    affects = data["rels"][data["rels"][":TYPE"] == "AFFECTS"].iloc[0]
    impact_name = data["impact"].loc[data["impact"]["id:ID"] == affects[":END_ID"], "impact_type"].iloc[0]

    response = client.post("/score/", json={"impact": str(impact_name)})

    assert response.status_code == 200
    body = response.json()
    assert body["total_risks"] > 0
    assert any(str(impact_name) in risk["matched"] for risk in body["risks"])


def test_score_returns_missing_review_recommendations() -> None:
    response = client.post("/score/", json={"ground": "파쇄대", "method": "NATM", "query": "도심지 굴착"})

    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"]
    assert "지하수" in body["recommendations"][0]["title"]


def test_score_rejects_overlong_query() -> None:
    response = client.post("/score/", json={"query": "x" * 1001})

    assert response.status_code == 422
