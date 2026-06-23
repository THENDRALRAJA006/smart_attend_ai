import csv
import io
import uuid
import json
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db, SessionLocal
from app.models.models import Faculty, AttendanceSession, AttendanceRecord, Student
from app.schemas.schemas import SessionCreate, SessionResponse, FacultySchema
from app.dependencies import get_current_faculty
from app.utils.jwt_utils import hash_password

router = APIRouter(prefix="/faculty", tags=["faculty"])

# --- CRUD for Faculty ---
@router.post("", response_model=FacultySchema, status_code=status.HTTP_201_CREATED)
def create_faculty(payload: FacultySchema, db: Session = Depends(get_db)):
    existing = db.query(Faculty).filter(Faculty.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Faculty already registered")
        
    faculty = Faculty(
        name=payload.name,
        employee_id=f"EMP-{uuid.uuid4().hex[:5].upper()}",
        email=payload.email,
        password_hash=hash_password("Faculty@123")
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return FacultySchema(id=faculty.id, name=faculty.name, email=faculty.email)

@router.get("", response_model=List[FacultySchema])
def list_faculty(db: Session = Depends(get_db)):
    faculty_list = db.query(Faculty).all()
    return [FacultySchema(id=f.id, name=f.name, email=f.email) for f in faculty_list]

@router.put("/{id}", response_model=FacultySchema)
def update_faculty(id: int, payload: FacultySchema, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    
    faculty.name = payload.name
    faculty.email = payload.email
    db.commit()
    db.refresh(faculty)
    return FacultySchema(id=faculty.id, name=faculty.name, email=faculty.email)

@router.delete("/{id}")
def delete_faculty(id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty member deleted successfully"}

# --- Session Management (Preserved Functionality) ---
@router.post("/session/create", response_model=SessionResponse)
def create_attendance_session(
    payload: SessionCreate,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    # End any currently active session for this faculty
    now = datetime.utcnow()
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

@router.post("/session/{id}/end", response_model=SessionResponse)
def end_attendance_session(
    id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == id,
        AttendanceSession.faculty_id == current_faculty.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
        
    session.end_time = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/session/active", response_model=SessionResponse)
def get_active_session(
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    session = db.query(AttendanceSession).filter(
        AttendanceSession.faculty_id == current_faculty.id,
        AttendanceSession.start_time <= now,
        AttendanceSession.end_time >= now
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
        
    return session

@router.post("/session/{id}/qr")
def generate_qr_token(
    id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == id,
        AttendanceSession.faculty_id == current_faculty.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
        
    qr_token_str = f"QR-{uuid.uuid4().hex[:8].upper()}"
    session.session_code = qr_token_str
    db.add(session)
    db.commit()
    
    return {
        "qr_token": qr_token_str,
        "expires_at": datetime.utcnow() + timedelta(minutes=1)
    }

@router.post("/attendance/review")
def review_attendance_override(
    attendance_id: int = Form(...),
    approve: bool = Form(...),
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    attendance = db.query(AttendanceRecord).filter(AttendanceRecord.id == attendance_id).first()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance log not found")
        
    session = db.query(AttendanceSession).filter(AttendanceSession.id == attendance.session_id).first()
    if session.faculty_id != current_faculty.id:
        raise HTTPException(status_code=403, detail="Not authorized to review this log")
        
    attendance.status = "present" if approve else "rejected"
    db.add(attendance)
    db.commit()
    
    return {"message": f"Log status updated to {attendance.status}"}

@router.get("/report/{id}")
def download_session_report(
    id: int,
    current_faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == id,
        AttendanceSession.faculty_id == current_faculty.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["SmartAttend AI - PostgreSQL Attendance Report"])
    writer.writerow(["Subject", session.subject_name])
    writer.writerow(["Classroom", session.classroom])
    writer.writerow(["Date", session.start_time.strftime("%Y-%m-%d")])
    writer.writerow([])
    writer.writerow(["Student ID", "Student Name", "Roll Number", "Status", "Verification", "Time"])
    
    for r in records:
        student = db.query(Student).filter(Student.id == r.student_id).first()
        name = student.full_name if student else "N/A"
        roll = student.roll_number if student else "N/A"
        
        writer.writerow([
            r.student_id,
            name,
            roll,
            r.status,
            r.verification_method,
            r.timestamp.strftime("%H:%M:%S")
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=report_session_{id}.csv"
    return response

@router.get("/live/{id}")
def live_attendance_sse(
    id: int,
    current_faculty: Faculty = Depends(get_current_faculty)
):
    def sse_generator():
        last_checked_id = 0
        while True:
            db = SessionLocal()
            try:
                records = db.query(AttendanceRecord).filter(
                    AttendanceRecord.session_id == id,
                    AttendanceRecord.id > last_checked_id
                ).order_by(AttendanceRecord.id.asc()).all()
                
                for r in records:
                    student = db.query(Student).filter(Student.id == r.student_id).first()
                    name = student.full_name if student else "N/A"
                    roll = student.roll_number if student else "N/A"
                    
                    data = {
                        "id": r.id,
                        "student_id": r.student_id,
                        "student_name": name,
                        "roll_no": roll,
                        "time": r.timestamp.strftime("%H:%M:%S"),
                        "similarity_score": r.similarity_score or 0.0,
                        "status": r.status
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    last_checked_id = max(last_checked_id, r.id)
            finally:
                db.close()
            time.sleep(2.0)
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")
