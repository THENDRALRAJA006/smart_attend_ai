import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Student, AttendanceSession, AttendanceRecord, LivenessToken, FaceEmbedding
from app.schemas.schemas import (
    LivenessChallengeResponse,
    LivenessVerifyResponse,
    AttendanceResponse,
    AttendanceMark,
    SessionCreate,
    SessionResponse
)
from app.dependencies import get_current_student, get_current_faculty
from app.utils.liveness_utils import verify_liveness
from app.utils.face_utils import get_embedding
from app.utils.embedding_utils import cosine_similarity
from app.config.config import settings

router = APIRouter(prefix="/attendance", tags=["attendance"])
liveness_router = APIRouter(prefix="/liveness", tags=["liveness"])

# Rate limit cache: (student_id, session_id) -> count
verification_attempts = {}

# --- Liveness Endpoints (Preserved Functionality) ---
@liveness_router.post("/challenge", response_model=LivenessChallengeResponse)
def get_liveness_challenge(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    import random
    challenges = ['blink', 'smile', 'turn_left', 'turn_right']
    challenge_type = random.choice(challenges)
    token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=settings.LIVENESS_TOKEN_EXPIRY_MINUTES)
    
    new_token = LivenessToken(
        student_id=current_student.id,
        token=token_str,
        challenge=challenge_type,
        is_used=False,
        expires_at=expiry
    )
    
    db.add(new_token)
    db.commit()
    
    return LivenessChallengeResponse(
        token=token_str,
        challenge=challenge_type,
        expires_at=expiry
    )

@liveness_router.post("/verify", response_model=LivenessVerifyResponse)
def verify_liveness_challenge(
    token: str = Form(...),
    files: List[UploadFile] = File(...),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    token_record = db.query(LivenessToken).filter(
        LivenessToken.token == token,
        LivenessToken.student_id == current_student.id
    ).first()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Challenge token not found")
        
    if token_record.is_used:
        raise HTTPException(status_code=400, detail="Challenge token already used")
        
    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Challenge token expired")
        
    token_record.is_used = True
    db.add(token_record)
    
    frames = [f.file.read() for f in files]
    is_live = verify_liveness(frames, token_record.challenge)
    
    if not is_live:
        db.commit()
        return LivenessVerifyResponse(
            verified=False,
            message="Liveness check failed. Please follow instructions."
        )
        
    liveness_token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=settings.LIVENESS_TOKEN_EXPIRY_MINUTES)
    
    success_token = LivenessToken(
        student_id=current_student.id,
        token=liveness_token_str,
        challenge=token_record.challenge,
        is_used=False,
        expires_at=expiry
    )
    db.add(success_token)
    db.commit()
    
    return LivenessVerifyResponse(
        verified=True,
        liveness_token=liveness_token_str,
        expires_at=expiry,
        message="Liveness verified successfully"
    )

# --- Attendance Start & End Sessions (New Endpoints) ---
@router.post("/start-session", response_model=SessionResponse)
def start_attendance_session(
    payload: SessionCreate,
    current_faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    # Close previous active sessions for this faculty
    active_sessions = db.query(AttendanceSession).filter(
        AttendanceSession.faculty_id == current_faculty.id,
        AttendanceSession.end_time > now
    ).all()
    for s in active_sessions:
        s.end_time = now
        db.add(s)
        
    new_session = AttendanceSession(
        faculty_id=current_faculty.id,
        subject_name=payload.subject_name,
        classroom=payload.classroom,
        session_code=payload.session_code,
        start_time=payload.start_time,
        end_time=payload.end_time
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.post("/end-session", response_model=SessionResponse)
def end_session_endpoint(
    session_id: int = Form(...),
    current_faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == session_id,
        AttendanceSession.faculty_id == current_faculty.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
        
    session.end_time = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

# --- Attendance History ---
@router.get("/history", response_model=List[AttendanceResponse])
def get_attendance_history(
    student_id: Optional[int] = None,
    current_student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    target_student_id = student_id if student_id else current_student.id
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == target_student_id
    ).order_by(AttendanceRecord.timestamp.desc()).all()
    return records

# --- Attendance Marking Helper Core ---
def execute_attendance_marking(
    selfie: UploadFile,
    liveness_token: str,
    classroom_id: Optional[int],
    qr_token: Optional[str],
    session_id: Optional[int],
    current_student: Student,
    db: Session
):
    # 1. Validate liveness token
    liveness_record = db.query(LivenessToken).filter(
        LivenessToken.token == liveness_token,
        LivenessToken.student_id == current_student.id
    ).first()
    
    if not liveness_record:
        raise HTTPException(status_code=400, detail="Liveness token not found")
    if liveness_record.is_used:
        raise HTTPException(status_code=400, detail="Liveness token already used")
    if liveness_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Liveness token expired")
        
    liveness_record.is_used = True
    db.add(liveness_record)
    
    # 2. Locate active session
    session = None
    if qr_token:
        session = db.query(AttendanceSession).filter(
            AttendanceSession.session_code == qr_token,
            AttendanceSession.start_time <= datetime.utcnow(),
            AttendanceSession.end_time >= datetime.utcnow()
        ).first()
        if not session:
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid or expired QR session code")
    else:
        if session_id:
            session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
        elif classroom_id:
            session = db.query(AttendanceSession).filter(
                AttendanceSession.classroom == f"ROOM{classroom_id}",
                AttendanceSession.start_time <= datetime.utcnow(),
                AttendanceSession.end_time >= datetime.utcnow()
            ).first()
            if not session:
                session = db.query(AttendanceSession).filter(
                    AttendanceSession.start_time <= datetime.utcnow(),
                    AttendanceSession.end_time >= datetime.utcnow()
                ).first()
                
        if not session:
            db.commit()
            raise HTTPException(status_code=404, detail="No active session found")

    # 3. Rate limiting (max 5 attempts)
    rate_key = (current_student.id, session.id)
    attempts = verification_attempts.get(rate_key, 0)
    if attempts >= 5:
        db.commit()
        raise HTTPException(status_code=429, detail="Verification attempts exceeded")
    verification_attempts[rate_key] = attempts + 1
    
    # 4. Check for duplicate logs
    dup = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == current_student.id,
        AttendanceRecord.session_id == session.id
    ).first()
    if dup:
        db.commit()
        raise HTTPException(status_code=400, detail="Attendance already marked for this session")

    # 5. Extract face embedding
    try:
        selfie_bytes = selfie.file.read()
        live_embedding = get_embedding(selfie_bytes)
    except Exception as e:
        db.commit()
        raise HTTPException(status_code=400, detail=f"Face extraction failed: {str(e)}")

    # 6. Load stored embeddings
    stored_embeddings = []
    # Fetch from FaceEmbedding model (new setup)
    db_embeddings = db.query(Student).filter(Student.id == current_student.id).first().face_embeddings
    if db_embeddings:
        # Compatibility array from students table
        stored_embeddings = db_embeddings
    
    # Also fetch from new FaceEmbedding table if available
    db_embeddings_list = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == current_student.id).all()
    for item in db_embeddings_list:
        stored_embeddings.append(item.embedding)

    if not stored_embeddings or len(stored_embeddings) == 0:
        db.commit()
        raise HTTPException(status_code=400, detail="Student has no registered face embeddings")
        
    # 7. Compare embeddings
    similarities = [cosine_similarity(live_embedding, emb) for emb in stored_embeddings]
    max_sim = max(similarities) if similarities else 0.0
    
    # 8. Apply thresholds
    if max_sim >= settings.SIMILARITY_THRESHOLD_PRESENT:
        status_marked = "present"
    elif max_sim >= settings.SIMILARITY_THRESHOLD_REVIEW:
        status_marked = "manual_review"
    else:
        status_marked = "rejected"
        
    # 9. Store attendance record
    new_attendance = AttendanceRecord(
        student_id=current_student.id,
        session_id=session.id,
        status=status_marked,
        verification_method="face",
        similarity_score=max_sim,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return {
        "status": status_marked,
        "similarity_score": max_sim,
        "message": f"Attendance registered with status: {status_marked}",
        "marked_at": new_attendance.timestamp
    }

# --- Handlers mapped to both Flutter (verify) and SQL (mark) paths ---
@router.post("/mark")
def mark_attendance_endpoint(
    selfie: UploadFile = File(...),
    liveness_token: str = Form(...),
    classroom_id: Optional[int] = Form(None),
    qr_token: Optional[str] = Form(None),
    session_id: Optional[int] = Form(None),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return execute_attendance_marking(selfie, liveness_token, classroom_id, qr_token, session_id, current_student, db)

@router.post("/verify")
def verify_attendance_endpoint(
    selfie: UploadFile = File(...),
    liveness_token: str = Form(...),
    classroom_id: Optional[int] = Form(None),
    qr_token: Optional[str] = Form(None),
    session_id: Optional[int] = Form(None),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return execute_attendance_marking(selfie, liveness_token, classroom_id, qr_token, session_id, current_student, db)

@router.get("/student/{student_id}", response_model=List[AttendanceResponse])
def get_student_attendance_by_id(
    student_id: int,
    db: Session = Depends(get_db)
):
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student_id
    ).order_by(AttendanceRecord.timestamp.desc()).all()
    return records

@router.get("/session/{session_id}", response_model=List[AttendanceResponse])
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db)
):
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id
    ).order_by(AttendanceRecord.timestamp.asc()).all()
    return records
