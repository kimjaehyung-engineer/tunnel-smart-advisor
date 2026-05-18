from backend.services.graph_builder import build_graph_json


def test_graph_json_contains_nodes_edges_and_strategy_for_critical_risk() -> None:
    graph = build_graph_json(
        target_nodes={"Ground_test": ("파쇄대", "#3b82f6")},
        sorted_risks=[("Risk_001", 10.0)],
        risk_levels={"Risk_001": ("최상위 위험", "#ef4444")},
        risk_matches={"Risk_001": ["파쇄대"]},
        top_n=1,
        strategy_n=2,
    )

    assert set(graph.keys()) == {"nodes", "edges"}
    risk_node = next(node for node in graph["nodes"] if node["id"] == "Risk_001")
    assert "detail" in risk_node
    assert "strategies" in risk_node["detail"]
    assert "sourceLL" in risk_node["detail"]
    assert "sourceVersion" in risk_node["detail"]
    assert "cause" in risk_node["detail"]
    assert "impactText" in risk_node["detail"]
    assert any(edge["from"] == "Ground_test" and edge["to"] == "Risk_001" for edge in graph["edges"])
    strategy_node = next(node for node in graph["nodes"] if node["label"] == "Strategy")
    assert "targetRisk" in strategy_node["detail"]
    assert "expectedEffect" in strategy_node["detail"]
