from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.database import engine
from app.api.auth import router as auth_router
from app.api.face import router as face_router, old_router as old_face_router
from app.api.attendance import router as attendance_router, liveness_router
from app.api.faculty import router as faculty_router
from app.api.student import router as students_router, old_router as student_router
from app.api.admin import router as admin_router
from app.config.config import settings

app = FastAPI(
    title="SmartAttend AI - PostgreSQL Unified API",
    description="FastAPI Backend for Smart Attendance System integrated with Supabase PostgreSQL",
    version="2.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(face_router)
app.include_router(old_face_router)
app.include_router(attendance_router)
app.include_router(liveness_router)
app.include_router(faculty_router)
app.include_router(students_router)
app.include_router(student_router)
app.include_router(admin_router)

@app.on_event("startup")
def verify_db_connection():
    """
    Validates database connectivity to Supabase PostgreSQL on server initialization.
    Raises exception on failure to prevent startup in an unhealthy state.
    """
    print("Testing connection to Supabase PostgreSQL...")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection verified successfully. Supabase PostgreSQL is online.")
    except Exception as e:
        print(f"CRITICAL: Failed to establish database connection on startup: {str(e)}")
        raise e

@app.get("/")
def health_check():
    # Attempt to test connection to return active status
    db_status = "connected"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "status": "running",
        "database": db_status,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
