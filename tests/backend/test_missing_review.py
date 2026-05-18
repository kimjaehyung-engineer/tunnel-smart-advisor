from backend.services.missing_review import recommend_missing_reviews


def test_natm_fractured_ground_recommends_groundwater_review() -> None:
    recommendations = recommend_missing_reviews(
        {
            "process": None,
            "ground": "파쇄대",
            "location": None,
            "method": "NATM",
            "equipment": None,
            "impact": None,
        },
        user_query="도심지 굴착",
    )

    assert recommendations
    assert recommendations[0]["type"] == "missing_condition"
    assert "지하수" in recommendations[0]["title"]
    assert recommendations[0]["suggested_filter"]["query"] == "지하수 유입"


def test_groundwater_review_is_not_recommended_when_already_covered() -> None:
    recommendations = recommend_missing_reviews(
        {
            "process": None,
            "ground": "파쇄대",
            "location": None,
            "method": "NATM",
            "equipment": None,
            "impact": "침하",
        },
        user_query="지하수 유입 검토",
    )

    assert recommendations == []
