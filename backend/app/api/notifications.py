import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.notification import Notification, NotificationPreference
from app.schemas.notification import (
    NotificationListResponse,
    NotificationItem,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["In-App Notifications & Preferences"])

@router.get("", response_model=NotificationListResponse)
def get_notifications(
    limit: int = Query(30, ge=1, le=100),
    x_reader_id: Optional[str] = Header("anonymous", alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Retrieve persistent in-app notifications for the reader, with unread count."""
    reader_id = (x_reader_id or "anonymous").strip()

    notifications = (
        db.query(Notification)
        .filter(or_(Notification.recipient_id == reader_id, Notification.recipient_id == "all"))
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )

    unread_count = (
        db.query(Notification)
        .filter(
            or_(Notification.recipient_id == reader_id, Notification.recipient_id == "all"),
            Notification.is_read == False
        )
        .count()
    )

    return NotificationListResponse(
        unread_count=unread_count,
        total_count=len(notifications),
        notifications=notifications,
    )


@router.patch("/{notification_id}/read", response_model=NotificationItem)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """Mark an individual notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/read-all")
def mark_all_notifications_read(
    x_reader_id: Optional[str] = Header("anonymous", alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Mark all notifications for this reader as read."""
    reader_id = (x_reader_id or "anonymous").strip()

    db.query(Notification).filter(
        or_(Notification.recipient_id == reader_id, Notification.recipient_id == "all"),
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)

    db.commit()
    return {"status": "success", "message": "All notifications marked as read."}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    x_reader_id: Optional[str] = Header("anonymous", alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Retrieve user notification preferences."""
    reader_id = (x_reader_id or "anonymous").strip()
    pref = NotificationService.get_or_create_preferences(db, reader_id)

    return NotificationPreferenceResponse(
        reader_id=pref.reader_id,
        followed_topics=json.loads(pref.followed_topics or "[]"),
        followed_stories=json.loads(pref.followed_stories or "[]"),
        categories_enabled=json.loads(pref.categories_enabled or "[]"),
        notifications_enabled=pref.notifications_enabled,
        updated_at=pref.updated_at
    )


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    x_reader_id: Optional[str] = Header("anonymous", alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Update user notification preferences."""
    reader_id = (x_reader_id or "anonymous").strip()
    pref = NotificationService.get_or_create_preferences(db, reader_id)

    if payload.followed_topics is not None:
        pref.followed_topics = json.dumps(payload.followed_topics)
    if payload.followed_stories is not None:
        pref.followed_stories = json.dumps(payload.followed_stories)
    if payload.categories_enabled is not None:
        pref.categories_enabled = json.dumps(payload.categories_enabled)
    if payload.notifications_enabled is not None:
        pref.notifications_enabled = payload.notifications_enabled

    db.commit()
    db.refresh(pref)

    return NotificationPreferenceResponse(
        reader_id=pref.reader_id,
        followed_topics=json.loads(pref.followed_topics or "[]"),
        followed_stories=json.loads(pref.followed_stories or "[]"),
        categories_enabled=json.loads(pref.categories_enabled or "[]"),
        notifications_enabled=pref.notifications_enabled,
        updated_at=pref.updated_at
    )
