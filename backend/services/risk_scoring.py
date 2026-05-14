import re
from collections import defaultdict
from .data_loader import load_data

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]

def apply_filter(df_rels, target_nodes, risk_scores, risk_matches, node_id, node_label, rel_type):
    """Port of original apply_filter — lines 177-187."""
    if node_id not in target_nodes:
        target_nodes[node_id] = (node_label, "#3b82f6")
        r_ids = df_rels[(df_rels[':START_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':END_ID'].tolist()
        degree = len(r_ids) if r_ids else 1
        for r_id in r_ids:
            risk_scores[r_id] *= degree
            if node_label not in risk_matches[r_id]:
                risk_matches[r_id].append(node_label)

def score_risks(selection: dict, user_query: str = ""):
    """
    selection = {
        "process":  "1. 터널 본坑..." or None,
        "ground":   "파쇄대"         or None,
        "location": "도심지"         or None,
        "method":   "NATM"           or None,
        "equipment":"탱크크레인"      or None,
    }
    user_query = free-text string (Korean)
    Returns: { sorted_risks, risk_levels, critical_count, target_nodes, risk_matches }
    """
    data = load_data()
    df_rels   = data["rels"]
    df_risk   = data["risk"]
    df_strat  = data["strategy"]
    df_proc   = data["process"]
    df_ground = data["ground"]
    df_loc    = data["location"]
    df_method = data["method"]
    df_equip  = data["equipment"]

    risk_scores  = defaultdict(lambda: 1.0)
    risk_matches = defaultdict(list)
    target_nodes = {}

    def apply(node_id, label, rel_type):
        apply_filter(df_rels, target_nodes, risk_scores, risk_matches, node_id, label, rel_type)

    if selection.get("process"):
        row = df_proc[df_proc['name'] == selection["process"]].iloc[0]
        apply(row['id:ID'], selection["process"], 'ENCOUNTERS')

    if selection.get("ground"):
        row = df_ground[df_ground['condition_name'] == selection["ground"]].iloc[0]
        apply(row['id:ID'], selection["ground"], 'TRIGGER')

    if selection.get("location"):
        row = df_loc[df_loc['loc_name'] == selection["location"]].iloc[0]
        apply(row['id:ID'], selection["location"], 'OCCURS_AT')

    if selection.get("method"):
        row = df_method[df_method['method_name'] == selection["method"]].iloc[0]
        apply(row['id:ID'], selection["method"], 'ASSOCIATED_WITH')

    if selection.get("equipment"):
        eq_id = df_equip[df_equip['equip_name'] == selection["equipment"]]['id:ID'].values[0]
        if eq_id not in target_nodes:
            target_nodes[eq_id] = (selection["equipment"], '#3b82f6')
            strat_ids = df_rels[(df_rels[':END_ID'] == eq_id) & (df_rels[':TYPE'] == 'REQUIRES')][':START_ID'].tolist()
            strat_ids = [s for s in strat_ids if s.startswith('Strat')]
            for s_id in strat_ids:
                r_ids = df_rels[(df_rels[':END_ID'] == s_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':START_ID'].tolist()
                degree = len(r_ids) if r_ids else 1
                for r_id in r_ids:
                    risk_scores[r_id] *= degree
                    if selection["equipment"] not in risk_matches[r_id]:
                        risk_matches[r_id].append(selection["equipment"])

    if user_query:
        query_words = [w for w in re.split(r'\W+', user_query) if len(w) >= 2]

        for _, row in df_proc.dropna(subset=['name']).iterrows():
            name = row['name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'ENCOUNTERS')
                    break

        for _, row in df_ground.dropna(subset=['condition_name']).iterrows():
            name = row['condition_name']
            if name in user_query or (len(name) >= 2 and name[:2] in user_query):
                apply(row['id:ID'], name, 'TRIGGER')

        for _, row in df_loc.dropna(subset=['loc_name']).iterrows():
            name = row['loc_name']
            for cw in name.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'OCCURS_AT')
                    break

        for _, row in df_method.dropna(subset=['method_name']).iterrows():
            name = row['method_name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'ASSOCIATED_WITH')
                    break

        for _, row in df_equip.dropna(subset=['equip_name']).iterrows():
            name = row['equip_name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    eq_id = row['id:ID']
                    if eq_id not in target_nodes:
                        target_nodes[eq_id] = (name, '#8b5cf6')
                        strat_ids = df_rels[(df_rels[':END_ID'] == eq_id) & (df_rels[':TYPE'] == 'REQUIRES')][':START_ID'].tolist()
                        strat_ids = [s for s in strat_ids if s.startswith('Strat')]
                        for s_id in strat_ids:
                            r_ids = df_rels[(df_rels[':END_ID'] == s_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':START_ID'].tolist()
                            degree = len(r_ids) if r_ids else 1
                            for r_id in r_ids:
                                risk_scores[r_id] *= degree
                                if name not in risk_matches[r_id]:
                                    risk_matches[r_id].append(name)
                    break

        for _, row in df_risk.dropna(subset=['description']).iterrows():
            r_id = row['id:ID']
            desc = row['description']
            for qw in query_words:
                if qw in desc:
                    risk_scores[r_id] *= 2.0
                    if "자연어 내용 매칭" not in risk_matches[r_id]:
                        risk_matches[r_id].append("자연어 내용 매칭")

    if not risk_scores:
        return {"sorted_risks": [], "risk_levels": {}, "critical_count": 0,
                "target_nodes": {}, "risk_matches": {}}

    sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
    total_risks  = len(sorted_risks)
    risk_levels  = {}

    for idx, (r_id, s) in enumerate(sorted_risks):
        percentile = (idx + 1) / total_risks
        if percentile <= 0.05:
            risk_levels[r_id] = ("최상위 위험", "#ef4444")
        elif percentile <= 0.20:
            risk_levels[r_id] = ("상위 위험", "#f97316")
        elif percentile <= 0.50:
            risk_levels[r_id] = ("중위험", "#eab308")
        else:
            risk_levels[r_id] = ("저위험", "#22c55e")

    critical_count = sum(1 for l, _ in risk_levels.values() if l == "최상위 위험")

    return {
        "sorted_risks":   sorted_risks,
        "risk_levels":    risk_levels,
        "critical_count": critical_count,
        "target_nodes":   target_nodes,
        "risk_matches":   risk_matches,
    }