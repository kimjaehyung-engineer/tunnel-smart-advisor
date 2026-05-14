from fastapi import APIRouter, HTTPException
from ..services.data_loader import load_data
from ..services.risk_scoring import natural_sort_key

router = APIRouter(prefix="/nodes", tags=["nodes"])

@router.get("/{node_type}")
def get_nodes(node_type: str):
    """
    node_type: ground | method | equipment | risk | process | location | strategy
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
    }
    name_key = key_map.get(node_type)
    if not name_key:
        raise HTTPException(status_code=404, detail=f"Unknown node type: {node_type}")

    data = load_data()
    df = data.get(node_type)
    if df is None:
        raise HTTPException(status_code=404, detail=f"No such node type: {node_type}")

    rows = sorted(
        df.dropna(subset=[name_key]).to_dict(orient="records"),
        key=lambda row: natural_sort_key(row.get(name_key, "")),
    )
    return {"nodes": rows, "type": node_type}
