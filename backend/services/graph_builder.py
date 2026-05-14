from .data_loader import load_data

def build_graph_json(target_nodes, sorted_risks, risk_levels, risk_matches, top_n=10, strategy_n=2):
    """
    Returns { nodes: [...], edges: [...] } for vis-network.
    Replaces pyvis Network() + save_graph() in app.py lines 389-421.
    """
    data = load_data()
    df_risk  = data["risk"]
    df_strat = data["strategy"]
    df_rels  = data["rels"]

    nodes = []
    edges = []

    for t_id, (t_label, t_color) in target_nodes.items():
        nodes.append({"id": t_id, "label": "Condition", "title": t_label,
                       "color": t_color, "size": 35})

    for r_id, score in sorted_risks[:top_n]:
        r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
        level_text, level_color = risk_levels.get(r_id, ("중위험", "#eab308"))
        is_critical = level_text == "최상위 위험"

        nodes.append({
            "id":    r_id,
            "label": "Critical Risk" if is_critical else "Risk",
            "title": r_desc,
            "color": level_color,
            "size":  45 if is_critical else 25,
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
            strat_ids = df_rels[
                (df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')
            ][':END_ID'].tolist()
            for s_id in strat_ids[:strategy_n]:
                s_row = df_strat[df_strat['id:ID'] == s_id]
                if s_row.empty:
                    continue
                s_label = s_row['action'].values[0]
                nodes.append({
                    "id":    s_id,
                    "label": "Strategy",
                    "title": s_label,
                    "color": "#10b981",
                    "size":  20,
                })
                edges.append({
                    "from": r_id, "to": s_id,
                    "title": "MITIGATED",
                    "color": "#6ee7b7",
                })

    return {"nodes": nodes, "edges": edges}