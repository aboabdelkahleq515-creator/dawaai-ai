"""
Configuration module for Dawaa'i AI backend.
Loads and manages environment variables, database paths, and third-party API configurations.
"""
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

def resolve_database_path() -> str:
    """
    Intelligently resolves the active database path.
    Prioritizes explicit DATABASE_PATH from env, then dawaai.db, then medicines.db,
    or backups if present. Never deletes or corrupts any existing database files.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.getenv("DATABASE_PATH")
    
    if env_path:
        full_env_path = os.path.abspath(os.path.join(base_dir, env_path)) if not os.path.isabs(env_path) else env_path
        if os.path.exists(full_env_path) and os.path.getsize(full_env_path) > 1024:
            return full_env_path

    # Primary candidate: dawaai.db
    dawaai_path = os.path.join(base_dir, "dawaai.db")
    if os.path.exists(dawaai_path) and os.path.getsize(dawaai_path) > 1024:
        return dawaai_path

    # Secondary candidate: medicines.db
    medicines_path = os.path.join(base_dir, "medicines.db")
    if os.path.exists(medicines_path) and os.path.getsize(medicines_path) > 1024:
        return medicines_path

    # Backups fallback
    for b_name in ["dawaai.backup_20261103_121447.db", "medicines.backup.db", "dawaai.backup.db"]:
        b_path = os.path.join(base_dir, b_name)
        if os.path.exists(b_path) and os.path.getsize(b_path) > 1024:
            return b_path

    return dawaai_path

class Settings(BaseModel):
    PROJECT_NAME: str = "Dawaa'i AI"
    ARABIC_NAME: str = "دوائي"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Security & JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dawaai-super-secret-jwt-key-2026-production-teal")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    
    # Gemini AI API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_TEXT: str = os.getenv("GEMINI_MODEL_TEXT", "gemini-3.5-flash-lite")
    GEMINI_MODEL_VISION: str = os.getenv("GEMINI_MODEL_VISION", "gemini-3.5-flash-lite")
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "10.0"))
    
    # Database
    DATABASE_PATH: str = resolve_database_path()
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
