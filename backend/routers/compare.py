from fastapi import APIRouter
from pydantic import BaseModel

from .score import ScoreRequest
from ..services.comparison_report_store import save_comparison_report
from ..services.design_compare import compare_design_change

router = APIRouter(prefix="/compare", tags=["compare"])


class DesignChangeCompareRequest(BaseModel):
    before: ScoreRequest
    after: ScoreRequest


def selection_from_request(request: ScoreRequest) -> dict[str, str | None]:
    return {
        "process": request.process,
        "ground": request.ground,
        "location": request.location,
        "method": request.method,
        "equipment": request.equipment,
        "impact": request.impact,
    }


@router.post("/design-change")
def design_change_compare(request: DesignChangeCompareRequest):
    return compare_design_change(
        selection_from_request(request.before),
        request.before.query,
        selection_from_request(request.after),
        request.after.query,
    )


@router.post("/design-change/reports", status_code=201)
def create_design_change_report(request: DesignChangeCompareRequest):
    before: dict[str, object] = {
        "process": request.before.process,
        "ground": request.before.ground,
        "location": request.before.location,
        "method": request.before.method,
        "equipment": request.before.equipment,
        "impact": request.before.impact,
        "query": request.before.query,
    }
    after: dict[str, object] = {
        "process": request.after.process,
        "ground": request.after.ground,
        "location": request.after.location,
        "method": request.after.method,
        "equipment": request.after.equipment,
        "impact": request.after.impact,
        "query": request.after.query,
    }
    result = compare_design_change(
        selection_from_request(request.before),
        request.before.query,
        selection_from_request(request.after),
        request.after.query,
    )
    report = save_comparison_report(before=before, after=after, result=result)
    report_id = int(report["id"])
    return {
        "id": report_id,
        "report_type": "comparison",
        "title": report["title"],
        "created_at": report["created_at"],
        "download_url": f"/reports/compare/{report_id}.html",
        "pdf_url": f"/reports/compare/{report_id}.pdf",
        "package_url": f"/reports/compare/{report_id}.zip",
        "model_version": report["model_version"],
        "data_version": report["data_version"],
    }
