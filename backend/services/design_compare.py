from typing import TypedDict

from .data_loader import load_data
from .risk_scoring import MODEL_VERSION, score_risks


Selection = dict[str, str | None]


class CompareSummary(TypedDict):
    total_risks: int
    max_score: float
    critical_count: int


def values_for_ids(key: str, ids: list[str], value_column: str) -> list[str]:
    frame = load_data()[key]
    id_set = set(ids)
    values = [
        str(row.get(value_column))
        for _, row in frame.iterrows()
        if str(row.get("id:ID")) in id_set and row.get(value_column) is not None
    ]
    return sorted(set(values))


def risk_title_lookup() -> dict[str, str]:
    risks = load_data()["risk"]
    return {
        str(row["id:ID"]): str(row.get("description", ""))
        for _, row in risks.iterrows()
    }


def risk_snapshot(selection: Selection, query: str, limit: int = 15) -> tuple[CompareSummary, dict[str, dict[str, object]]]:
    result = score_risks(selection, query)
    titles = risk_title_lookup()
    risks: dict[str, dict[str, object]] = {}
    for risk_id, score in result["sorted_risks"][:limit]:
        level, color = result["risk_levels"][risk_id]
        risks[risk_id] = {
            "id": risk_id,
            "description": titles.get(risk_id, ""),
            "score": round(float(score), 1),
            "level": level,
            "color": color,
            "matched": result["risk_matches"].get(risk_id, []),
        }
    summary: CompareSummary = {
        "total_risks": len(result["sorted_risks"]),
        "max_score": round(float(result["sorted_risks"][0][1]), 1) if result["sorted_risks"] else 0.0,
        "critical_count": result["critical_count"],
    }
    return summary, risks


def related_strategy_and_standard_labels(risk_ids: set[str]) -> tuple[list[str], list[str]]:
    data = load_data()
    rels = data["rels"]
    strategy_ids = [
        str(row.get(":END_ID"))
        for _, row in rels.iterrows()
        if str(row.get(":START_ID")) in risk_ids and row.get(":TYPE") == "MITIGATED_BY"
    ]
    strategy_id_set = set(strategy_ids)
    standard_ids = [
        str(row.get(":END_ID"))
        for _, row in rels.iterrows()
        if str(row.get(":START_ID")) in strategy_id_set and row.get(":TYPE") == "BASED_ON"
    ]
    return (
        values_for_ids("strategy", strategy_ids, "action")[:10],
        values_for_ids("standard", standard_ids, "doc_name")[:10],
    )


def compare_design_change(before: Selection, before_query: str, after: Selection, after_query: str) -> dict[str, object]:
    before_summary, before_risks = risk_snapshot(before, before_query)
    after_summary, after_risks = risk_snapshot(after, after_query)
    before_ids = set(before_risks)
    after_ids = set(after_risks)
    new_ids = after_ids - before_ids
    removed_ids = before_ids - after_ids
    shared_ids = before_ids & after_ids
    increased_ids = {
        risk_id for risk_id in shared_ids
        if score_value(after_risks[risk_id]) > score_value(before_risks[risk_id])
    }
    decreased_ids = {
        risk_id for risk_id in shared_ids
        if score_value(after_risks[risk_id]) < score_value(before_risks[risk_id])
    }
    strategies, standards = related_strategy_and_standard_labels(new_ids | increased_ids)
    return {
        "model_version": MODEL_VERSION,
        "before": before_summary,
        "after": after_summary,
        "new_risks": [after_risks[risk_id] for risk_id in sorted(new_ids)],
        "removed_risks": [before_risks[risk_id] for risk_id in sorted(removed_ids)],
        "increased_risks": [after_risks[risk_id] for risk_id in sorted(increased_ids)],
        "decreased_risks": [before_risks[risk_id] for risk_id in sorted(decreased_ids)],
        "additional_strategies": strategies,
        "related_standards": standards,
    }


def score_value(risk: dict[str, object]) -> float:
    value = risk.get("score", 0.0)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0
