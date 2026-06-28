import os
# TensorFlow & CUDA memory and log optimization
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"

print("Loading environment...", flush=True)

import sys
# Force stdout/stderr to use UTF-8 encoding on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.database import engine
from app.api.auth import router as auth_router
from app.api.face import router as face_router
from app.api.attendance import router as attendance_router, liveness_router
from app.api.faculty import router as faculty_router
from app.api.student import router as students_router, old_router as student_router
from app.api.admin import router as admin_router
from app.config.config import settings

app = FastAPI(
    title="SmartAttend AI",
    description=(
        "Production-ready AI-powered college attendance platform.\n\n"
        "Features: BLE proximity detection, ArcFace face verification (master-embedding system), "
        "DeepFace liveness anti-spoofing, JWT auth with role-based access control, pgvector similarity search."
    ),
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(face_router)
app.include_router(attendance_router)
app.include_router(liveness_router)
app.include_router(faculty_router)
app.include_router(students_router)
app.include_router(student_router)
app.include_router(admin_router)


@app.on_event("startup")
def verify_db_connection():
    """Validate Database connectivity on startup and pre-initialize ArcFace."""
    print("Connecting PostgreSQL...", flush=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connected.", flush=True)
    except Exception as e:
        print(f"[SmartAttend AI] ❌ CRITICAL: Database connection failed: {e}", flush=True)
        raise e

    print("Initializing ArcFace...", flush=True)
    try:
        from app.utils.face_utils import get_face_analysis_app
        get_face_analysis_app()
        print("ArcFace ready.", flush=True)
    except Exception as e:
        print(f"[SmartAttend AI] ❌ WARNING: ArcFace initialization failed: {e}", flush=True)

    print("Starting FastAPI...", flush=True)
    print("Server ready.", flush=True)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def health_check():
    """Health-check endpoint for Render deployment monitoring."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "service": "SmartAttend AI",
        "version": "4.0.0",
        "status": "running",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
