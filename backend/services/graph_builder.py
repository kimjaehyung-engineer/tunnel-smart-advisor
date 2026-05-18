from .data_loader import load_data
from .risk_scoring import RiskLevels, RiskMatches, SortedRisks, TargetNodes


def values_for_ids(frame, ids: list[str], id_column: str, value_column: str) -> list[str]:
    if not ids or value_column not in frame.columns:
        return []
    values = frame[frame[id_column].isin(ids)][value_column].dropna().tolist()
    return [str(value) for value in values]


def related_ids(df_rels, start_ids: list[str], rel_type: str, *, direction: str = "out") -> list[str]:
    if direction == "in":
        matches = df_rels[(df_rels[":END_ID"].isin(start_ids)) & (df_rels[":TYPE"] == rel_type)]
        return [str(value) for value in matches[":START_ID"].tolist()]
    matches = df_rels[(df_rels[":START_ID"].isin(start_ids)) & (df_rels[":TYPE"] == rel_type)]
    return [str(value) for value in matches[":END_ID"].tolist()]

def build_graph_json(
    target_nodes: TargetNodes,
    sorted_risks: SortedRisks,
    risk_levels: RiskLevels,
    risk_matches: RiskMatches,
    top_n: int = 10,
    strategy_n: int = 2,
) -> dict[str, list[dict[str, object]]]:
    """
    Returns { nodes: [...], edges: [...] } for vis-network.
    Replaces the legacy Streamlit/PyVis HTML generation path.
    """
    data = load_data()
    df_risk  = data["risk"]
    df_strat = data["strategy"]
    df_impact = data["impact"]
    df_role = data["role"]
    df_standard = data["standard"]
    df_rels  = data["rels"]

    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    for t_id, (t_label, t_color) in target_nodes.items():
        nodes.append({"id": t_id, "label": "Condition", "title": t_label,
                       "color": t_color, "size": 35})

    for r_id, _score in sorted_risks[:top_n]:
        risk_descriptions = df_risk.loc[df_risk['id:ID'] == r_id, 'description'].tolist()
        r_desc = str(risk_descriptions[0]) if risk_descriptions else ''
        risk_projects = df_risk.loc[df_risk['id:ID'] == r_id, 'source_project'].tolist()
        r_project = str(risk_projects[0]) if risk_projects else ''
        risk_rows = df_risk[df_risk['id:ID'] == r_id]
        risk_row = risk_rows.iloc[0] if not risk_rows.empty else {}
        level_text, level_color = risk_levels.get(r_id, ("중위험", "#eab308"))
        is_critical = level_text == "최상위 위험"
        all_strat_ids = related_ids(df_rels, [r_id], "MITIGATED_BY")
        all_strategy_labels = values_for_ids(df_strat, all_strat_ids, "id:ID", "action")
        impact_ids = related_ids(df_rels, [r_id], "AFFECTS")
        impact_labels = values_for_ids(df_impact, impact_ids, "id:ID", "impact_type")
        role_ids = related_ids(df_rels, all_strat_ids, "ASSIGNED_TO")
        role_labels = values_for_ids(df_role, role_ids, "id:ID", "role_name")
        standard_ids = related_ids(df_rels, all_strat_ids, "BASED_ON")
        standard_labels = values_for_ids(df_standard, standard_ids, "id:ID", "doc_name")

        nodes.append({
            "id":    r_id,
            "label": "Critical Risk" if is_critical else "Risk",
            "title": r_desc,
            "color": level_color,
            "size":  45 if is_critical else 25,
            "detail": {
                "project": r_project,
                "sourceVersion": str(risk_row.get("source_version", "")) if hasattr(risk_row, "get") else "",
                "sourceLL": str(risk_row.get("source_ll", "")) if hasattr(risk_row, "get") else "",
                "cause": str(risk_row.get("cause", "")) if hasattr(risk_row, "get") else "",
                "impactText": str(risk_row.get("impact_text", "")) if hasattr(risk_row, "get") else "",
                "matched": risk_matches.get(r_id, []),
                "strategies": all_strategy_labels[:5],
                "impacts": impact_labels,
                "roles": role_labels,
                "standards": standard_labels,
            },
        })

        for t_id, (t_label, _) in target_nodes.items():
            if t_label in risk_matches.get(r_id, []):
                edges.append({
                    "from": t_id, "to": r_id,
                    "title": "RELATES_TO",
                    "width": 4 if is_critical else 1,
                    "color": "#94a3b8",
                })

        if is_critical:
            strat_ids = all_strat_ids
            for s_id in strat_ids[:strategy_n]:
                s_row = df_strat[df_strat['id:ID'] == s_id]
                if s_row.empty:
                    continue
                strategy_actions = s_row['action'].tolist()
                s_label = str(strategy_actions[0]) if strategy_actions else ''
                strategy_role_ids = related_ids(df_rels, [s_id], "ASSIGNED_TO")
                strategy_standard_ids = related_ids(df_rels, [s_id], "BASED_ON")
                nodes.append({
                    "id":    s_id,
                    "label": "Strategy",
                    "title": s_label,
                    "color": "#10b981",
                    "size":  20,
                    "detail": {
                        "targetRisk": str(s_row.iloc[0].get("target_risk", "")),
                        "expectedEffect": str(s_row.iloc[0].get("expected_effect", "")),
                        "requiredEquipment": str(s_row.iloc[0].get("required_equipment", "")),
                        "relatedStandard": str(s_row.iloc[0].get("related_standard", "")),
                        "responsibleRole": str(s_row.iloc[0].get("responsible_role", "")),
                        "roles": values_for_ids(df_role, strategy_role_ids, "id:ID", "role_name"),
                        "standards": values_for_ids(df_standard, strategy_standard_ids, "id:ID", "doc_name"),
                    },
                })
                edges.append({
                    "from": r_id, "to": s_id,
                    "title": "MITIGATED",
                    "color": "#6ee7b7",
                })

    return {"nodes": nodes, "edges": edges}
