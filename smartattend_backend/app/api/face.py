"""
SmartAttend AI — Face Registration & Verification Router

Master-embedding architecture:
  POST   /face/register     → upload frames → generate ONE master embedding
  POST   /face/register-sdk → accept pre-computed embedding as master
  GET    /face/status       → check registration status
  DELETE /face/reset        → admin resets a student's face embedding
  POST   /face/verify-sdk   → verify a pre-computed embedding (stateless)
"""
import logging
from datetime import datetime
from typing import List

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Student
from app.schemas.schemas import (
    FaceStatusResponse, FaceRegisterPayload, FaceVerifyPayload, FaceVerifyResponse,
)
from app.dependencies import get_current_student
from app.services.embedding_service import get_embedding_service
from app.utils.embedding_utils import cosine_similarity
from app.config.config import settings

logger = logging.getLogger("smartattend.face")

router = APIRouter(prefix="/face", tags=["face"])

# Keep backwards-compatible alias
old_router = APIRouter(prefix="/face", tags=["face"])


# ── Multipart: Upload frames → generate ONE master embedding ──────────────────

@router.post("/register", summary="Upload face frames for registration (master-embedding system)")
def register_face_frames(
    files: List[UploadFile] = File(...),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Accepts 100–150 raw image frames captured during guided pose capture.
    Backend pipeline:
      1. Quality filtering (blur, brightness, face size, angle, confidence)
      2. ArcFace embedding extraction (one-by-one for memory efficiency)
      3. Outlier removal
      4. Deduplication
      5. Generate ONE L2-normalised master embedding
    Stores the master embedding directly on the student record.
    No images are persisted.
    """
    if len(files) < settings.MIN_FRAMES_FOR_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Too few frames ({len(files)}). Please complete all guided "
                f"poses (min {settings.MIN_FRAMES_FOR_REGISTRATION} frames required)."
            ),
        )

    # Read frame bytes one-by-one to avoid loading all into memory at once
    frames_bytes: List[bytes] = []
    for f in files:
        frames_bytes.append(f.file.read())
        f.file.close()

    # Generate master embedding via the pipeline
    service = get_embedding_service()
    try:
        result = service.generate_master_embedding(
            frames=frames_bytes,
            sharpness_threshold=settings.SHARPNESS_THRESHOLD,
            det_confidence_threshold=settings.DETECTION_CONFIDENCE_THRESHOLD,
            dedup_threshold=settings.DEDUP_SIMILARITY_THRESHOLD,
            min_valid=settings.MIN_VALID_EMBEDDINGS,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Store the master embedding directly on the student record
    current_student.master_embedding = result.master_embedding.tolist()
    current_student.embedding_version = settings.EMBEDDING_VERSION
    current_student.embedding_quality_score = result.quality_score
    current_student.embedding_updated_at = datetime.utcnow()
    current_student.is_face_registered = True
    db.add(current_student)
    db.commit()

    logger.info(
        "Student %d registered: quality=%.4f, %d/%d frames used",
        current_student.id,
        result.quality_score,
        result.valid_count,
        result.total_processed,
    )

    return {
        "message": "Face registration completed successfully",
        "embeddings_stored": 1,
        "student_id": current_student.id,
        "quality_score": round(result.quality_score, 4),
        "frames_used": result.valid_count,
        "frames_rejected": result.rejected_count,
    }


# ── SDK Path: accept pre-computed embedding ───────────────────────────────────

@router.post("/register-sdk", summary="Register a single pre-computed ArcFace embedding (SDK path)")
def register_face_sdk(payload: FaceRegisterPayload, db: Session = Depends(get_db)):
    """Accept a single pre-computed 512-dim embedding as the master embedding."""
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Validate embedding dimension
    if len(payload.embedding) != 512:
        raise HTTPException(
            status_code=400,
            detail=f"Embedding must be 512-dimensional, got {len(payload.embedding)}",
        )

    # L2-normalise the incoming embedding
    emb = np.array(payload.embedding, dtype=np.float32)
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm

    student.master_embedding = emb.tolist()
    student.embedding_version = settings.EMBEDDING_VERSION
    student.embedding_quality_score = 1.0  # SDK path assumes pre-validated
    student.embedding_updated_at = datetime.utcnow()
    student.is_face_registered = True
    db.add(student)
    db.commit()

    return {"message": "Embedding saved", "student_id": payload.student_id}


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=FaceStatusResponse, summary="Check face registration status")
def check_face_status(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    has_embedding = current_student.master_embedding is not None
    return FaceStatusResponse(
        is_face_registered=has_embedding,
        embedding_count=1 if has_embedding else 0,
        quality_score=current_student.embedding_quality_score,
        embedding_version=current_student.embedding_version,
    )


# ── Admin Reset ───────────────────────────────────────────────────────────────

@router.delete("/reset", summary="Admin: delete face embedding for a student")
def reset_student_face(
    student_id: int = Query(..., description="Student ID to reset"),
    db: Session = Depends(get_db),
):
    """Admin-only: wipe the master embedding for a student so they can re-register."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.master_embedding = None
    student.embedding_version = None
    student.embedding_quality_score = None
    student.embedding_updated_at = None
    student.is_face_registered = False
    db.add(student)
    db.commit()

    return {"message": f"Face registration reset for student ID {student_id}"}


# ── SDK Verify (stateless — does NOT mark attendance) ─────────────────────────

@router.post("/verify-sdk", response_model=FaceVerifyResponse, summary="Verify face embedding (SDK, stateless)")
def verify_face_sdk(payload: FaceVerifyPayload, db: Session = Depends(get_db)):
    """
    Compare a pre-computed embedding against the stored master embedding.
    This is a pure similarity check — it does NOT mark attendance.
    """
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.master_embedding is None:
        raise HTTPException(status_code=400, detail="Student has no registered face embedding")

    # Single cosine similarity against the master embedding
    similarity = cosine_similarity(
        payload.embedding,
        np.array(student.master_embedding, dtype=np.float32),
    )

    verified = similarity >= settings.SIMILARITY_THRESHOLD_PRESENT
    return FaceVerifyResponse(
        verified=verified,
        similarity_score=similarity,
        message="Match found" if verified else "No match",
    )
