from fastapi.testclient import TestClient

from backend.main import app
from backend.services.data_loader import load_data


client = TestClient(app)


def test_library_items_support_backend_keyword_category_and_tag_filters() -> None:
    all_response = client.get("/library/items")
    assert all_response.status_code == 200
    all_body = all_response.json()
    first_item = all_body["items"][0]
    keyword = first_item["title"].split()[0]
    category = first_item["category"]

    filtered_response = client.get("/library/items", params={"query": keyword, "category": category})

    assert filtered_response.status_code == 200
    body = filtered_response.json()
    assert body["filters"] == {"query": keyword, "category": category, "tag": "전체", "relation_type": "전체"}
    assert body["items"]
    assert all(item["category"] == category for item in body["items"])

    tag = all_body["popularTags"][0]["label"]
    tag_response = client.get("/library/items", params={"tag": tag})
    assert tag_response.status_code == 200
    assert tag_response.json()["items"]
    assert all(tag in item["tags"] for item in tag_response.json()["items"])


def test_library_items_support_full_text_and_relation_type_filters() -> None:
    all_response = client.get("/library/items")
    assert all_response.status_code == 200
    body = all_response.json()
    assert body["relationTypes"]
    relation_type = next(item["label"] for item in body["relationTypes"] if item["label"] != "전체")

    relation_response = client.get("/library/items", params={"relation_type": relation_type})

    assert relation_response.status_code == 200
    relation_body = relation_response.json()
    assert relation_body["filters"]["relation_type"] == relation_type
    assert relation_body["items"]
    assert all(relation_type in item["relationTypes"] for item in relation_body["items"])

    detail_response = client.get(f"/library/items/{relation_body['items'][0]['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    searchable_value = detail["cause"] or detail["impactText"] or detail["sourceLL"]
    if searchable_value:
        keyword = str(searchable_value).split()[0]
        full_text_response = client.get("/library/items", params={"query": keyword})
        assert full_text_response.status_code == 200
        assert any(item["id"] == detail["id"] for item in full_text_response.json()["items"])


def test_library_items_include_lesson_learned_relationship_search() -> None:
    response = client.get("/library/items", params={"relation_type": "LEARNED_AS"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert body["filters"]["relation_type"] == "LEARNED_AS"
    assert all("LEARNED_AS" in item["relationTypes"] for item in body["items"])

    lesson_label = body["items"][0]["tags"][0]
    search_response = client.get("/library/items", params={"query": lesson_label.split()[0]})
    assert search_response.status_code == 200
    assert any(item["id"] == body["items"][0]["id"] for item in search_response.json()["items"])


def test_library_items_return_empty_list_for_unmatched_query() -> None:
    response = client.get("/library/items", params={"query": "__no_such_tunnel_knowledge__"})

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_library_item_detail_returns_related_ontology_context() -> None:
    data = load_data()
    relation = data["rels"][data["rels"][":TYPE"] == "MITIGATED_BY"].iloc[0]
    risk_id = str(relation[":START_ID"])

    response = client.get(f"/library/items/{risk_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == risk_id
    assert body["title"]
    assert body["sourceVersion"]
    assert "sourceLL" in body
    assert "cause" in body
    assert "impactText" in body
    assert isinstance(body["relationCount"], int)
    assert set(body["relatedConditions"].keys()) == {"process", "ground", "location", "method", "equipment", "impact"}
    assert body["strategies"]
    assert "impacts" in body
    assert "standards" in body
    assert "roles" in body
    assert body["graph"]["nodes"]
    assert body["graph"]["edges"]
    assert any(node["id"] == risk_id and node["label"] == "Risk" for node in body["graph"]["nodes"])
    assert any(edge["from"] == risk_id and edge["title"] == "MITIGATED_BY" for edge in body["graph"]["edges"])


def test_library_item_detail_returns_related_lessons() -> None:
    response = client.get("/library/items/Risk_001")

    assert response.status_code == 200
    body = response.json()
    assert body["lessons"] == [
        {"id": "Lesson_1", "label": "운행선 공사 시 신설공사와 달리 추가 RISK 검토 절차 필요"}
    ]
    assert any(edge["title"] == "LEARNED_AS" for edge in body["graph"]["edges"])


def test_library_item_detail_returns_404_for_unknown_risk() -> None:
    response = client.get("/library/items/Risk_DOES_NOT_EXIST")

    assert response.status_code == 404
