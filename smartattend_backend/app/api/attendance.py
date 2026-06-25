"""
SmartAttend AI — Attendance & Liveness Router

Liveness Endpoints:
  POST /liveness/challenge → generate random challenge + liveness-challenge token
  POST /liveness/verify   → verify challenge frames → issue liveness-success token

Attendance Endpoints:
  POST /attendance/verify  → BLE/QR + liveness token + ArcFace → mark attendance
  POST /attendance/mark    → alias of /verify for backwards compatibility
  GET  /attendance/history → student's own attendance history
  GET  /attendance/session/{id} → all attendance for a session (faculty)
  GET  /attendance/student/{id} → attendance records for a specific student
"""
import uuid
import json
from datetime import datetime, timedelta, date, time as dtime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Student, AttendanceSession, Attendance, LivenessToken, FaceEmbedding
from app.schemas.schemas import (
    LivenessChallengeResponse, LivenessVerifyResponse,
    AttendanceResponse, SessionResponse,
)
from app.dependencies import get_current_student, get_current_faculty
from app.utils.liveness_utils import verify_liveness
from app.utils.face_utils import get_embedding
from app.utils.embedding_utils import batch_cosine_similarities, max_cosine_similarity
from app.config.config import settings

router = APIRouter(prefix="/attendance", tags=["attendance"])
liveness_router = APIRouter(prefix="/liveness", tags=["liveness"])

# ── In-memory rate-limit cache: (student_id, session_id) → attempt count ─────
_rate_cache: dict = {}


# ═════════════════════════════════════════════════════════════════════════════
# LIVENESS ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@liveness_router.post(
    "/challenge",
    response_model=LivenessChallengeResponse,
    summary="Issue a random liveness challenge to the student",
)
def get_liveness_challenge(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns a random challenge type ('blink', 'smile', 'turn_left', 'turn_right')
    and a challenge token valid for LIVENESS_TOKEN_EXPIRY_MINUTES minutes.
    """
    import random
    challenges = ["blink", "turn_left", "turn_right"]
    if not settings.DISABLE_EMOTION_DETECTION:
        challenges.append("smile")
    challenge_type = random.choice(challenges)
    token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=settings.LIVENESS_TOKEN_EXPIRY_MINUTES)

    db.add(LivenessToken(
        student_id=current_student.id,
        token=token_str,
        challenge=challenge_type,
        is_used=False,
        expires_at=expiry,
    ))
    db.commit()

    return LivenessChallengeResponse(token=token_str, challenge=challenge_type, expires_at=expiry)


@liveness_router.post(
    "/verify",
    response_model=LivenessVerifyResponse,
    summary="Submit challenge frames and verify liveness",
)
def verify_liveness_challenge(
    token: str = Form(...),
    files: List[UploadFile] = File(...),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Accepts the challenge token and 10 captured frames.
    Runs DeepFace / OpenCV liveness analysis.
    On success issues a new single-use liveness token valid for 3 minutes.
    """
    token_record = db.query(LivenessToken).filter(
        LivenessToken.token == token,
        LivenessToken.student_id == current_student.id,
    ).first()

    if not token_record:
        raise HTTPException(status_code=400, detail="Challenge token not found")
    if token_record.is_used:
        raise HTTPException(status_code=400, detail="Challenge token already used")
    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Challenge token expired")

    # Consume the challenge token
    token_record.is_used = True
    db.add(token_record)

    frames = [f.file.read() for f in files]
    is_live = verify_liveness(frames, token_record.challenge)

    if not is_live:
        db.commit()
        return LivenessVerifyResponse(verified=False, message="Liveness check failed. Please follow the on-screen instructions carefully.")

    # Issue a fresh liveness-success token
    liveness_token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(minutes=settings.LIVENESS_TOKEN_EXPIRY_MINUTES)

    db.add(LivenessToken(
        student_id=current_student.id,
        token=liveness_token_str,
        challenge=token_record.challenge,
        is_used=False,
        expires_at=expiry,
    ))
    db.commit()

    return LivenessVerifyResponse(
        verified=True,
        liveness_token=liveness_token_str,
        expires_at=expiry,
        message="Liveness verified successfully",
    )


# ═════════════════════════════════════════════════════════════════════════════
# ATTENDANCE ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

def _execute_attendance_marking(
    selfie: UploadFile,
    liveness_token: str,
    classroom_id: Optional[int],
    qr_token: Optional[str],
    session_id: Optional[int],
    current_student: Student,
    db: Session,
) -> dict:
    """
    Core attendance marking logic shared by /verify and /mark endpoints.

    Steps:
      1. Validate & consume liveness token (single-use, 3-min expiry)
      2. Locate the active attendance session
      3. Rate-limit check (max 5 attempts per student per session)
      4. Duplicate attendance check (UNIQUE constraint guard)
      5. Extract ArcFace embedding from selfie
      6. Load all 50 stored embeddings for the student
      7. Vectorised cosine similarity comparison
      8. Apply thresholds (present ≥ 0.75, review ≥ 0.65, else rejected)
      9. Persist attendance record
    """
    # 1. Validate liveness token
    lr = db.query(LivenessToken).filter(
        LivenessToken.token == liveness_token,
        LivenessToken.student_id == current_student.id,
    ).first()
    if not lr:
        raise HTTPException(status_code=400, detail="Liveness token not found")
    if lr.is_used:
        raise HTTPException(status_code=400, detail="Liveness token already used")
    if lr.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Liveness token expired")
    lr.is_used = True
    db.add(lr)

    # 2. Locate active session
    now = datetime.utcnow()
    session = None

    if qr_token:
        session = db.query(AttendanceSession).filter(
            AttendanceSession.qr_token == qr_token,
            AttendanceSession.qr_expires_at > now,
            AttendanceSession.is_active == True,
        ).first()
        if not session:
            # Try legacy session_code field
            session = db.query(AttendanceSession).filter(
                AttendanceSession.session_code == qr_token,
                AttendanceSession.end_time > now,
            ).first()
        if not session:
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid or expired QR session code")
    else:
        if session_id:
            session = db.query(AttendanceSession).filter(
                AttendanceSession.id == session_id
            ).first()
        elif classroom_id:
            session = db.query(AttendanceSession).filter(
                AttendanceSession.classroom_id == classroom_id,
                AttendanceSession.is_active == True,
            ).first()
        if not session:
            session = db.query(AttendanceSession).filter(
                AttendanceSession.is_active == True,
            ).first()
        if not session:
            db.commit()
            raise HTTPException(status_code=404, detail="No active session found")

    # 3. Rate limiting
    rate_key = (current_student.id, session.id)
    attempts = _rate_cache.get(rate_key, 0)
    if attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
        db.commit()
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {settings.MAX_VERIFICATION_ATTEMPTS} verification attempts reached for this session",
        )
    _rate_cache[rate_key] = attempts + 1

    # 4. Duplicate check
    dup = db.query(Attendance).filter(
        Attendance.student_id == current_student.id,
        Attendance.session_id == session.id,
    ).first()
    if dup:
        db.commit()
        raise HTTPException(status_code=400, detail="Attendance already marked for this session")

    # 5. Extract live embedding
    try:
        selfie_bytes = selfie.file.read()
        live_embedding = get_embedding(selfie_bytes)
    except Exception as e:
        db.commit()
        raise HTTPException(status_code=400, detail=f"Face extraction failed: {e}")

    # 6. Load stored embeddings
    stored_rows = db.query(FaceEmbedding).filter(
        FaceEmbedding.student_id == current_student.id
    ).all()

    if not stored_rows:
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="No registered face embeddings found. Please complete face registration first.",
        )

    gallery = [json.loads(r.embedding_json) for r in stored_rows]

    # 7. Vectorised cosine similarity
    sims = batch_cosine_similarities(live_embedding, gallery)
    max_sim = max(sims) if sims else 0.0

    # 8. Threshold classification
    if max_sim >= settings.SIMILARITY_THRESHOLD_PRESENT:
        att_status = "present"
    elif max_sim >= settings.SIMILARITY_THRESHOLD_REVIEW:
        att_status = "manual_review"
    else:
        att_status = "rejected"

    # 9. Persist attendance record
    today = datetime.utcnow().date()
    now_time = datetime.utcnow().time()

    new_att = Attendance(
        student_id=current_student.id,
        session_id=session.id,
        classroom_id=classroom_id or session.classroom_id,
        subject_id=session.subject_id,
        date=today,
        time=now_time,
        similarity_score=max_sim,
        attendance_status=att_status,
        liveness_verified=True,
        marked_at=datetime.utcnow(),
    )
    db.add(new_att)
    db.commit()
    db.refresh(new_att)

    return {
        "status": att_status,
        "similarity_score": round(max_sim, 4),
        "message": f"Attendance recorded with status: {att_status}",
        "marked_at": new_att.marked_at.isoformat(),
        "session_id": session.id,
    }


@router.post("/verify", summary="Mark attendance: liveness + ArcFace face verification")
def verify_attendance(
    selfie: UploadFile = File(...),
    liveness_token: str = Form(...),
    classroom_id: Optional[int] = Form(None),
    qr_token: Optional[str] = Form(None),
    session_id: Optional[int] = Form(None),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return _execute_attendance_marking(
        selfie, liveness_token, classroom_id, qr_token, session_id, current_student, db
    )


@router.post("/mark", summary="Mark attendance (alias of /verify)", include_in_schema=False)
def mark_attendance(
    selfie: UploadFile = File(...),
    liveness_token: str = Form(...),
    classroom_id: Optional[int] = Form(None),
    qr_token: Optional[str] = Form(None),
    session_id: Optional[int] = Form(None),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return _execute_attendance_marking(
        selfie, liveness_token, classroom_id, qr_token, session_id, current_student, db
    )


@router.get(
    "/history",
    response_model=List[AttendanceResponse],
    summary="Get authenticated student's attendance history",
)
def get_attendance_history(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Attendance)
        .filter(Attendance.student_id == current_student.id)
        .order_by(Attendance.marked_at.desc())
        .all()
    )
    return records


@router.get(
    "/session/{session_id}",
    response_model=List[AttendanceResponse],
    summary="Get all attendance records for a session (faculty use)",
)
def get_session_attendance(
    session_id: int,
    current_faculty=Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Attendance)
        .filter(Attendance.session_id == session_id)
        .order_by(Attendance.marked_at.asc())
        .all()
    )
    return records


@router.get(
    "/student/{student_id}",
    response_model=List[AttendanceResponse],
    summary="Get attendance records for a specific student (admin / faculty)",
)
def get_student_attendance(
    student_id: int,
    db: Session = Depends(get_db),
):
    records = (
        db.query(Attendance)
        .filter(Attendance.student_id == student_id)
        .order_by(Attendance.marked_at.desc())
        .all()
    )
    return records


# ── Legacy session management (kept for Flutter backwards compatibility) ──────

@router.post("/start-session", response_model=SessionResponse, include_in_schema=False)
def start_session_legacy(
    subject_name: str = Form(...),
    classroom: str = Form(...),
    session_code: str = Form(...),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    current_faculty=Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    # Close any previously active sessions for this faculty
    db.query(AttendanceSession).filter(
        AttendanceSession.faculty_id == current_faculty.id,
        AttendanceSession.is_active == True,
    ).update({"is_active": False, "end_time": now})

    end_dt = (
        datetime.fromisoformat(end_time)
        if end_time
        else now + timedelta(hours=2)
    )
    start_dt = datetime.fromisoformat(start_time) if start_time else now

    new_session = AttendanceSession(
        faculty_id=current_faculty.id,
        subject_name=subject_name,
        classroom=classroom,
        session_code=session_code,
        start_time=start_dt,
        end_time=end_dt,
        is_active=True,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session
