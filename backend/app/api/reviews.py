import html
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.review import ReaderReview
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewItem, ReviewSummary

router = APIRouter(prefix="/reviews", tags=["Reader Ratings & Reviews"])

def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Basic XSS prevention sanitization."""
    if not text:
        return None
    return html.escape(text.strip())

@router.get("/{target_type}/{target_id}", response_model=ReviewSummary)
def get_reviews_summary(
    target_type: str,
    target_id: str,
    limit: int = Query(20, ge=1, le=100),
    x_reader_id: Optional[str] = Header(None, alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Retrieve reader ratings aggregate statistics, rating distribution, and written reviews."""
    target_type_clean = target_type.lower().strip()
    if target_type_clean not in ["article", "story"]:
        raise HTTPException(status_code=400, detail="Target type must be 'article' or 'story'.")

    # Fetch all reviews for this target
    all_reviews = (
        db.query(ReaderReview)
        .filter(ReaderReview.target_type == target_type_clean, ReaderReview.target_id == target_id)
        .order_by(ReaderReview.created_at.desc())
        .all()
    )

    total_ratings = len(all_reviews)
    distribution = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    sum_ratings = 0

    user_review = None
    for rev in all_reviews:
        score_str = str(rev.rating)
        if score_str in distribution:
            distribution[score_str] += 1
        sum_ratings += rev.rating

        if x_reader_id and rev.reader_id == x_reader_id:
            user_review = rev

    avg_rating = round(sum_ratings / total_ratings, 1) if total_ratings > 0 else 0.0

    return ReviewSummary(
        target_type=target_type_clean,
        target_id=target_id,
        average_rating=avg_rating,
        total_ratings=total_ratings,
        rating_distribution=distribution,
        user_review=user_review,
        reviews=all_reviews[:limit],
    )


@router.post("/{target_type}/{target_id}", response_model=ReviewItem)
def submit_or_update_review(
    target_type: str,
    target_id: str,
    payload: ReviewCreate,
    x_reader_id: Optional[str] = Header(None, alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Submit a reader rating (1-5 stars) and optional review.
    
    Prevents repeated vote inflation: If reader has already reviewed this target,
    updates their existing review record instead of creating duplicates.
    """
    target_type_clean = target_type.lower().strip()
    if target_type_clean not in ["article", "story"]:
        raise HTTPException(status_code=400, detail="Target type must be 'article' or 'story'.")

    reader_id = (x_reader_id or "anonymous").strip()
    clean_text = sanitize_text(payload.review_text)
    clean_name = sanitize_text(payload.reader_name) or "Anonymous Reader"

    # Check for existing review by this reader
    existing = (
        db.query(ReaderReview)
        .filter(
            ReaderReview.target_type == target_type_clean,
            ReaderReview.target_id == target_id,
            ReaderReview.reader_id == reader_id
        )
        .first()
    )

    if existing:
        # Update existing rating and review
        existing.rating = payload.rating
        existing.review_text = clean_text
        existing.reader_name = clean_name
        db.commit()
        db.refresh(existing)
        return existing

    # Create new review
    new_review = ReaderReview(
        target_type=target_type_clean,
        target_id=target_id,
        reader_id=reader_id,
        reader_name=clean_name,
        rating=payload.rating,
        review_text=clean_text
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


@router.put("/{review_id}", response_model=ReviewItem)
def update_review(
    review_id: str,
    payload: ReviewUpdate,
    x_reader_id: str = Header(..., alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Update a written review. Enforces strict authorization: user can only edit their own review."""
    rev = db.query(ReaderReview).filter(ReaderReview.id == review_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found.")

    if rev.reader_id != x_reader_id.strip():
        raise HTTPException(status_code=403, detail="Unauthorized: You cannot modify another reader's review.")

    if payload.rating is not None:
        rev.rating = payload.rating
    if payload.review_text is not None:
        rev.review_text = sanitize_text(payload.review_text)
    if payload.reader_name is not None:
        rev.reader_name = sanitize_text(payload.reader_name) or rev.reader_name

    db.commit()
    db.refresh(rev)
    return rev


@router.delete("/{review_id}")
def delete_review(
    review_id: str,
    x_reader_id: str = Header(..., alias="X-Reader-Id"),
    db: Session = Depends(get_db)
):
    """Delete a review. Enforces strict authorization: user can only delete their own review."""
    rev = db.query(ReaderReview).filter(ReaderReview.id == review_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Review not found.")

    if rev.reader_id != x_reader_id.strip():
        raise HTTPException(status_code=403, detail="Unauthorized: You cannot delete another reader's review.")

    db.delete(rev)
    db.commit()
    return {"status": "success", "message": "Review deleted successfully."}
