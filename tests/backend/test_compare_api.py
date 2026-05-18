from fastapi.testclient import TestClient

from backend.main import app
from backend.services.data_loader import load_data


client = TestClient(app)


def test_design_change_compare_returns_before_after_deltas() -> None:
    data = load_data()
    trigger = data["rels"][data["rels"][":TYPE"] == "TRIGGER"].iloc[0]
    ground_name = data["ground"].loc[data["ground"]["id:ID"] == trigger[":START_ID"], "condition_name"].iloc[0]

    response = client.post(
        "/compare/design-change",
        json={
            "before": {"query": ""},
            "after": {"ground": str(ground_name), "query": ""},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["before"]["total_risks"] == 0
    assert body["after"]["total_risks"] > 0
    assert body["new_risks"]
    assert body["removed_risks"] == []
    assert "increased_risks" in body
    assert "decreased_risks" in body
    assert "additional_strategies" in body
    assert "related_standards" in body


def test_design_change_compare_rejects_overlong_query() -> None:
    response = client.post(
        "/compare/design-change",
        json={
            "before": {"query": ""},
            "after": {"query": "x" * 1001},
        },
    )

    assert response.status_code == 422
