from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.notification_store import archive_notification, list_notifications, mark_all_read, set_notification_important, set_notification_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


class ImportantRequest(BaseModel):
    is_important: bool


@router.get("")
def notifications(filter: Literal["all", "unread", "important"] = "all"):
    return list_notifications(filter_by=filter)


@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int):
    notification = set_notification_read(notification_id, True)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/{notification_id}/important")
def mark_notification_important(notification_id: int, request: ImportantRequest):
    notification = set_notification_important(notification_id, request.is_important)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.delete("/{notification_id}")
def delete_notification(notification_id: int):
    notification = archive_notification(notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/read-all")
def mark_notifications_read():
    return mark_all_read()
