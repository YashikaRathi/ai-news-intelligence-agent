import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationPreference

logger = logging.getLogger(__name__)

class NotificationService:
    """Service handling creation, deduplication, and retrieval of persistent in-app notifications."""

    @staticmethod
    def get_or_create_preferences(db: Session, reader_id: str) -> NotificationPreference:
        """Retrieve user notification preferences or create sensible default preferences."""
        pref = db.query(NotificationPreference).filter(NotificationPreference.reader_id == reader_id).first()
        if not pref:
            default_categories = json.dumps(["topic_alert", "story_update", "verification_change", "contradiction_alert"])
            pref = NotificationPreference(
                reader_id=reader_id,
                followed_topics=json.dumps(["artificial intelligence", "technology"]),
                followed_stories=json.dumps([]),
                categories_enabled=default_categories,
                notifications_enabled=True,
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def create_notification(
        db: Session,
        recipient_id: str,
        event_type: str,
        title: str,
        message: str,
        event_key: Optional[str] = None,
        story_id: Optional[str] = None,
        article_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> Optional[Notification]:
        """Create an in-app notification with deduplication by event_key."""
        try:
            # 1. Deduplication check
            if event_key:
                existing = db.query(Notification).filter(Notification.event_key == event_key).first()
                if existing:
                    return existing

            # 2. Check recipient preferences if specific reader
            if recipient_id != "all":
                pref = db.query(NotificationPreference).filter(NotificationPreference.reader_id == recipient_id).first()
                if pref:
                    if not pref.notifications_enabled:
                        return None
                    try:
                        enabled_cats = json.loads(pref.categories_enabled or "[]")
                        if event_type not in enabled_cats:
                            return None
                    except Exception:
                        pass

            notif = Notification(
                recipient_id=recipient_id,
                event_type=event_type,
                title=title,
                message=message,
                story_id=story_id,
                article_id=article_id,
                topic=topic,
                event_key=event_key,
                is_read=False,
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)
            return notif
        except Exception as exc:
            db.rollback()
            logger.warning(f"Error creating notification: {exc}")
            return None

    @staticmethod
    def notify_verification_change(
        db: Session,
        story_id: str,
        story_title: str,
        new_status: str,
        reason: str
    ):
        """Notify readers when a story verification status materially updates."""
        event_key = f"verif_change_{story_id}_{new_status}"
        title = f"Verification Update: {new_status}"
        message = f"Story '{story_title[:60]}...' status updated to '{new_status}'. {reason}"
        
        NotificationService.create_notification(
            db=db,
            recipient_id="all",
            event_type="verification_change",
            title=title,
            message=message,
            event_key=event_key,
            story_id=story_id
        )

    @staticmethod
    def notify_topic_article(
        db: Session,
        article_id: str,
        article_title: str,
        topic: str,
        source_name: str
    ):
        """Create notification for fresh article matching topic."""
        event_key = f"topic_art_{topic.lower()}_{article_id}"
        title = f"New Coverage: {topic.title()}"
        message = f"{source_name} reported: '{article_title[:70]}...'"

        NotificationService.create_notification(
            db=db,
            recipient_id="all",
            event_type="topic_alert",
            title=title,
            message=message,
            event_key=event_key,
            article_id=article_id,
            topic=topic
        )
