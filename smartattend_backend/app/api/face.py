import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.models.models import Student, Faculty, FaceEmbedding, AttendanceRecord, AttendanceSession
from app.schemas.schemas import FaceStatusResponse, FaceRegisterPayload, FaceVerifyPayload, FaceVerifyResponse
from app.dependencies import get_current_student, get_current_faculty
from app.utils.face_utils import select_best_embeddings
from app.utils.embedding_utils import cosine_similarity
from app.config.config import settings

router = APIRouter(tags=["face"])

# Support /face prefix as backwards compatibility aliases
old_router = APIRouter(prefix="/face", tags=["face"])

@router.post("/register-face")
def register_face_sdk(payload: FaceRegisterPayload, db: Session = Depends(get_db)):
    """
    Registers a face embedding vector for a student.
    Accepts student_id and float embedding vector, saving it in the database.
    """
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Save in FaceEmbedding table
    db_emb = FaceEmbedding(
        student_id=payload.student_id,
        embedding=payload.embedding
    )
    db.add(db_emb)
    
    # Re-sync / add to Student JSON embeddings list for compatibility
    if not student.face_embeddings:
        student.face_embeddings = []
    
    student.face_embeddings.append(payload.embedding)
    db.add(student)
    
    db.commit()
    return {"message": "Embedding saved successfully", "student_id": payload.student_id}

@router.post("/verify-face", response_model=FaceVerifyResponse)
def verify_face_sdk(payload: FaceVerifyPayload, db: Session = Depends(get_db)):
    """
    Verifies a face embedding against registered embeddings for the student,
    marks attendance if matched.
    """
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Query active session
    session = db.query(AttendanceSession).filter(AttendanceSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Check duplicate
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == payload.student_id,
        AttendanceRecord.session_id == payload.session_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this session")

    # Load stored embeddings
    stored_embeddings = []
    # From JSON
    if student.face_embeddings:
        stored_embeddings.extend(student.face_embeddings)
    # From FaceEmbedding table
    db_embs = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == payload.student_id).all()
    for item in db_embs:
        stored_embeddings.append(item.embedding)

    if not stored_embeddings:
        raise HTTPException(status_code=400, detail="Student has no registered face embeddings")
        
    # Compare
    similarities = [cosine_similarity(payload.embedding, emb) for emb in stored_embeddings]
    max_sim = max(similarities) if similarities else 0.0
    
    verified = max_sim >= settings.SIMILARITY_THRESHOLD_PRESENT
    status_marked = "present" if verified else "rejected"
    
    attendance_dict = None
    if verified:
        # Mark attendance
        record = AttendanceRecord(
            student_id=payload.student_id,
            session_id=payload.session_id,
            status=status_marked,
            verification_method=payload.verification_method,
            similarity_score=max_sim,
            timestamp=datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        attendance_dict = {
            "id": record.id,
            "student_id": record.student_id,
            "session_id": record.session_id,
            "status": record.status,
            "verification_method": record.verification_method,
            "similarity_score": record.similarity_score,
            "timestamp": record.timestamp.isoformat()
        }
        
    return FaceVerifyResponse(
        verified=verified,
        similarity_score=max_sim,
        message="Face verified successfully and attendance marked" if verified else "Verification failed: low similarity score",
        attendance_record=attendance_dict
    )

# --- Backwards compatibility /face/... Endpoints ---
@old_router.post("/register")
def register_face_endpoint(
    files: List[UploadFile] = File(...),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    if len(files) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too few frames uploaded ({len(files)}). Please record guided poses."
        )
        
    frames_bytes = [f.file.read() for f in files]
    embeddings = select_best_embeddings(frames_bytes, target=50)
    
    if len(embeddings) < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract enough high-quality facial embeddings."
        )
        
    embeddings_list = [emb.tolist() for emb in embeddings]
    current_student.face_embeddings = embeddings_list
    
    # Also save each in the FaceEmbedding table
    for emb in embeddings_list:
        db.add(FaceEmbedding(student_id=current_student.id, embedding=emb))
        
    db.add(current_student)
    db.commit()
    
    return {
        "message": "Face registration completed successfully",
        "embeddings_count": len(embeddings)
    }

@old_router.get("/status", response_model=FaceStatusResponse)
def check_face_status(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    is_registered = current_student.face_embeddings is not None and len(current_student.face_embeddings) > 0
    count = len(current_student.face_embeddings) if is_registered else 0
    return FaceStatusResponse(
        is_face_registered=is_registered,
        embedding_count=count
    )

@old_router.delete("/reset")
def reset_student_face(
    student_id: int = Query(..., description="ID of the student to reset"),
    current_faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    student.face_embeddings = None
    # Delete from FaceEmbedding table too
    db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student_id).delete()
    db.add(student)
    db.commit()
    
    return {"message": f"Face registration reset successfully for student ID {student_id}"}
