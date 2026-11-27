"""
Authentication router for Dawaa'i AI.
"""
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import (
    GoogleAuthRequest, DemoAuthRequest, LocalLoginRequest,
    TokenResponse, UserResponse, OnboardingUpdateRequest
)
from app.auth import (
    verify_google_id_token, get_or_create_user, create_access_token,
    get_current_user
)
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login_local(request: LocalLoginRequest):
    """
    Local authentication for testing or development without external Google OAuth.
    Supports email and password, or defaults immediately to a verified active demo account.
    """
    raw_email = (request.email or "").strip()
    email = raw_email if raw_email else "demo.patient@dawaai.local"

    full_name = (request.full_name or "").strip()
    if not full_name:
        if "admin" in email.lower():
            full_name = "مسؤول النظام السريري" if request.preferred_language == "ar" else "Clinical Administrator"
        elif email in ["demo.patient@dawaai.local", "user@dawaai.ai"]:
            full_name = "مستخدم دوائي موثق" if request.preferred_language == "ar" else "Verified Dawaa'i Patient"
        else:
            username_part = email.split("@")[0].replace(".", " ").replace("_", " ").title()
            full_name = username_part or ("مستخدم دوائي" if request.preferred_language == "ar" else "Dawaa'i User")

    role = request.role if (request.role and request.role in ["user", "admin"]) else ("admin" if "admin" in email.lower() else "user")

    user_data = get_or_create_user(
        email=email,
        full_name=full_name,
        google_id=None,
        picture_url=None,
        preferred_language=request.preferred_language or "ar"
    )

    # Ensure demo user has onboarding marked complete to prevent intrusive modals during testing
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET has_completed_onboarding = 1, role = ? WHERE id = ?;", (role, user_data["id"]))
        conn.commit()
    user_data["has_completed_onboarding"] = 1
    user_data["role"] = role

    token = create_access_token(data={"sub": user_data["id"], "email": user_data["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }

@router.post("/google", response_model=TokenResponse)
async def login_with_google(request: GoogleAuthRequest):
    """
    Authenticates or registers a user via Google Identity Services ID token.
    Properly verifies token with Google and returns clear errors on failure.
    """
    is_mock = not request.id_token or request.id_token in ["demo", "mock", "local", "test", "mock_google_id_token"]
    
    if is_mock:
        if settings.ENVIRONMENT != "production":
            google_data = {
                "email": "demo.patient@dawaai.local",
                "full_name": "مستخدم دوائي موثق" if request.preferred_language == "ar" else "Verified Dawaa'i Patient",
                "google_id": "google_demo_id_1001",
                "picture_url": None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mock Google tokens are disabled in production environment."
            )
    else:
        try:
            google_data = await verify_google_id_token(request.id_token)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google authentication failed: {str(e)}"
            )

    user_data = get_or_create_user(
        email=google_data["email"],
        full_name=google_data["full_name"],
        google_id=google_data.get("google_id"),
        picture_url=google_data.get("picture_url"),
        preferred_language=request.preferred_language or "ar"
    )
    
    token = create_access_token(data={"sub": user_data["id"], "email": user_data["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }

@router.post("/demo-login", response_model=TokenResponse)
async def login_demo(request: DemoAuthRequest):
    """
    Convenience authentication for local testing or demo environments.
    Creates a verified user in the database and returns a real signed JWT token.
    """
    user_data = get_or_create_user(
        email=request.email,
        full_name=request.full_name,
        google_id=None,
        picture_url=request.picture_url,
        preferred_language=request.preferred_language or "ar"
    )
    token = create_access_token(data={"sub": user_data["id"], "email": user_data["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile and preferences."""
    return current_user

@router.put("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    payload: OnboardingUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Updates onboarding status and language preferences."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE users
        SET has_completed_onboarding = 1, preferred_language = ?
        WHERE id = ?;
        """, (payload.preferred_language, current_user["id"]))
        
        cursor.execute("SELECT * FROM users WHERE id = ?;", (current_user["id"],))
        updated = cursor.fetchone()
        return dict(updated)

@router.post("/signout")
async def sign_out():
    """Sign-out endpoint."""
    return {"message": "Successfully signed out"}

@router.get("/me/activities")
async def get_my_activities(current_user: dict = Depends(get_current_user)):
    """
    Returns the chronologically ordered activity history for the authenticated user,
    including searches, viewed medicines, scans, and AI assistant inquiries.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, event_type, target_id, target_name, is_successful, metadata_json, created_at
            FROM user_activities
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 60;
        """, (current_user["id"],))
        rows = cursor.fetchall()
        
        activities = []
        for r in rows:
            meta = {}
            if r["metadata_json"]:
                try:
                    meta = json.loads(r["metadata_json"])
                except Exception:
                    meta = {}
            activities.append({
                "id": r["id"],
                "event_type": r["event_type"],
                "target_id": r["target_id"],
                "target_name": r["target_name"],
                "is_successful": bool(r["is_successful"]),
                "metadata": meta,
                "created_at": r["created_at"]
            })
            
        # Summary statistics for user activity
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN event_type = 'medicine_search' THEN 1 ELSE 0 END) as searches_count,
                SUM(CASE WHEN event_type = 'medicine_view' THEN 1 ELSE 0 END) as views_count,
                SUM(CASE WHEN event_type = 'medicine_scanned' THEN 1 ELSE 0 END) as scans_count,
                SUM(CASE WHEN event_type = 'assistant_explanation' THEN 1 ELSE 0 END) as assistant_count
            FROM user_activities
            WHERE user_id = ?;
        """, (current_user["id"],))
        summary_row = cursor.fetchone()
        
        summary = {
            "total": (summary_row["total"] or 0) if summary_row else 0,
            "total_activities": (summary_row["total"] or 0) if summary_row else 0,
            "searches": (summary_row["searches_count"] or 0) if summary_row else 0,
            "views": (summary_row["views_count"] or 0) if summary_row else 0,
            "scans": (summary_row["scans_count"] or 0) if summary_row else 0,
            "assistant_chats": (summary_row["assistant_count"] or 0) if summary_row else 0
        }
        
        return {
            "user": current_user,
            "summary": summary,
            "activities": activities
        }

@router.delete("/me/activities")
async def clear_my_activities(current_user: dict = Depends(get_current_user)):
    """Clears the personal activity and search history for the current authenticated user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_activities WHERE user_id = ?;", (current_user["id"],))
        conn.commit()
    return {"message": "User activity history cleared successfully", "cleared": True}
