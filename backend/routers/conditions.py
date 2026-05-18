from typing import Annotated

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

from ..services.conditions_store import delete_condition, list_conditions, save_condition


class SavedConditionRequest(BaseModel):
    process: str | None = Field(default=None, max_length=120)
    ground: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    method: str | None = Field(default=None, max_length=120)
    equipment: str | None = Field(default=None, max_length=120)
    impact: str | None = Field(default=None, max_length=120)
    query: str = Field(default="", max_length=1000)


router = APIRouter(prefix="/conditions", tags=["conditions"])


@router.get("")
def saved_conditions(limit: Annotated[int, Query(ge=1, le=100)] = 50):
    return {"items": list_conditions(limit=limit)}


@router.post("", status_code=201)
def create_saved_condition(request: SavedConditionRequest):
    filters = {
        "process": request.process,
        "ground": request.ground,
        "location": request.location,
        "method": request.method,
        "equipment": request.equipment,
        "impact": request.impact,
    }
    return save_condition(filters, request.query)


@router.delete("/{condition_id}")
def remove_saved_condition(condition_id: int):
    deleted = delete_condition(condition_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved condition not found")
    return {"id": condition_id, "deleted": True}
