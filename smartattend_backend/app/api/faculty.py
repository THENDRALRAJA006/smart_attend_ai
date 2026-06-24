"""
SmartAttend AI — Faculty Router

Endpoints:
  POST /faculty/session/create        → create attendance session
  POST /faculty/session/{id}/end      → end a session
  GET  /faculty/session/active        → get current active session
  POST /faculty/session/{id}/qr       → generate QR token
  POST /faculty/attendance/review     → approve/reject manual_review records
  GET  /faculty/report/{id}           → download CSV attendance report
  GET  /faculty/live/{id}             → SSE stream of live attendance updates
  CRUD /faculty  (admin-facing CRUD)
"""
import csv
import io
import uuid
import json
import time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.database.database import get_db, SessionLocal
from app.models.models import Faculty, AttendanceSession, Attendance, Student, Subject, Classroom
from app.schemas.schemas import SessionCreate, SessionResponse, FacultySchema, FacultyRegister
from app.dependencies import get_current_faculty
from app.utils.jwt_utils import hash_password

router = APIRouter(prefix="/faculty", tags=["faculty"])


# ── Faculty CRUD (used by admin panel) ───────────────────────────────────────

@router.get("", response_model=List[FacultySchema])
def list_faculty(db: Session = Depends(get_db)):
    faculty_list = db.query(Faculty).all()
    return [FacultySchema(id=f.id, name=f.name or "", email=f.email, department=f.department) for f in faculty_list]


@router.post("", response_model=FacultySchema, status_code=status.HTTP_201_CREATED)
def create_faculty(payload: FacultySchema, db: Session = Depends(get_db)):
    if db.query(Faculty).filter(Faculty.email == str(payload.email)).first():
        raise HTTPException(status_code=400, detail="Faculty already registered with this email")
    faculty = Faculty(
        name=payload.name,
        email=str(payload.email),
        password_hash=hash_password("Faculty@123"),
        department=payload.department,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return FacultySchema(id=faculty.id, name=faculty.name or "", email=faculty.email, department=faculty.department)


@router.put("/{faculty_id}", response_model=FacultySchema)
def update_faculty(faculty_id: int, payload: FacultySchema, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    faculty.name = payload.name
    faculty.email = str(payload.email)
    faculty.department = payload.department
    db.commit()
    db.refresh(faculty)
    return FacultySchema(id=faculty.id, name=faculty.name or "", email=faculty.email, department=faculty.department)


@router.delete("/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty member deleted successfully"}


# ── Session Management ────────────────────────────────────────────────────────

@router.post("/session/create", response_model=SessionResponse, summary="Create a new attendance session")
def create_attendance_session(
    payload: SessionCreate,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    """
    Creates a new attendance session and ends any currently active session for this faculty.
    Accepts both simple (subject_name + classroom string) and relational (subject_id + classroom_id).
    """
    now = datetime.utcnow()

    # End previous active sessions for this faculty
    db.query(AttendanceSession).filter(
        AttendanceSession.faculty_id == current_faculty.id,
        AttendanceSession.is_active == True,
    ).update({"is_active": False, "end_time": now})

    subject_name = payload.subject_name
    classroom = payload.classroom
    session_code = payload.session_code
    start_time = payload.start_time or now
    end_time = payload.end_time or (start_time + timedelta(hours=1))

    # Resolve from relational IDs if strings not provided
    if payload.subject_id and not subject_name:
        from app.models.models import Subject
        subj = db.query(Subject).filter(Subject.id == payload.subject_id).first()
        if subj:
            subject_name = subj.subject_name

    if payload.classroom_id and not classroom:
        from app.models.models import Classroom
        cls = db.query(Classroom).filter(Classroom.id == payload.classroom_id).first()
        if cls:
            classroom = cls.room_name

    if not subject_name:
        subject_name = "Class Session"
    if not classroom:
        classroom = "Standard Classroom"

    if not session_code:
        import uuid
        session_code = f"SESS-{uuid.uuid4().hex[:8].upper()}"

    new_session = AttendanceSession(
        faculty_id=current_faculty.id,
        subject_name=subject_name,
        classroom=classroom,
        session_code=session_code,
        subject_id=payload.subject_id,
        classroom_id=payload.classroom_id,
        start_time=start_time,
        end_time=end_time,
        is_active=True,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.post("/session/{session_id}/end", response_model=SessionResponse, summary="End an active session")
def end_attendance_session(
    session_id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == session_id,
        AttendanceSession.faculty_id == current_faculty.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by you")

    session.is_active = False
    session.end_time = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.get("/session/active", response_model=SessionResponse, summary="Get current active session")
def get_active_session(
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.faculty_id == current_faculty.id,
        AttendanceSession.is_active == True,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    return session


@router.post("/session/{session_id}/qr", summary="Generate a QR token for a session")
def generate_qr_token(
    session_id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    """
    Generates a new QR token for the session (valid 10 minutes).
    Overwrites any existing QR token for this session.
    """
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == session_id,
        AttendanceSession.faculty_id == current_faculty.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by you")

    qr_token = f"SA-{uuid.uuid4().hex[:12].upper()}"
    qr_expires = datetime.utcnow() + timedelta(minutes=10)

    session.qr_token = qr_token
    session.qr_expires_at = qr_expires
    # Also update legacy field
    session.session_code = qr_token
    db.commit()

    return {
        "qr_token": qr_token,
        "session_id": session_id,
        "expires_at": qr_expires.isoformat(),
        "payload": {
            "session_id": session_id,
            "qr_token": qr_token,
            "expires_at": qr_expires.isoformat(),
        },
    }


# ── Manual Review ─────────────────────────────────────────────────────────────

@router.post("/attendance/review", summary="Approve or reject a manual_review attendance record")
def review_attendance_override(
    attendance_id: int = Form(...),
    approve: bool = Form(...),
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    att = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    session = db.query(AttendanceSession).filter(AttendanceSession.id == att.session_id).first()
    if not session or session.faculty_id != current_faculty.id:
        raise HTTPException(status_code=403, detail="Not authorised to review this record")

    att.attendance_status = "present" if approve else "rejected"
    db.commit()
    return {"message": f"Record updated to '{att.attendance_status}'"}


# ── CSV Report Download ────────────────────────────────────────────────────────

@router.get("/report/{session_id}", summary="Download session attendance as CSV")
def download_session_report(
    session_id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db),
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == session_id,
        AttendanceSession.faculty_id == current_faculty.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not owned by you")

    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["SmartAttend AI — Attendance Report"])
    writer.writerow(["Subject", session.subject_name or "N/A"])
    writer.writerow(["Classroom", session.classroom or "N/A"])
    writer.writerow(["Date", session.start_time.strftime("%Y-%m-%d")])
    writer.writerow(["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")])
    writer.writerow([])
    writer.writerow(["#", "Student ID", "Name", "Roll No", "Status", "Similarity Score", "Liveness", "Time"])

    for idx, r in enumerate(records, 1):
        student = db.query(Student).filter(Student.id == r.student_id).first()
        name = student.name if student else "N/A"
        roll = student.roll_no if student else "N/A"
        writer.writerow([
            idx,
            r.student_id,
            name,
            roll,
            r.attendance_status,
            f"{r.similarity_score:.4f}" if r.similarity_score else "N/A",
            "Yes" if r.liveness_verified else "No",
            r.marked_at.strftime("%H:%M:%S"),
        ])

    content = buf.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=session_{session_id}_report.csv"
        },
    )


# ── SSE Live Attendance Stream ─────────────────────────────────────────────────

@router.get("/live/{session_id}", summary="SSE stream of real-time attendance for a session")
def live_attendance_sse(
    session_id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
):
    """
    Server-Sent Events stream. Polls the database every 2 seconds and emits
    new attendance records as they are added.
    """
    def sse_generator():
        last_id = 0
        while True:
            db = SessionLocal()
            payloads = []
            try:
                records = (
                    db.query(Attendance)
                    .filter(
                        Attendance.session_id == session_id,
                        Attendance.id > last_id,
                    )
                    .order_by(Attendance.id.asc())
                    .all()
                )
                for r in records:
                    student = db.query(Student).filter(Student.id == r.student_id).first()
                    payloads.append({
                        "id": r.id,
                        "student_id": r.student_id,
                        "student_name": student.name if student else "N/A",
                        "roll_no": student.roll_no if student else "N/A",
                        "status": r.attendance_status,
                        "similarity_score": round(r.similarity_score or 0.0, 4),
                        "liveness_verified": r.liveness_verified,
                        "time": r.marked_at.strftime("%H:%M:%S"),
                    })
                    last_id = max(last_id, r.id)
            finally:
                db.close()

            for payload in payloads:
                yield f"data: {json.dumps(payload)}\n\n"
                
            time.sleep(2.0)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
