import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.services.notification import NotificationService

client = TestClient(app)

def test_notification_creation_and_deduplication():
    db = SessionLocal()
    try:
        # 1. Create notification
        notif1 = NotificationService.create_notification(
            db=db,
            recipient_id="test_reader_notif",
            event_type="verification_change",
            title="Verification Update",
            message="Status changed to Fact-check rated TRUE",
            event_key="unique_evt_101",
            story_id="story_101"
        )
        assert notif1 is not None
        assert notif1.is_read is False

        # 2. Duplicate event_key should return existing without creating second record
        notif2 = NotificationService.create_notification(
            db=db,
            recipient_id="test_reader_notif",
            event_type="verification_change",
            title="Verification Update",
            message="Status changed again",
            event_key="unique_evt_101",
            story_id="story_101"
        )
        assert notif2.id == notif1.id
    finally:
        db.close()

def test_notification_api_endpoints():
    reader_id = "reader_api_test"

    db = SessionLocal()
    try:
        NotificationService.create_notification(
            db=db,
            recipient_id=reader_id,
            event_type="topic_alert",
            title="New AI Article",
            message="BBC reported on AI advances.",
            event_key="api_test_evt_1"
        )
        NotificationService.create_notification(
            db=db,
            recipient_id=reader_id,
            event_type="contradiction_alert",
            title="Contradiction Detected",
            message="Conflicting reports detected in story cluster.",
            event_key="api_test_evt_2"
        )
    finally:
        db.close()

    # GET notifications
    list_resp = client.get("/api/notifications", headers={"X-Reader-Id": reader_id})
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["unread_count"] >= 2
    assert len(data["notifications"]) >= 2
    first_notif_id = data["notifications"][0]["id"]

    # PATCH read single
    read_resp = client.patch(f"/api/notifications/{first_notif_id}/read")
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    # POST read-all
    read_all_resp = client.post("/api/notifications/read-all", headers={"X-Reader-Id": reader_id})
    assert read_all_resp.status_code == 200

    # Verify unread count is 0
    after_resp = client.get("/api/notifications", headers={"X-Reader-Id": reader_id})
    assert after_resp.json()["unread_count"] == 0

def test_notification_preferences():
    reader_id = "reader_pref_user"

    # GET preferences
    pref_resp = client.get("/api/notifications/preferences", headers={"X-Reader-Id": reader_id})
    assert pref_resp.status_code == 200
    pref = pref_resp.json()
    assert pref["notifications_enabled"] is True
    assert "artificial intelligence" in pref["followed_topics"]

    # PUT update preferences
    update_resp = client.put(
        "/api/notifications/preferences",
        json={
            "followed_topics": ["artificial intelligence", "climate"],
            "notifications_enabled": False
        },
        headers={"X-Reader-Id": reader_id}
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["notifications_enabled"] is False
    assert "climate" in updated["followed_topics"]
