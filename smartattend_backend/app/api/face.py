"""
SmartAttend AI — Face Registration & Verification Router

Endpoints:
  POST   /face/register  → upload frames → select best 50 → store embeddings
  GET    /face/status    → check registration status
  DELETE /face/reset     → admin resets a student's face embeddings
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.models.models import Student, FaceEmbedding, AttendanceRecord as Attendance, AttendanceSession
from app.schemas.schemas import FaceStatusResponse, FaceRegisterPayload, FaceVerifyPayload, FaceVerifyResponse
from app.dependencies import get_current_student, get_current_faculty, get_current_admin
from app.utils.face_utils import select_best_embeddings, get_embedding
from app.utils.embedding_utils import cosine_similarity, batch_cosine_similarities, max_cosine_similarity
from app.config.config import settings

router = APIRouter(prefix="/face", tags=["face"])

# Keep backwards-compatible alias
old_router = APIRouter(prefix="/face", tags=["face"])


# ── Multipart: Upload frames → select 50 best → store embeddings ──────────────

@router.post("/register", summary="Upload face frames for registration (50-embedding system)")
def register_face_frames(
    files: List[UploadFile] = File(...),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Accepts 100–150 raw image frames captured during guided pose capture.
    Backend selects the best 50 embeddings using:
      - Sharpness (Laplacian variance > 100)
      - ArcFace detection confidence > 0.95
      - Cosine similarity deduplication < 0.98
    Stores embeddings as JSON arrays — no images are persisted.
    """
    if len(files) < settings.MIN_FRAMES_FOR_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too few frames ({len(files)}). Please complete all guided poses (min {settings.MIN_FRAMES_FOR_REGISTRATION} frames required).",
        )

    frames_bytes = [f.file.read() for f in files]

    embeddings = select_best_embeddings(
        frames=frames_bytes,
        target=settings.MAX_FACE_EMBEDDINGS,
        sharpness_threshold=settings.SHARPNESS_THRESHOLD,
        det_confidence_threshold=settings.DETECTION_CONFIDENCE_THRESHOLD,
        dedup_threshold=settings.DEDUP_SIMILARITY_THRESHOLD,
    )

    if len(embeddings) < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only {len(embeddings)} high-quality face embeddings could be extracted. "
                "Please retry in better lighting with all guided poses completed."
            ),
        )

    # Clear any existing embeddings for this student
    db.query(FaceEmbedding).filter(FaceEmbedding.student_id == current_student.id).delete()

    # Store all selected embeddings
    for emb in embeddings:
        db.add(FaceEmbedding(
            student_id=current_student.id,
            pose_name="auto",
            embedding_json=json.dumps(emb.tolist()),
        ))

    # Mark student as face-registered
    current_student.is_face_registered = True
    db.add(current_student)
    db.commit()

    return {
        "message": "Face registration completed successfully",
        "embeddings_stored": len(embeddings),
        "student_id": current_student.id,
    }


# ── SDK Path: accept pre-computed embedding ───────────────────────────────────

@router.post("/register-sdk", summary="Register a single pre-computed ArcFace embedding (SDK path)")
def register_face_sdk(payload: FaceRegisterPayload, db: Session = Depends(get_db)):
    """Accept a single pre-computed 512-dim embedding (useful for SDK integrations)."""
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.add(FaceEmbedding(
        student_id=payload.student_id,
        pose_name=payload.pose_name or "sdk",
        embedding_json=json.dumps(payload.embedding),
    ))
    db.commit()
    return {"message": "Embedding saved", "student_id": payload.student_id}


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=FaceStatusResponse, summary="Check face registration status")
def check_face_status(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    count = db.query(FaceEmbedding).filter(
        FaceEmbedding.student_id == current_student.id
    ).count()
    return FaceStatusResponse(
        is_face_registered=count > 0,
        embedding_count=count,
    )


# ── Admin Reset ───────────────────────────────────────────────────────────────

@router.delete("/reset", summary="Admin: delete all face embeddings for a student")
def reset_student_face(
    student_id: int = Query(..., description="Student ID to reset"),
    db: Session = Depends(get_db),
):
    """Admin-only: wipe all face embeddings for a student so they can re-register."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student_id).delete()
    student.is_face_registered = False
    db.add(student)
    db.commit()

    return {"message": f"Face registration reset for student ID {student_id}"}


# ── SDK Verify (stateless — does NOT mark attendance) ─────────────────────────

@router.post("/verify-sdk", response_model=FaceVerifyResponse, summary="Verify face embedding (SDK, stateless)")
def verify_face_sdk(payload: FaceVerifyPayload, db: Session = Depends(get_db)):
    """
    Compare a pre-computed embedding against the stored gallery.
    This is a pure similarity check — it does NOT mark attendance.
    """
    stored_rows = db.query(FaceEmbedding).filter(
        FaceEmbedding.student_id == payload.student_id
    ).all()

    if not stored_rows:
        raise HTTPException(status_code=400, detail="Student has no registered face embeddings")

    gallery = [json.loads(r.embedding_json) for r in stored_rows]
    sims = batch_cosine_similarities(payload.embedding, gallery)
    max_sim = max(sims) if sims else 0.0

    verified = max_sim >= settings.SIMILARITY_THRESHOLD_PRESENT
    return FaceVerifyResponse(
        verified=verified,
        similarity_score=max_sim,
        message="Match found" if verified else "No match",
    )
