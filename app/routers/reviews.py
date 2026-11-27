"""
Reviews router for Dawaa'i AI.
Implements the mandatory first-use review system, duplicate prevention,
database aggregation, privacy-preserving public display, and admin moderation.
"""
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.models import (
    ReviewCreate, ReviewResponse, ReviewStatusResponse,
    ReviewsPublicResponse, RatingDistribution, AdminModerationRequest
)
from app.database import get_db
from app.auth import get_current_user, get_optional_current_user, get_admin_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

def format_privacy_name(full_name: Optional[str]) -> str:
    """Masks full name to protect user privacy (e.g., 'Ahmed M.')."""
    if not full_name:
        return "مستخدم موثق"
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[1][0]}."

@router.get("/me/status", response_model=ReviewStatusResponse)
async def get_my_review_status(current_user: Optional[dict] = Depends(get_optional_current_user)):
    """
    Checks the authenticated user's review status against database activity.
    Determines whether a mandatory first-use review prompt should be displayed.
    """
    if not current_user:
        return ReviewStatusResponse(
            is_authenticated=False,
            has_meaningful_use=False,
            has_submitted_first_review=False,
            should_prompt_review=False,
            pending_review_event=None
        )
        
    user_id = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Check if user has already submitted a first-use review
        cursor.execute("SELECT id FROM reviews WHERE user_id = ? AND review_type = 'first_use';", (user_id,))
        review_row = cursor.fetchone()
        has_submitted = review_row is not None
        
        # 2. Check if user has completed at least one meaningful action
        cursor.execute("""
        SELECT event_type FROM user_activities
        WHERE user_id = ? AND is_successful = 1
        ORDER BY created_at DESC LIMIT 1;
        """, (user_id,))
        activity_row = cursor.fetchone()
        has_meaningful_use = activity_row is not None
        last_event = activity_row["event_type"] if activity_row else None
        
        # Should prompt review only if user had meaningful use and hasn't submitted yet
        should_prompt = has_meaningful_use and not has_submitted
        
        return ReviewStatusResponse(
            is_authenticated=True,
            has_meaningful_use=has_meaningful_use,
            has_submitted_first_review=has_submitted,
            should_prompt_review=should_prompt,
            pending_review_event=last_event
        )

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    review_in: ReviewCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Submits a user review with server-side rating validation (1 to 5),
    persists it in the database, and enforces the unique first-use constraint.
    """
    if review_in.rating < 1 or review_in.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rating must be an integer between 1 and 5 stars."
        )
        
    user_id = current_user["id"]
    now_iso = datetime.now(timezone.utc).isoformat()
    review_id = f"rev_{uuid.uuid4().hex[:12]}"
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Server-side duplicate prevention check
        cursor.execute("SELECT id FROM reviews WHERE user_id = ? AND review_type = 'first_use';", (user_id,))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted your mandatory first-use platform review. Duplicate submission rejected."
            )
            
        cursor.execute("""
        INSERT INTO reviews (
            id, user_id, rating, comment, category, review_type, consent_public,
            is_published, moderation_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'first_use', ?, 1, 'approved', ?, ?);
        """, (
            review_id,
            user_id,
            review_in.rating,
            (review_in.comment or "").strip() or None,
            review_in.category or "ease_of_use",
            1 if review_in.consent_public else 0,
            now_iso,
            now_iso
        ))
        
        return ReviewResponse(
            id=review_id,
            user_id=user_id,
            user_name=format_privacy_name(current_user["full_name"]),
            rating=review_in.rating,
            comment=review_in.comment,
            category=review_in.category,
            review_type="first_use",
            consent_public=review_in.consent_public,
            is_published=True,
            moderation_status="approved",
            created_at=now_iso
        )

@router.get("/public", response_model=ReviewsPublicResponse)
async def get_public_reviews(
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by star rating"),
    category: Optional[str] = Query(None, description="Filter by review category"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Returns authentic, approved, published user reviews and real database aggregation metrics.
    Protects user privacy by never exposing emails or internal user IDs.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Calculate overall rating distribution and totals
        cursor.execute("""
        SELECT rating, COUNT(*) as cnt
        FROM reviews
        WHERE is_published = 1 AND moderation_status = 'approved' AND consent_public = 1
        GROUP BY rating;
        """)
        counts_by_rating = {row["rating"]: row["cnt"] for row in cursor.fetchall()}
        
        dist = RatingDistribution(
            star_1=counts_by_rating.get(1, 0),
            star_2=counts_by_rating.get(2, 0),
            star_3=counts_by_rating.get(3, 0),
            star_4=counts_by_rating.get(4, 0),
            star_5=counts_by_rating.get(5, 0)
        )
        total_reviews = sum(counts_by_rating.values())
        
        cursor.execute("""
        SELECT AVG(rating) as avg_rating
        FROM reviews
        WHERE is_published = 1 AND moderation_status = 'approved' AND consent_public = 1;
        """)
        avg_row = cursor.fetchone()
        avg_rating = round(float(avg_row["avg_rating"]), 1) if avg_row and avg_row["avg_rating"] is not None else 0.0
        
        # 2. Query filtered reviews with privacy-preserving display name
        query_sql = """
        SELECT r.id, r.user_id, r.rating, r.comment, r.category, r.review_type,
               r.consent_public, r.is_published, r.moderation_status, r.created_at,
               u.full_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.is_published = 1 AND r.moderation_status = 'approved' AND r.consent_public = 1
        """
        params = []
        if rating is not None:
            query_sql += " AND r.rating = ?"
            params.append(rating)
        if category:
            query_sql += " AND r.category = ?"
            params.append(category)
            
        query_sql += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])
        
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()
        
        reviews_list = []
        for r in rows:
            reviews_list.append(ReviewResponse(
                id=r["id"],
                user_id=r["user_id"][:6] + "***",  # Masked user id
                user_name=format_privacy_name(r["full_name"]),
                rating=r["rating"],
                comment=r["comment"],
                category=r["category"],
                review_type=r["review_type"],
                consent_public=bool(r["consent_public"]),
                is_published=bool(r["is_published"]),
                moderation_status=r["moderation_status"],
                created_at=r["created_at"]
            ))
            
        return ReviewsPublicResponse(
            total_reviews=total_reviews,
            average_rating=avg_rating,
            rating_distribution=dist,
            reviews=reviews_list
        )

@router.get("/admin", response_model=List[dict])
async def get_all_reviews_admin(admin_user: dict = Depends(get_admin_user)):
    """Admin endpoint: lists all reviews with detailed moderation info."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.*, u.email, u.full_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC;
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

@router.post("/admin/{review_id}/moderate")
async def moderate_review(
    review_id: str,
    action: AdminModerationRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin endpoint: approves or hides reviews without altering the user's score."""
    with get_db() as conn:
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        UPDATE reviews
        SET moderation_status = ?, is_published = ?, updated_at = ?
        WHERE id = ?;
        """, (action.moderation_status, 1 if action.is_published else 0, now_iso, review_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Review not found.")
            
        return {"message": f"Review {review_id} updated to {action.moderation_status}."}
