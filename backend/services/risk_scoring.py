import re
from collections import defaultdict
from statistics import median
from typing import TypeAlias, TypedDict

import pandas as pd

from .data_loader import load_data

SortedRisks: TypeAlias = list[tuple[str, float]]
RiskLevels: TypeAlias = dict[str, tuple[str, str]]
TargetNodes: TypeAlias = dict[str, tuple[str, str]]
RiskMatches: TypeAlias = defaultdict[str, list[str]]
RiskScoreDetails: TypeAlias = dict[str, dict[str, object]]
ClusterBands: TypeAlias = dict[str, dict[str, object]]

DEFAULT_TARGET_NODE_COLOR = "#3b82f6"
QUERY_EQUIPMENT_NODE_COLOR = "#8b5cf6"
QUERY_MATCH_LABEL = "자연어 내용 매칭"
BANDING_MODEL_VERSION = "p1_gap_bands_v1"
MODEL_VERSION = "p1_rule_components_gap_bands_v1"

class ScoreRisksResult(TypedDict):
    sorted_risks: SortedRisks
    risk_levels: RiskLevels
    critical_count: int
    target_nodes: TargetNodes
    risk_matches: RiskMatches
    score_details: RiskScoreDetails
    cluster_bands: ClusterBands
    banding_metadata: dict[str, object]
    model_version: str


def safe_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text == "nan" else text


def optional_float(row: pd.Series, column: str, default: float) -> float:
    if column not in row.index:
        return default
    value = row.get(column)
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def bounded(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def build_score_detail(risk_row: pd.Series, base_score: float, matches: list[str], impact_names: set[str]) -> dict[str, object]:
    source_ll = safe_text(risk_row.get("source_ll"))
    cause = safe_text(risk_row.get("cause"))
    impact_text = safe_text(risk_row.get("impact_text"))
    source_project = safe_text(risk_row.get("source_project"))
    source_version = safe_text(risk_row.get("source_version"))
    matched_count = len(matches)
    has_query_match = QUERY_MATCH_LABEL in matches
    has_impact_match = any(match in impact_names for match in matches)

    likelihood_default = 1.0 + min(matched_count, 4) * 0.75 + (0.5 if has_query_match else 0.0)
    likelihood = max(optional_float(risk_row, "likelihood", likelihood_default), likelihood_default)
    likelihood = bounded(likelihood, 1.0, 5.0)
    impact_default = 4.0 if has_impact_match else 3.5 if impact_text else 3.0
    impact_score = max(optional_float(risk_row, "impact_score", impact_default), impact_default)
    impact_score = bounded(impact_score, 1.0, 5.0)
    evidence_fields = sum(1 for value in [source_ll, cause, impact_text, source_project] if value)
    confidence_default = (evidence_fields / 4) * 0.6 + min(matched_count / 4, 1.0) * 0.4
    confidence = max(optional_float(risk_row, "confidence", confidence_default), confidence_default)
    confidence = bounded(confidence, 0.0, 1.0)
    frequency = optional_float(risk_row, "frequency", 1.0)
    recency = optional_float(risk_row, "recency", 1.0)
    expert_weight = optional_float(risk_row, "expert_weight", 1.0)
    project_similarity = optional_float(risk_row, "project_similarity", 1.0)

    component_boost = min(0.4, ((likelihood - 1.0) * 0.04) + ((impact_score - 3.0) * 0.05) + (confidence * 0.1))
    adjusted_score = base_score * (1.0 + component_boost)

    rationale = [
        f"기본 그래프 매칭 점수 {round(base_score, 2)}를 기준으로 계산했습니다.",
        f"매칭 근거 {matched_count}건을 발생 가능성에 반영했습니다.",
    ]
    if has_query_match:
        rationale.append("자연어 질의가 위험 설명과 직접 매칭되었습니다.")
    if has_impact_match:
        rationale.append("선택한 영향 유형과 연결된 위험입니다.")
    if impact_text:
        rationale.append("원문 영향 설명이 존재해 영향도 기본값을 상향했습니다.")
    rationale.append("빈도, 최신성, 전문가 가중치, 프로젝트 유사도는 현재 원천 데이터에 정량 컬럼이 없어 중립값 1.0을 사용했습니다.")

    return {
        "model_version": MODEL_VERSION,
        "base_score": round(float(base_score), 3),
        "adjusted_score": round(float(adjusted_score), 3),
        "likelihood": round(float(likelihood), 2),
        "impact_score": round(float(impact_score), 2),
        "confidence": round(float(confidence), 2),
        "frequency": round(float(frequency), 2),
        "recency": round(float(recency), 2),
        "expert_weight": round(float(expert_weight), 2),
        "project_similarity": round(float(project_similarity), 2),
        "matched_factors": matches,
        "rationale": rationale,
        "source_evidence": {
            "source_project": source_project,
            "source_version": source_version,
            "source_ll": source_ll,
            "cause": cause,
            "impact_text": impact_text,
        },
    }

def natural_sort_key(value: object) -> list[int | str]:
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', str(value))
    ]


def compute_cluster_bands(adjusted_scores: dict[str, float]) -> tuple[ClusterBands, dict[str, object]]:
    """Assign deterministic gap-analysis bands over adjusted risk scores.

    This is an auditable 1D heuristic, not a statistical clustering claim. Tied
    scores always share the same band and at most four bands are produced.
    """
    if not adjusted_scores:
        return {}, {
            "banding_method": "gap_analysis",
            "banding_model_version": BANDING_MODEL_VERSION,
            "band_boundaries": [],
            "band_fallback_reason": "empty_scores",
        }

    grouped: dict[float, list[str]] = defaultdict(list)
    for risk_id, score in adjusted_scores.items():
        grouped[round(float(score), 3)].append(str(risk_id))

    unique_scores = sorted(grouped.keys(), reverse=True)
    for risk_ids in grouped.values():
        risk_ids.sort(key=natural_sort_key)

    fallback_reason = ""
    cut_indexes: list[int] = []
    if len(adjusted_scores) < 4 or len(unique_scores) == 1:
        fallback_reason = "too_few_or_tied_scores"
    else:
        gaps = [round(unique_scores[index] - unique_scores[index + 1], 3) for index in range(len(unique_scores) - 1)]
        score_range = unique_scores[0] - unique_scores[-1]
        median_gap = median(gaps) if gaps else 0.0
        material_gap = max(score_range * 0.15, median_gap * 1.5, 0.001)
        candidate_indexes = [index for index, gap in enumerate(gaps) if gap >= material_gap]
        selected = sorted(candidate_indexes, key=lambda index: (-gaps[index], index))[:3]
        cut_indexes = sorted(selected)
        if not cut_indexes:
            fallback_reason = "no_material_gaps"

    band_colors = ["#ef4444", "#f97316", "#eab308", "#22c55e"]
    band_labels = ["군집 B1 (상위 점수군)", "군집 B2", "군집 B3", "군집 B4"]
    score_band_by_score: dict[float, str] = {}
    band_scores: dict[str, list[float]] = defaultdict(list)
    for score_index, score in enumerate(unique_scores):
        band_index = sum(1 for cut_index in cut_indexes if score_index > cut_index)
        band_id = f"B{band_index + 1}"
        score_band_by_score[score] = band_id
        band_scores[band_id].append(score)

    cluster_bands: ClusterBands = {}
    band_sizes = {
        band_id: sum(len(grouped[score]) for score in scores)
        for band_id, scores in band_scores.items()
    }
    for score in unique_scores:
        band_id = score_band_by_score[score]
        band_number = int(band_id[1:])
        band_score_values = band_scores[band_id]
        for risk_id in grouped[score]:
            cluster_bands[risk_id] = {
                "cluster_band": band_id,
                "cluster_label": band_labels[band_number - 1],
                "cluster_rank": band_number,
                "cluster_color": band_colors[band_number - 1],
                "cluster_score_min": min(band_score_values),
                "cluster_score_max": max(band_score_values),
                "cluster_size": band_sizes[band_id],
            }

    band_boundaries = [
        {
            "from_band": f"B{index + 1}",
            "to_band": f"B{index + 2}",
            "upper_min_score": unique_scores[cut_index],
            "lower_max_score": unique_scores[cut_index + 1],
            "gap": round(unique_scores[cut_index] - unique_scores[cut_index + 1], 3),
        }
        for index, cut_index in enumerate(cut_indexes)
    ]
    return cluster_bands, {
        "banding_method": "gap_analysis",
        "banding_model_version": BANDING_MODEL_VERSION,
        "band_boundaries": band_boundaries,
        "band_fallback_reason": fallback_reason,
    }

def apply_filter(
    df_rels: pd.DataFrame,
    target_nodes: TargetNodes,
    risk_scores: defaultdict[str, float],
    risk_matches: RiskMatches,
    node_id: object,
    node_label: str,
    rel_type: str,
) -> None:
    """Port of original apply_filter — lines 177-187."""
    node_id = str(node_id)
    if node_id not in target_nodes:
        target_nodes[node_id] = (node_label, DEFAULT_TARGET_NODE_COLOR)
        r_ids = df_rels[(df_rels[':START_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':END_ID'].tolist()
        degree = len(r_ids) if r_ids else 1
        for r_id in r_ids:
            risk_id = str(r_id)
            risk_scores[risk_id] *= degree
            if node_label not in risk_matches[risk_id]:
                risk_matches[risk_id].append(node_label)


def apply_reverse_filter(
    df_rels: pd.DataFrame,
    target_nodes: TargetNodes,
    risk_scores: defaultdict[str, float],
    risk_matches: RiskMatches,
    node_id: object,
    node_label: str,
    rel_type: str,
) -> None:
    """Score risks that point to the selected target node."""
    node_id = str(node_id)
    if node_id not in target_nodes:
        target_nodes[node_id] = (node_label, DEFAULT_TARGET_NODE_COLOR)
        r_ids = df_rels[(df_rels[':END_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':START_ID'].tolist()
        degree = len(r_ids) if r_ids else 1
        for r_id in r_ids:
            risk_id = str(r_id)
            risk_scores[risk_id] *= degree
            if node_label not in risk_matches[risk_id]:
                risk_matches[risk_id].append(node_label)

def first_matching_row(df: pd.DataFrame, column: str, value: str) -> pd.Series | None:
    matches = df[df[column] == value]
    if matches.empty:
        return None
    return matches.iloc[0]


def apply_equipment_strategy_risks(
    df_rels: pd.DataFrame,
    target_nodes: TargetNodes,
    risk_scores: defaultdict[str, float],
    risk_matches: RiskMatches,
    equipment_id: object,
    equipment_label: str,
    node_color: str,
) -> None:
    equipment_id = str(equipment_id)
    if equipment_id in target_nodes:
        return

    target_nodes[equipment_id] = (equipment_label, node_color)
    strategy_ids = df_rels[
        (df_rels[':END_ID'] == equipment_id) & (df_rels[':TYPE'] == 'REQUIRES')
    ][':START_ID'].tolist()
    strategy_ids = [str(strategy_id) for strategy_id in strategy_ids if str(strategy_id).startswith('Strat')]

    for strategy_id in strategy_ids:
        risk_ids = df_rels[
            (df_rels[':END_ID'] == strategy_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')
        ][':START_ID'].tolist()
        degree = len(risk_ids) if risk_ids else 1
        for risk_id in risk_ids:
            risk_id = str(risk_id)
            risk_scores[risk_id] *= degree
            if equipment_label not in risk_matches[risk_id]:
                risk_matches[risk_id].append(equipment_label)

def score_risks(selection: dict[str, str | None], user_query: str = "") -> ScoreRisksResult:
    """
    selection = {
        "process":  "1. 터널 본坑..." or None,
        "ground":   "파쇄대"         or None,
        "location": "도심지"         or None,
        "method":   "NATM"           or None,
        "equipment":"탱크크레인"      or None,
        "impact":   "침하"            or None,
    }
    user_query = free-text string (Korean)
    Returns: { sorted_risks, risk_levels, critical_count, target_nodes, risk_matches }
    """
    data = load_data()
    df_rels   = data["rels"]
    df_risk   = data["risk"]
    df_proc   = data["process"]
    df_ground = data["ground"]
    df_loc    = data["location"]
    df_method = data["method"]
    df_equip  = data["equipment"]
    df_impact = data["impact"]
    impact_names = set(df_impact["impact_type"].dropna().astype(str).tolist())

    risk_scores: defaultdict[str, float] = defaultdict(lambda: 1.0)
    risk_matches: RiskMatches = defaultdict(list)
    target_nodes: TargetNodes = {}

    def apply(node_id: object, label: str, rel_type: str) -> None:
        apply_filter(df_rels, target_nodes, risk_scores, risk_matches, node_id, label, rel_type)

    def apply_reverse(node_id: object, label: str, rel_type: str) -> None:
        apply_reverse_filter(df_rels, target_nodes, risk_scores, risk_matches, node_id, label, rel_type)

    if selected_process := selection.get("process"):
        row = first_matching_row(df_proc, 'name', selected_process)
        if row is not None:
            apply(str(row['id:ID']), selected_process, 'ENCOUNTERS')

    if selected_ground := selection.get("ground"):
        row = first_matching_row(df_ground, 'condition_name', selected_ground)
        if row is not None:
            apply(str(row['id:ID']), selected_ground, 'TRIGGER')

    if selected_location := selection.get("location"):
        row = first_matching_row(df_loc, 'loc_name', selected_location)
        if row is not None:
            apply(str(row['id:ID']), selected_location, 'OCCURS_AT')

    if selected_method := selection.get("method"):
        row = first_matching_row(df_method, 'method_name', selected_method)
        if row is not None:
            apply(str(row['id:ID']), selected_method, 'ASSOCIATED_WITH')

    if selected_equipment := selection.get("equipment"):
        row = first_matching_row(df_equip, 'equip_name', selected_equipment)
        if row is not None:
            apply_equipment_strategy_risks(
                df_rels,
                target_nodes,
                risk_scores,
                risk_matches,
                row['id:ID'],
                selected_equipment,
                DEFAULT_TARGET_NODE_COLOR,
            )

    if selected_impact := selection.get("impact"):
        row = first_matching_row(df_impact, 'impact_type', selected_impact)
        if row is not None:
            apply_reverse(str(row['id:ID']), selected_impact, 'AFFECTS')

    if user_query:
        query_words = [w for w in re.split(r'\W+', user_query) if len(w) >= 2]

        for _, row in df_proc.dropna(subset=['name']).iterrows():
            name = str(row['name'])
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'ENCOUNTERS')
                    break

        for _, row in df_ground.dropna(subset=['condition_name']).iterrows():
            name = str(row['condition_name'])
            if name in user_query or (len(name) >= 2 and name[:2] in user_query):
                apply(row['id:ID'], name, 'TRIGGER')

        for _, row in df_loc.dropna(subset=['loc_name']).iterrows():
            name = str(row['loc_name'])
            for cw in name.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'OCCURS_AT')
                    break

        for _, row in df_method.dropna(subset=['method_name']).iterrows():
            name = str(row['method_name'])
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply(row['id:ID'], name, 'ASSOCIATED_WITH')
                    break

        for _, row in df_equip.dropna(subset=['equip_name']).iterrows():
            name = str(row['equip_name'])
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply_equipment_strategy_risks(
                        df_rels,
                        target_nodes,
                        risk_scores,
                        risk_matches,
                        row['id:ID'],
                        name,
                        QUERY_EQUIPMENT_NODE_COLOR,
                    )
                    break

        for _, row in df_impact.dropna(subset=['impact_type']).iterrows():
            name = str(row['impact_type'])
            for cw in name.split():
                if len(cw) >= 2 and cw in user_query:
                    apply_reverse(row['id:ID'], name, 'AFFECTS')
                    break

        for _, row in df_risk.dropna(subset=['description']).iterrows():
            r_id = str(row['id:ID'])
            desc = str(row['description'])
            for qw in query_words:
                if qw in desc:
                    risk_scores[r_id] *= 2.0
                    if QUERY_MATCH_LABEL not in risk_matches[r_id]:
                        risk_matches[r_id].append(QUERY_MATCH_LABEL)

    if not risk_scores:
        return {"sorted_risks": [], "risk_levels": {}, "critical_count": 0,
                "target_nodes": {}, "risk_matches": defaultdict(list), "score_details": {},
                "cluster_bands": {}, "banding_metadata": compute_cluster_bands({})[1],
                "model_version": MODEL_VERSION}

    risk_rows_by_id = {str(row["id:ID"]): row for _, row in df_risk.iterrows()}
    score_details: RiskScoreDetails = {}
    adjusted_scores: dict[str, float] = {}
    for r_id, base_score in risk_scores.items():
        risk_row = risk_rows_by_id.get(str(r_id), pd.Series(dtype=object))
        detail = build_score_detail(risk_row, float(base_score), risk_matches[str(r_id)], impact_names)
        score_details[str(r_id)] = detail
        adjusted_scores[str(r_id)] = float(detail["adjusted_score"])

    sorted_risks = sorted(adjusted_scores.items(), key=lambda item: (-item[1], natural_sort_key(item[0])))
    total_risks  = len(sorted_risks)
    risk_levels: RiskLevels = {}
    cluster_bands, banding_metadata = compute_cluster_bands(adjusted_scores)

    for idx, (r_id, _score) in enumerate(sorted_risks):
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
        "score_details":  score_details,
        "cluster_bands":  cluster_bands,
        "banding_metadata": banding_metadata,
        "model_version":  MODEL_VERSION,
    }
