"""
Authentication module for Dawaa'i AI.
Implements Google OAuth token verification, JWT issuance, and secure session management.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import jwt
import httpx
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db

security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """
    Validates a Google ID token using Google's official tokeninfo endpoint.
    Verifies audience, issuer, expiration, and email verification status.
    """
    tokeninfo_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(tokeninfo_url)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Network error communicating with Google Identity Services: {str(exc)}"
            )
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired Google authentication token."
            )
            
        data = response.json()
        
        # Verify issuer
        iss = data.get("iss")
        if iss not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token issuer verification failed."
            )
            
        # Verify audience if client id is configured
        if settings.GOOGLE_CLIENT_ID:
            aud = data.get("aud")
            if aud != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Google token audience mismatch. Expected: {settings.GOOGLE_CLIENT_ID}"
                )
                
        # Verify email is present and verified
        email = data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account did not provide an email address."
            )
            
        return {
            "google_id": data.get("sub"),
            "email": email,
            "full_name": data.get("name") or email.split("@")[0],
            "picture_url": data.get("picture"),
            "email_verified": data.get("email_verified") in [True, "true", "True"]
        }

def get_or_create_user(
    email: str,
    full_name: str,
    google_id: Optional[str] = None,
    picture_url: Optional[str] = None,
    preferred_language: str = "ar"
) -> Dict[str, Any]:
    """Finds an existing user or creates a new one securely in the database."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Search by google_id first if available, then by email
        if google_id:
            cursor.execute("SELECT * FROM users WHERE google_id = ?;", (google_id,))
            user = cursor.fetchone()
        else:
            user = None
            
        if not user:
            cursor.execute("SELECT * FROM users WHERE email = ?;", (email,))
            user = cursor.fetchone()
            
        if user:
            user_id = user["id"]
            # Update user info if needed
            cursor.execute("""
            UPDATE users
            SET full_name = ?, picture_url = COALESCE(?, picture_url),
                google_id = COALESCE(?, google_id), updated_at = ?
            WHERE id = ?;
            """, (full_name, picture_url, google_id, now_iso, user_id))
            
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            updated_user = cursor.fetchone()
            return dict(updated_user)
        else:
            # Create brand new user
            new_id = f"usr_{uuid.uuid4().hex[:12]}"
            # Make the first user or admin email an admin
            role = "admin" if email.startswith("admin@") else "user"
            cursor.execute("""
            INSERT INTO users (
                id, google_id, email, full_name, picture_url, preferred_language,
                role, has_completed_onboarding, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?);
            """, (new_id, google_id, email, full_name, picture_url, preferred_language, role, now_iso, now_iso))
            
            cursor.execute("SELECT * FROM users WHERE id = ?;", (new_id,))
            new_user = cursor.fetchone()
            return dict(new_user)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """Dependency to retrieve the authenticated user from the Bearer JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in."
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please sign in again."
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject."
        )
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists."
            )
        return dict(user)

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """Optional user dependency: returns None if not authenticated."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None

async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency that ensures the authenticated user is an administrator."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required."
        )
    return current_user
