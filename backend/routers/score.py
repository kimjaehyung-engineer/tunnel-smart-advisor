from fastapi import APIRouter
from pydantic import BaseModel
from ..services.risk_scoring import score_risks
from ..services.graph_builder import build_graph_json

router = APIRouter(prefix="/score", tags=["risk"])

class ScoreRequest(BaseModel):
    process:   str | None = None
    ground:    str | None = None
    location:  str | None = None
    method:    str | None = None
    equipment: str | None = None
    query:     str = ""

@router.post("/")
def score(request: ScoreRequest):
    result = score_risks(
        selection={
            "process":   request.process,
            "ground":    request.ground,
            "location":  request.location,
            "method":    request.method,
            "equipment": request.equipment,
        },
        user_query=request.query,
    )

    sorted_risks    = result["sorted_risks"]
    risk_levels     = result["risk_levels"]
    critical_count  = result["critical_count"]
    target_nodes    = result["target_nodes"]
    risk_matches    = result["risk_matches"]

    if not sorted_risks:
        return {
            "total_risks": 0, "critical_count": 0, "max_score": 0.0,
            "risks": [], "graph": {"nodes": [], "edges": []}
        }

    max_score = sorted_risks[0][1]

    from ..services.data_loader import load_data
    df_risk  = load_data()["risk"]
    df_strat = load_data()["strategy"]
    df_rels  = load_data()["rels"]

    risks_out = []
    for r_id, score in sorted_risks[:15]:
        r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
        level_text, level_color = risk_levels[r_id]
        matched_tags = " | ".join(risk_matches[r_id])

        strat_ids = df_rels[
            (df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')
        ][':END_ID'].tolist()
        strategies = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()

        risks_out.append({
            "id":          r_id,
            "description": r_desc,
            "score":       round(float(score), 1),
            "level":       level_text,
            "color":       level_color,
            "matched":     matched_tags,
            "strategies":  strategies,
        })

    graph = build_graph_json(target_nodes, sorted_risks, risk_levels, risk_matches)

    return {
        "total_risks":    len(sorted_risks),
        "critical_count": critical_count,
        "max_score":     round(float(max_score), 1),
        "risks":         risks_out,
        "graph":         graph,
    }