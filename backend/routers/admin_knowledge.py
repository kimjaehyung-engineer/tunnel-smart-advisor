from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.knowledge_store import create_knowledge_submission, list_knowledge_submissions, update_knowledge_status


KnowledgeItemType = Literal["risk", "strategy", "lesson", "project", "standard", "equipment", "method"]
KnowledgeStatus = Literal["pending_review", "verified", "rejected"]


class KnowledgeSubmissionRequest(BaseModel):
    item_type: KnowledgeItemType
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    source: str = Field(default="", max_length=500)


class KnowledgeStatusRequest(BaseModel):
    verification_status: KnowledgeStatus
    reviewer: str = Field(default="", max_length=120)
    review_note: str = Field(default="", max_length=1000)


router = APIRouter(prefix="/admin/knowledge", tags=["admin", "knowledge"])


@router.get("/items")
def knowledge_items(
    item_type: KnowledgeItemType | None = None,
    verification_status: KnowledgeStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
):
    return {
        "items": list_knowledge_submissions(
            item_type=item_type or "",
            verification_status=verification_status or "",
            limit=limit,
        )
    }


@router.post("/items", status_code=201)
def create_knowledge_item(request: KnowledgeSubmissionRequest):
    return create_knowledge_submission(
        item_type=request.item_type,
        title=request.title.strip(),
        content=request.content.strip(),
        tags=request.tags,
        source=request.source.strip(),
    )


@router.post("/items/{submission_id}/status")
def set_knowledge_item_status(submission_id: int, request: KnowledgeStatusRequest):
    item = update_knowledge_status(
        submission_id=submission_id,
        verification_status=request.verification_status,
        reviewer=request.reviewer.strip(),
        review_note=request.review_note.strip(),
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge submission not found")
    return item
