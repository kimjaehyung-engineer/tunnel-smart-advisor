import logging
import time

from fastapi import APIRouter
from fastapi import Request as FastAPIRequest
from pydantic import BaseModel, Field, field_validator
from ..services.risk_scoring import MODEL_VERSION, score_risks
from ..services.graph_builder import build_graph_json
from ..services.metrics import metrics
from ..services.history_store import save_analysis
from ..services.notification_store import create_notification
from ..services.ontology_version import load_ontology_version
from ..services.missing_review import recommend_missing_reviews

router = APIRouter(prefix="/score", tags=["risk"])
logger = logging.getLogger("tunnel.score")


def unique_text_values(values: object) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    to_list = getattr(values, "tolist", None)
    if not callable(to_list):
        return output
    raw_values = to_list()
    if not isinstance(raw_values, list):
        return output
    for value in raw_values:
        text = str(value).strip()
        if text and text != "nan" and text not in seen:
            seen.add(text)
            output.append(text)
    return output

class ScoreRequest(BaseModel):
    process:   str | None = Field(default=None, max_length=120)
    ground:    str | None = Field(default=None, max_length=120)
    location:  str | None = Field(default=None, max_length=120)
    method:    str | None = Field(default=None, max_length=120)
    equipment: str | None = Field(default=None, max_length=120)
    impact:    str | None = Field(default=None, max_length=120)
    query:     str = Field(default="", max_length=1000)

    @field_validator("process", "ground", "location", "method", "equipment", "impact", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        return value

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: object) -> object:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value

@router.post("/")
def score(request: ScoreRequest, http_request: FastAPIRequest):
    return run_score_analysis(request, request_id=getattr(http_request.state, "request_id", ""))


def run_score_analysis(request: ScoreRequest, request_id: str = ""):
    started = time.perf_counter()
    selection = {
        "process":   request.process,
        "ground":    request.ground,
        "location":  request.location,
        "method":    request.method,
        "equipment": request.equipment,
        "impact":    request.impact,
    }
    result = score_risks(
        selection=selection,
        user_query=request.query,
    )
    recommendations = recommend_missing_reviews(selection, request.query)
    data_version = load_ontology_version()

    sorted_risks    = result["sorted_risks"]
    risk_levels     = result["risk_levels"]
    critical_count  = result["critical_count"]
    target_nodes    = result["target_nodes"]
    risk_matches    = result["risk_matches"]
    score_details   = result["score_details"]
    cluster_bands   = result["cluster_bands"]
    banding_metadata = result["banding_metadata"]

    if not sorted_risks:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics.record_score(latency_ms)
        response = {
            "total_risks": 0, "critical_count": 0, "max_score": 0.0,
            "risks": [], "graph": {"nodes": [], "edges": []}, "data_version": data_version,
            "model_version": MODEL_VERSION,
            **banding_metadata,
            "recommendations": recommendations,
        }
        history = save_analysis(selection, request.query, response)
        response["history_id"] = history["id"]
        create_notification("analysis", "분석 완료", f"분석 #{history['id']}이 완료되었습니다.")
        logger.info(
            "Score request completed",
            extra={
                "event": "score_request",
                "request_id": request_id,
                "filters": selection,
                "result_count": 0,
                "latency_ms": latency_ms,
            },
        )
        return response

    max_score = sorted_risks[0][1]

    from ..services.data_loader import load_data
    df_risk  = load_data()["risk"]
    df_strat = load_data()["strategy"]
    df_rels  = load_data()["rels"]
    df_role  = load_data()["role"]
    df_standard = load_data()["standard"]

    risks_out = []
    for r_id, score in sorted_risks[:15]:
        r_desc = str(next(iter(df_risk.loc[df_risk['id:ID'] == r_id, 'description']), ''))
        r_project = str(next(iter(df_risk.loc[df_risk['id:ID'] == r_id, 'source_project']), ''))
        level_text, level_color = risk_levels[r_id]
        matched_tags = " | ".join(risk_matches[r_id])

        strat_ids = df_rels[
            (df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')
        ][':END_ID'].tolist()
        strategies = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()
        role_ids = df_rels[
            (df_rels[':START_ID'].isin(strat_ids)) & (df_rels[':TYPE'] == 'ASSIGNED_TO')
        ][':END_ID'].tolist()
        standard_ids = df_rels[
            (df_rels[':START_ID'].isin(strat_ids)) & (df_rels[':TYPE'] == 'BASED_ON')
        ][':END_ID'].tolist()
        roles = unique_text_values(df_role[df_role['id:ID'].isin(role_ids)]['role_name'])
        standards = unique_text_values(df_standard[df_standard['id:ID'].isin(standard_ids)]['doc_name'])
        detail = score_details.get(r_id, {})
        cluster_detail = cluster_bands.get(r_id, {})
        source_evidence = detail.get("source_evidence", {}) if isinstance(detail, dict) else {}

        risks_out.append({
            "id":          r_id,
            "description": r_desc,
            "project":     r_project,
            "score":       round(float(score), 1),
            "level":       level_text,
            "color":       level_color,
            "cluster_band": cluster_detail.get("cluster_band", "B1"),
            "cluster_label": cluster_detail.get("cluster_label", "군집 B1"),
            "cluster_rank": cluster_detail.get("cluster_rank", 1),
            "cluster_color": cluster_detail.get("cluster_color", level_color),
            "cluster_score_min": cluster_detail.get("cluster_score_min", score),
            "cluster_score_max": cluster_detail.get("cluster_score_max", score),
            "cluster_size": cluster_detail.get("cluster_size", 1),
            "matched":     matched_tags,
            "strategies":  strategies,
            "standards": standards,
            "roles": roles,
            "source_evidence": source_evidence,
            "likelihood": detail.get("likelihood", 1.0),
            "impact": source_evidence.get("impact_text", "") if isinstance(source_evidence, dict) else "",
            "impact_score": detail.get("impact_score", 3.0),
            "confidence": detail.get("confidence", 0.0),
            "frequency": detail.get("frequency", 1.0),
            "recency": detail.get("recency", 1.0),
            "expert_weight": detail.get("expert_weight", 1.0),
            "project_similarity": detail.get("project_similarity", 1.0),
            "score_explanation": detail,
        })

    graph = build_graph_json(target_nodes, sorted_risks, risk_levels, risk_matches)

    response = {
        "total_risks":    len(sorted_risks),
        "critical_count": critical_count,
        "max_score":     round(float(max_score), 1),
        "risks":         risks_out,
        "graph":         graph,
        "data_version":  data_version,
        "model_version": result["model_version"],
        **banding_metadata,
        "recommendations": recommendations,
    }
    history = save_analysis(selection, request.query, response)
    response["history_id"] = history["id"]
    create_notification("analysis", "분석 완료", f"분석 #{history['id']}이 완료되었습니다.")
    if critical_count > 0:
        create_notification("risk", "고위험 결과 발생", f"분석 #{history['id']}에서 최상위 위험 {critical_count}건이 감지되었습니다.", is_important=True)
    logger.info(
        "Score request completed",
        extra={
            "event": "score_request",
            "request_id": request_id,
            "filters": selection,
            "result_count": response["total_risks"],
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    metrics.record_score(round((time.perf_counter() - started) * 1000, 2))
    return response
