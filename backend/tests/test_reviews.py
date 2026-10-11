import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_reader_review_submission_and_aggregation():
    target_id = "test_art_reviews_1"

    # 1. Reader 1 rates 5 stars
    resp1 = client.post(
        f"/api/reviews/article/{target_id}",
        json={"rating": 5, "review_text": "Very informative article with clear sources.", "reader_name": "Alice"},
        headers={"X-Reader-Id": "reader_alice"}
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["rating"] == 5
    assert data1["reader_name"] == "Alice"
    assert data1["reader_id"] == "reader_alice"
    assert "rev_" in data1["id"]

    # 2. Reader 2 rates 3 stars
    resp2 = client.post(
        f"/api/reviews/article/{target_id}",
        json={"rating": 3, "review_text": "Decent summary but lacks detail.", "reader_name": "Bob"},
        headers={"X-Reader-Id": "reader_bob"}
    )
    assert resp2.status_code == 200

    # 3. Retrieve summary: average should be (5 + 3) / 2 = 4.0
    summary_resp = client.get(
        f"/api/reviews/article/{target_id}",
        headers={"X-Reader-Id": "reader_alice"}
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_ratings"] == 2
    assert summary["average_rating"] == 4.0
    assert summary["rating_distribution"]["5"] == 1
    assert summary["rating_distribution"]["3"] == 1
    assert summary["user_review"] is not None
    assert summary["user_review"]["reader_id"] == "reader_alice"
    assert "Reader ratings reflect reader experience" in summary["disclaimer"]

def test_anti_inflation_upsert_review():
    """Submitting multiple ratings from the same user should update their existing rating rather than inflating counts."""
    target_id = "test_art_anti_inflation"

    # Alice rates 2 stars
    client.post(
        f"/api/reviews/article/{target_id}",
        json={"rating": 2, "review_text": "Initial thought."},
        headers={"X-Reader-Id": "reader_alice_upsert"}
    )

    # Alice changes mind and updates rating to 4 stars
    client.post(
        f"/api/reviews/article/{target_id}",
        json={"rating": 4, "review_text": "Updated perspective."},
        headers={"X-Reader-Id": "reader_alice_upsert"}
    )

    summary = client.get(f"/api/reviews/article/{target_id}").json()
    assert summary["total_ratings"] == 1  # Still 1 rating, not 2!
    assert summary["average_rating"] == 4.0
    assert summary["rating_distribution"]["4"] == 1
    assert summary["rating_distribution"]["2"] == 0

def test_review_validation_bounds():
    """Rating must be between 1 and 5 stars."""
    # Rating 0 should fail
    resp_low = client.post(
        "/api/reviews/article/art_bounds",
        json={"rating": 0},
        headers={"X-Reader-Id": "r_val"}
    )
    assert resp_low.status_code == 422

    # Rating 6 should fail
    resp_high = client.post(
        "/api/reviews/article/art_bounds",
        json={"rating": 6},
        headers={"X-Reader-Id": "r_val"}
    )
    assert resp_high.status_code == 422

def test_review_edit_and_delete_authorization():
    """A reader cannot edit or delete another reader's review."""
    target_id = "test_auth_target"
    post_resp = client.post(
        f"/api/reviews/article/{target_id}",
        json={"rating": 4, "review_text": "Author review."},
        headers={"X-Reader-Id": "original_author"}
    )
    rev_id = post_resp.json()["id"]

    # Attacker tries to edit
    edit_resp = client.put(
        f"/api/reviews/{rev_id}",
        json={"rating": 1, "review_text": "Hacked review."},
        headers={"X-Reader-Id": "attacker_user"}
    )
    assert edit_resp.status_code == 403

    # Attacker tries to delete
    del_resp = client.delete(
        f"/api/reviews/{rev_id}",
        headers={"X-Reader-Id": "attacker_user"}
    )
    assert del_resp.status_code == 403

    # Original author can successfully edit
    legit_edit = client.put(
        f"/api/reviews/{rev_id}",
        json={"rating": 5, "review_text": "Legit updated review."},
        headers={"X-Reader-Id": "original_author"}
    )
    assert legit_edit.status_code == 200
    assert legit_edit.json()["rating"] == 5

    # Original author can successfully delete
    legit_del = client.delete(
        f"/api/reviews/{rev_id}",
        headers={"X-Reader-Id": "original_author"}
    )
    assert legit_del.status_code == 200
