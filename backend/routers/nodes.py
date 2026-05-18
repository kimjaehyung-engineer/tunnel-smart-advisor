import math
from typing import cast

from fastapi import APIRouter, HTTPException
from ..services.data_loader import load_data
from ..services.risk_scoring import natural_sort_key

router = APIRouter(prefix="/nodes", tags=["nodes"])


def sanitize_row(row: dict[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in row.items():
        is_blank = value is None or (isinstance(value, float) and math.isnan(value))
        sanitized[key] = "" if is_blank else value
    return sanitized

@router.get("/{node_type}")
def get_nodes(node_type: str):
    """
    node_type: ground | method | equipment | risk | process | location | strategy | role | standard | impact | project | lesson
    Returns list of records sorted by natural sort.
    """
    key_map = {
        "ground":     "condition_name",
        "method":     "method_name",
        "equipment":  "equip_name",
        "risk":       "description",
        "process":    "name",
        "location":   "loc_name",
        "strategy":   "action",
        "role":       "role_name",
        "standard":   "doc_name",
        "impact":     "impact_type",
        "project":    "name",
        "lesson":     "content",
    }
    name_key = key_map.get(node_type)
    if not name_key:
        raise HTTPException(status_code=404, detail=f"Unknown node type: {node_type}")

    data = load_data()
    df = data.get(node_type)
    if df is None:
        raise HTTPException(status_code=404, detail=f"No such node type: {node_type}")

    records = cast(list[dict[str, object]], df.dropna(subset=[name_key]).to_dict(orient="records"))
    rows = sorted(
        [sanitize_row(row) for row in records],
        key=lambda row: natural_sort_key(row.get(name_key, "")),
    )
    return {"nodes": rows, "type": node_type}
