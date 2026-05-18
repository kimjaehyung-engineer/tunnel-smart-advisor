from backend.services.data_loader import load_data
from backend.services.risk_scoring import BANDING_MODEL_VERSION, MODEL_VERSION, compute_cluster_bands, score_risks


def test_empty_selection_returns_no_risks() -> None:
    result = score_risks(
        {
            "process": None,
            "ground": None,
            "location": None,
            "method": None,
            "equipment": None,
            "impact": None,
        },
        user_query="",
    )

    assert result["sorted_risks"] == []
    assert result["critical_count"] == 0
    assert result["model_version"] == MODEL_VERSION
    assert result["banding_metadata"]["band_fallback_reason"] == "empty_scores"


def test_cluster_bands_handle_empty_scores() -> None:
    bands, metadata = compute_cluster_bands({})

    assert bands == {}
    assert metadata["banding_model_version"] == BANDING_MODEL_VERSION
    assert metadata["band_fallback_reason"] == "empty_scores"


def test_cluster_bands_keep_ties_in_same_band() -> None:
    bands, metadata = compute_cluster_bands({"Risk_2": 100.0, "Risk_1": 100.0, "Risk_3": 10.0, "Risk_4": 10.0, "Risk_5": 9.0, "Risk_6": 8.0})

    assert bands["Risk_1"]["cluster_band"] == bands["Risk_2"]["cluster_band"]
    assert bands["Risk_3"]["cluster_band"] == bands["Risk_4"]["cluster_band"]
    assert bands["Risk_1"]["cluster_band"] != bands["Risk_3"]["cluster_band"]
    assert metadata["band_boundaries"]


def test_cluster_bands_do_not_force_uniform_clusters() -> None:
    bands, metadata = compute_cluster_bands({"Risk_1": 4.0, "Risk_2": 3.0, "Risk_3": 2.0, "Risk_4": 1.0})

    assert {band["cluster_band"] for band in bands.values()} == {"B1"}
    assert metadata["band_fallback_reason"] == "no_material_gaps"


def test_cluster_bands_limit_to_four_bands() -> None:
    bands, metadata = compute_cluster_bands({f"Risk_{index}": float(100 - (index * index)) for index in range(1, 8)})

    assert len({band["cluster_band"] for band in bands.values()}) <= 4
    assert len(metadata["band_boundaries"]) <= 3


def test_condition_selection_scores_related_risks() -> None:
    data = load_data()
    trigger = data["rels"][data["rels"][":TYPE"] == "TRIGGER"].iloc[0]
    ground_id = trigger[":START_ID"]
    ground_name = data["ground"].loc[data["ground"]["id:ID"] == ground_id, "condition_name"].iloc[0]

    result = score_risks(
        {
            "process": None,
            "ground": str(ground_name),
            "location": None,
            "method": None,
            "equipment": None,
            "impact": None,
        },
        user_query="",
    )

    assert result["sorted_risks"]
    assert ground_id in result["target_nodes"]
    assert str(ground_name) in result["risk_matches"][trigger[":END_ID"]]


def test_equipment_selection_scores_strategy_related_risks() -> None:
    data = load_data()
    requires = data["rels"][data["rels"][":TYPE"] == "REQUIRES"].iloc[0]
    equipment_id = requires[":END_ID"]
    equipment_name = data["equipment"].loc[
        data["equipment"]["id:ID"] == equipment_id,
        "equip_name",
    ].iloc[0]
    mitigated = data["rels"][
        (data["rels"][":END_ID"] == requires[":START_ID"])
        & (data["rels"][":TYPE"] == "MITIGATED_BY")
    ].iloc[0]

    result = score_risks(
        {
            "process": None,
            "ground": None,
            "location": None,
            "method": None,
            "equipment": str(equipment_name),
            "impact": None,
        },
        user_query="",
    )

    assert str(equipment_id) in result["target_nodes"]
    assert str(equipment_name) in result["risk_matches"][str(mitigated[":START_ID"])]


def test_query_matching_increases_score_and_records_match() -> None:
    risk = load_data()["risk"].dropna(subset=["description"]).iloc[0]
    query_word = str(risk["description"]).split()[0]

    result = score_risks(
        {
            "process": None,
            "ground": None,
            "location": None,
            "method": None,
            "equipment": None,
            "impact": None,
        },
        user_query=query_word,
    )

    risk_id = str(risk["id:ID"])
    assert any(item_id == risk_id and score > 2.0 for item_id, score in result["sorted_risks"])
    assert "자연어 내용 매칭" in result["risk_matches"][str(risk["id:ID"])]
    assert result["score_details"][risk_id]["likelihood"] > 1.0
    assert any("자연어 질의" in text for text in result["score_details"][risk_id]["rationale"])


def test_impact_selection_scores_affected_risks() -> None:
    data = load_data()
    affects = data["rels"][data["rels"][":TYPE"] == "AFFECTS"].iloc[0]
    impact_id = affects[":END_ID"]
    impact_name = data["impact"].loc[data["impact"]["id:ID"] == impact_id, "impact_type"].iloc[0]

    result = score_risks(
        {
            "process": None,
            "ground": None,
            "location": None,
            "method": None,
            "equipment": None,
            "impact": str(impact_name),
        },
        user_query="",
    )

    assert str(impact_id) in result["target_nodes"]
    assert str(impact_name) in result["risk_matches"][str(affects[":START_ID"])]
    assert result["score_details"][str(affects[":START_ID"])]["impact_score"] >= 4.0


def test_score_details_use_neutral_defaults_for_future_optional_columns() -> None:
    data = load_data()
    trigger = data["rels"][data["rels"][":TYPE"] == "TRIGGER"].iloc[0]
    ground_name = data["ground"].loc[data["ground"]["id:ID"] == trigger[":START_ID"], "condition_name"].iloc[0]

    result = score_risks(
        {
            "process": None,
            "ground": str(ground_name),
            "location": None,
            "method": None,
            "equipment": None,
            "impact": None,
        },
        user_query="",
    )

    detail = result["score_details"][str(trigger[":END_ID"])]
    assert detail["model_version"] == MODEL_VERSION
    assert detail["frequency"] == 1.0
    assert detail["recency"] == 1.0
    assert detail["expert_weight"] == 1.0
    assert detail["project_similarity"] == 1.0


def test_score_risks_returns_cluster_band_metadata() -> None:
    data = load_data()
    trigger = data["rels"][data["rels"][":TYPE"] == "TRIGGER"].iloc[0]
    ground_name = data["ground"].loc[data["ground"]["id:ID"] == trigger[":START_ID"], "condition_name"].iloc[0]

    result = score_risks(
        {
            "process": None,
            "ground": str(ground_name),
            "location": None,
            "method": None,
            "equipment": None,
            "impact": None,
        },
        user_query="",
    )

    first_risk_id = result["sorted_risks"][0][0]
    assert result["cluster_bands"][first_risk_id]["cluster_band"].startswith("B")
    assert result["banding_metadata"]["banding_model_version"] == BANDING_MODEL_VERSION
