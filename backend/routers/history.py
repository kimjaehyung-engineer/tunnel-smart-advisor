from fastapi import APIRouter, HTTPException, Query

from ..services.history_store import get_analysis, list_analyses
from .score import ScoreRequest, run_score_analysis

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/analyses")
def analyses(
    query: str = "",
    project: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = Query(default=50, ge=1, le=100),
):
    return {
        "items": list_analyses(
            query=query.strip(),
            project=project.strip(),
            date_from=date_from.strip(),
            date_to=date_to.strip(),
            limit=limit,
        )
    }


@router.get("/analyses/{history_id}")
def analysis_detail(history_id: int):
    analysis = get_analysis(history_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis history not found")
    return analysis


@router.post("/analyses/{history_id}/rerun")
def rerun_analysis(history_id: int):
    analysis = get_analysis(history_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis history not found")
    filters = analysis.get("filters", {})
    if not isinstance(filters, dict):
        raise HTTPException(status_code=422, detail="Saved analysis filters are invalid")
    request = ScoreRequest(
        process=filters.get("process"),
        ground=filters.get("ground"),
        location=filters.get("location"),
        method=filters.get("method"),
        equipment=filters.get("equipment"),
        impact=filters.get("impact"),
        query=str(analysis.get("query") or ""),
    )
    return run_score_analysis(request)
