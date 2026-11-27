"""
Main FastAPI application entry point for Dawaa'i AI.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.database import init_db
from app.medicines_db import seed_initial_medicines
from app.routers import auth, medicines, scan, leaflets, assistant, reviews, statistics
from app.ai_provider import ai_provider
from app.database import get_db
from datetime import datetime, timezone

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[startup] Dawaa'i AI starting in '{settings.ENVIRONMENT}' mode...")
    
    # Auto-extract or download database if dawaai.db does not exist
    db_path = settings.DATABASE_PATH
    if not os.path.exists(db_path):
        if os.path.exists(f"{db_path}.zip"):
            print(f"[startup] Unzipping local packaged database {db_path}.zip ...")
            import zipfile
            with zipfile.ZipFile(f"{db_path}.zip", "r") as z:
                z.extractall(".")
            print(f"[startup] Extracted {db_path} successfully ({os.path.getsize(db_path)/(1024*1024):.2f} MB).")
        else:
            print(f"[startup] Downloading database from GitHub release v1.0.0 ...")
            try:
                import urllib.request
                import zipfile
                url = "https://github.com/aboabdelkahleq515-creator/dawaai-ai/releases/download/v1.0.0/dawaai.db.zip"
                urllib.request.urlretrieve(url, f"{db_path}.zip")
                with zipfile.ZipFile(f"{db_path}.zip", "r") as z:
                    z.extractall(".")
                print(f"[startup] Downloaded and extracted {db_path} successfully ({os.path.getsize(db_path)/(1024*1024):.2f} MB).")
            except Exception as ex:
                print(f"[startup] Database auto-download note: {ex}")
        
    print(f"[startup] Active database: {settings.DATABASE_PATH}")
    init_db()
    seed_initial_medicines()
    print("[startup] Application startup complete - Dawaa'i AI ready.")
    yield

app = FastAPI(
    title=f"{settings.PROJECT_NAME} ({settings.ARABIC_NAME})",
    description="AI-powered bilingual medicine information platform with verified health authority sources.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(medicines.router, prefix=settings.API_PREFIX)
app.include_router(scan.router, prefix=settings.API_PREFIX)
app.include_router(leaflets.router, prefix=settings.API_PREFIX)
app.include_router(assistant.router, prefix=settings.API_PREFIX)
app.include_router(reviews.router, prefix=settings.API_PREFIX)
app.include_router(statistics.router, prefix=settings.API_PREFIX)

# Static files directory
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Dawaa'i AI API is operational. Static frontend is initializing."})

@app.get("/login")
@app.get("/search")
@app.get("/scan")
@app.get("/leaflet")
@app.get("/assistant")
@app.get("/about")
@app.get("/admin")
@app.get("/history")
async def serve_spa_routes():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/health")
async def health_check():
    """
    System Health & AI Provider Status Diagnostic Endpoint.
    Checks server, database connectivity, primary & fallback AI models, and error logs.
    """
    db_status = "healthy"
    db_counts = {}
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM medicines WHERE is_hidden = 0;")
            db_counts["total_active_records"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM medicines WHERE classification = 'registered_drug' AND is_verified = 1 AND is_hidden = 0;")
            db_counts["verified_registered_drugs"] = cursor.fetchone()[0]
    except Exception as e:
        db_status = f"unhealthy: {e}"

    ai_health = ai_provider.get_health_status()

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app": settings.PROJECT_NAME,
        "arabic": settings.ARABIC_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": db_status,
            "path": os.path.basename(settings.DATABASE_PATH),
            **db_counts
        },
        "ai_services": ai_health,
        "env_status": {
            "environment_configured": bool(settings.ENVIRONMENT),
            "jwt_secret_configured": bool(settings.JWT_SECRET and len(settings.JWT_SECRET) > 10),
            "google_client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
            "gemini_api_key_configured": bool(settings.GEMINI_API_KEY)
        }
    }
