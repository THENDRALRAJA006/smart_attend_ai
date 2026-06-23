from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid
from datetime import datetime

from app.database.database import get_db
from app.models.models import Student, Faculty, AttendanceSession, AttendanceRecord, Classroom, BleBeacon
from app.schemas.schemas import StudentSchema, FacultySchema, ClassroomSchema, BeaconSchema, AnalyticsResponse
from app.dependencies import get_current_faculty
from app.utils.jwt_utils import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Students CRUD ---
@router.get("/students")
def list_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return [
        {
            "id": s.id,
            "name": s.full_name,
            "roll_no": s.roll_number,
            "department": s.department,
            "year": s.year,
            "section": s.section,
            "email": s.email,
            "is_face_registered": s.face_embeddings is not None and len(s.face_embeddings) > 0
        }
        for s in students
    ]

@router.post("/students")
def create_student(payload: StudentSchema, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.roll_number == payload.roll_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")
        
    student = Student(
        full_name=payload.name,
        roll_number=payload.roll_no,
        department=payload.department,
        year=payload.year,
        section=payload.section,
        email=payload.email,
        password_hash=hash_password("Student@123")
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return payload

@router.delete("/students/{id}")
def delete_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}

# --- Faculty CRUD ---
@router.get("/faculty")
def list_faculty(db: Session = Depends(get_db)):
    faculty = db.query(Faculty).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "email": f.email,
            "department": "Computer Science"
        }
        for f in faculty
    ]

@router.post("/faculty")
def create_faculty(payload: FacultySchema, db: Session = Depends(get_db)):
    existing = db.query(Faculty).filter(Faculty.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Faculty already exists")
        
    faculty = Faculty(
        name=payload.name,
        employee_id=f"EMP-{uuid.uuid4().hex[:5].upper()}",
        email=payload.email,
        password_hash=hash_password("Faculty@123")
    )
    db.add(faculty)
    db.commit()
    return payload

@router.delete("/faculty/{id}")
def delete_faculty(id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty member deleted"}

# --- Classrooms CRUD ---
@router.get("/classrooms", response_model=List[ClassroomSchema])
def list_classrooms(db: Session = Depends(get_db)):
    return db.query(Classroom).all()

@router.post("/classrooms", response_model=ClassroomSchema)
def create_classroom(payload: ClassroomSchema, db: Session = Depends(get_db)):
    existing = db.query(Classroom).filter(Classroom.room_name == payload.room_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Classroom already exists")
    room = Classroom(
        room_name=payload.room_name,
        building=payload.building,
        capacity=payload.capacity
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

@router.delete("/classrooms/{id}")
def delete_classroom(id: int, db: Session = Depends(get_db)):
    room = db.query(Classroom).filter(Classroom.id == id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Classroom not found")
    db.delete(room)
    db.commit()
    return {"message": "Classroom deleted"}

# --- Beacons CRUD ---
@router.get("/beacons", response_model=List[BeaconSchema])
def list_beacons(db: Session = Depends(get_db)):
    return db.query(BleBeacon).all()

@router.post("/beacons", response_model=BeaconSchema)
def create_beacon(payload: BeaconSchema, db: Session = Depends(get_db)):
    existing = db.query(BleBeacon).filter(BleBeacon.uuid == payload.uuid).first()
    if existing:
        raise HTTPException(status_code=400, detail="Beacon already exists")
    beacon = BleBeacon(
        classroom_id=payload.classroom_id,
        uuid=payload.uuid,
        device_name=payload.device_name,
        rssi_threshold=payload.rssi_threshold,
        is_active=payload.is_active
    )
    db.add(beacon)
    db.commit()
    db.refresh(beacon)
    return beacon

@router.delete("/beacons/{id}")
def delete_beacon(id: int, db: Session = Depends(get_db)):
    beacon = db.query(BleBeacon).filter(BleBeacon.id == id).first()
    if not beacon:
        raise HTTPException(status_code=404, detail="Beacon not found")
    db.delete(beacon)
    db.commit()
    return {"message": "Beacon deleted"}

# --- Analytics ---
@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    students_count = db.query(Student).count()
    faculty_count = db.query(Faculty).count()
    classrooms_count = db.query(Classroom).count()
    
    now = datetime.utcnow()
    active_sessions = db.query(AttendanceSession).filter(
        AttendanceSession.start_time <= now,
        AttendanceSession.end_time >= now
    ).count()

    total_marked = db.query(AttendanceRecord).count()
    present_marked = db.query(AttendanceRecord).filter(AttendanceRecord.status == "present").count()
    rate = 0.0
    if total_marked > 0:
        rate = float(present_marked / total_marked) * 100.0

    return AnalyticsResponse(
        total_students=students_count,
        total_faculty=faculty_count,
        total_classrooms=classrooms_count,
        active_sessions=active_sessions,
        attendance_rate=round(rate, 2)
    )
