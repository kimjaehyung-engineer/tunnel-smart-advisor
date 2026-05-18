from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.data_loader import load_data
from ..services.standards_link_store import list_standards_links, save_standards_link
from ..services.standards_evidence import list_standards, revalidate_standard_nodes, search_clauses, search_evidence, verify_standard_code

router = APIRouter(prefix="/standards", tags=["standards"])


class StandardsLinkRequest(BaseModel):
    target_type: Literal["risk", "strategy"]
    target_id: str = Field(..., min_length=1, max_length=160)
    standard_code: str = Field(..., min_length=1, max_length=40)
    standard_name: str = Field(default="", max_length=200)
    clause_path: str = Field(..., min_length=1, max_length=500)
    clause_label: str = Field(default="", max_length=80)
    clause_text: str = Field(default="", max_length=3000)
    source_url: str = Field(default="", max_length=500)
    note: str = Field(default="", max_length=1000)


@router.get("/evidence")
def standards_evidence(query: str = "", limit: int = Query(default=5, ge=1, le=20)):
    return {
        "query": query,
        "items": search_evidence(query=query.strip(), limit=limit),
        "source": "KCSC Standards MCP seed evidence",
    }


@router.get("/search")
def standards_search(query: str = "", limit: int = Query(default=20, ge=1, le=50)):
    return {
        "query": query,
        "items": list_standards(query=query.strip(), limit=limit),
        "source": "KCSC Standards MCP seed evidence",
    }


@router.get("/clauses")
def standards_clauses(query: str = "", code: str = "", limit: int = Query(default=10, ge=1, le=50)):
    return {
        "query": query,
        "code": code,
        "items": search_clauses(query=query.strip(), code=code.strip(), limit=limit),
        "source": "KCSC Standards MCP seed evidence",
    }


@router.get("/verify")
def standards_verify(code: str = Query(..., min_length=1, max_length=40)):
    return verify_standard_code(code)


@router.post("/revalidate")
def standards_revalidate():
    standards = load_data()["standard"].to_dict(orient="records")
    return revalidate_standard_nodes(standards)


@router.get("/links")
def standards_links(
    target_type: Literal["risk", "strategy"] | None = None,
    target_id: str = Query(default="", max_length=160),
    standard_code: str = Query(default="", max_length=40),
    limit: int = Query(default=100, ge=1, le=200),
):
    return {
        "items": list_standards_links(
            target_type=target_type or "",
            target_id=target_id.strip(),
            standard_code=standard_code.strip(),
            limit=limit,
        )
    }


@router.post("/links", status_code=201)
def create_standards_link(request: StandardsLinkRequest):
    verification = verify_standard_code(request.standard_code)
    if not verification["is_valid"]:
        raise HTTPException(status_code=400, detail="Standard code is not available in seeded KCSC evidence")
    standard = verification.get("standard")
    standard_name = request.standard_name
    source_url = request.source_url
    if isinstance(standard, dict):
        standard_name = standard_name or str(standard.get("name", ""))
        source_url = source_url or str(standard.get("source_url", ""))
    return save_standards_link(
        target_type=request.target_type,
        target_id=request.target_id.strip(),
        standard_code=str(verification["code"]),
        standard_name=standard_name,
        clause_path=request.clause_path.strip(),
        clause_label=request.clause_label.strip(),
        clause_text=request.clause_text.strip(),
        source_url=source_url,
        note=request.note.strip(),
    )
