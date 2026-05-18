from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_supported_node_type_returns_nodes() -> None:
    response = client.get("/nodes/ground")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "ground"
    assert len(body["nodes"]) > 0


def test_prd_node_types_return_nodes() -> None:
    expected_fields = {
        "role": "role_name",
        "standard": "doc_name",
        "impact": "impact_type",
        "project": "name",
        "lesson": "content",
    }

    for node_type, display_field in expected_fields.items():
        response = client.get(f"/nodes/{node_type}")

        assert response.status_code == 200
        body = response.json()
        assert body["type"] == node_type
        assert len(body["nodes"]) > 0
        assert display_field in body["nodes"][0]


def test_prd_schema_fields_are_exposed_on_risk_and_strategy_nodes() -> None:
    risk_response = client.get("/nodes/risk")
    strategy_response = client.get("/nodes/strategy")

    assert risk_response.status_code == 200
    assert strategy_response.status_code == 200
    risk = risk_response.json()["nodes"][0]
    strategy = strategy_response.json()["nodes"][0]
    for field in ["cause", "impact", "likelihood", "impact_score", "frequency", "recency", "confidence", "expert_weight", "source_project", "source_version"]:
        assert field in risk
    for field in ["target_risk", "expected_effect", "required_equipment", "related_standard", "responsible_role"]:
        assert field in strategy


def test_project_nodes_are_canonical_and_linked_to_risk_strategy_cases() -> None:
    project_response = client.get("/nodes/project")
    assert project_response.status_code == 200
    projects = project_response.json()["nodes"]
    assert len(projects) > 100
    assert projects[0][":LABEL"] == "Project"

    from backend.services.data_loader import load_data

    data = load_data()
    rel_types = set(data["rels"][":TYPE"].astype(str).tolist())
    assert "HAS_RISK_CASE" in rel_types
    assert "APPLIED_STRATEGY" in rel_types
    assert len(data["rels"][data["rels"][":TYPE"] == "HAS_RISK_CASE"]) == len(data["risk"])
    assert len(data["rels"][data["rels"][":TYPE"] == "APPLIED_STRATEGY"]) == len(data["strategy"])


def test_lesson_nodes_are_loaded_from_rail_import_seed() -> None:
    response = client.get("/nodes/lesson")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "lesson"
    assert body["nodes"]
    assert body["nodes"][0][":LABEL"] == "LessonLearned"
    assert body["nodes"][0]["content"]


def test_unsupported_node_type_returns_404() -> None:
    response = client.get("/nodes/unknown")

    assert response.status_code == 404
