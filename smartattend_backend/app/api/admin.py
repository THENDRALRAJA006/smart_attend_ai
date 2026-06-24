"""
SmartAttend AI — Admin Router

Full CRUD for:
  /admin/students
  /admin/faculty
  /admin/subjects
  /admin/classrooms
  /admin/beacons
  /admin/analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid
from datetime import datetime

from app.database.database import get_db
from app.models.models import (
    Student, Faculty, Admin, Subject, Classroom, BleBeacon,
    AttendanceSession, Attendance, FaceEmbedding,
)
from app.schemas.schemas import (
    StudentSchema, FacultySchema, SubjectSchema, ClassroomSchema,
    BeaconSchema, AnalyticsResponse,
)
from app.utils.jwt_utils import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Students CRUD ─────────────────────────────────────────────────────────────

@router.get("/students", summary="List all students")
def list_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "roll_no": s.roll_no,
            "department": s.department,
            "year": s.year,
            "section": s.section,
            "email": s.email,
            "is_face_registered": s.is_face_registered,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in students
    ]


@router.post("/students", status_code=status.HTTP_201_CREATED, summary="Create a student account")
def create_student(payload: StudentSchema, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.roll_no == payload.roll_no).first():
        raise HTTPException(status_code=400, detail="Student with this roll number already exists")
    if db.query(Student).filter(Student.email == str(payload.email)).first():
        raise HTTPException(status_code=400, detail="Student with this email already exists")

    student = Student(
        name=payload.name,
        roll_no=payload.roll_no,
        department=payload.department,
        year=payload.year,
        section=payload.section,
        email=str(payload.email),
        password_hash=hash_password("Student@123"),
        is_face_registered=False,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"message": "Student created successfully", "id": student.id}


@router.put("/students/{student_id}", summary="Update a student")
def update_student(student_id: int, payload: StudentSchema, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.name = payload.name
    student.roll_no = payload.roll_no
    student.department = payload.department
    student.year = payload.year
    student.section = payload.section
    student.email = str(payload.email)
    db.commit()
    return {"message": "Student updated successfully"}


@router.delete("/students/{student_id}", summary="Delete a student")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}


# ── Faculty CRUD ──────────────────────────────────────────────────────────────

@router.get("/faculty", summary="List all faculty")
def list_faculty(db: Session = Depends(get_db)):
    faculty_list = db.query(Faculty).all()
    return [
        {"id": f.id, "name": f.name, "email": f.email, "department": f.department}
        for f in faculty_list
    ]


@router.post("/faculty", status_code=status.HTTP_201_CREATED, summary="Create a faculty account")
def create_faculty(payload: FacultySchema, db: Session = Depends(get_db)):
    if db.query(Faculty).filter(Faculty.email == str(payload.email)).first():
        raise HTTPException(status_code=400, detail="Faculty with this email already exists")
    faculty = Faculty(
        name=payload.name,
        email=str(payload.email),
        password_hash=hash_password("Faculty@123"),
        department=payload.department,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return {"message": "Faculty created. Default password: Faculty@123", "id": faculty.id}


@router.put("/faculty/{faculty_id}", summary="Update a faculty member")
def update_faculty(faculty_id: int, payload: FacultySchema, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    faculty.name = payload.name
    faculty.email = str(payload.email)
    faculty.department = payload.department
    db.commit()
    return {"message": "Faculty updated successfully"}


@router.delete("/faculty/{faculty_id}", summary="Delete a faculty member")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty deleted successfully"}


# ── Subjects CRUD ─────────────────────────────────────────────────────────────

@router.get("/subjects", response_model=List[SubjectSchema], summary="List all subjects")
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/subjects", response_model=SubjectSchema, status_code=status.HTTP_201_CREATED, summary="Create a subject")
def create_subject(payload: SubjectSchema, db: Session = Depends(get_db)):
    if payload.subject_code:
        if db.query(Subject).filter(Subject.subject_code == payload.subject_code).first():
            raise HTTPException(status_code=400, detail="Subject code already exists")
    subject = Subject(
        subject_name=payload.subject_name,
        subject_code=payload.subject_code,
        department=payload.department,
        year=payload.year,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectSchema, summary="Update a subject")
def update_subject(subject_id: int, payload: SubjectSchema, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject.subject_name = payload.subject_name
    subject.subject_code = payload.subject_code
    subject.department = payload.department
    subject.year = payload.year
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", summary="Delete a subject")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted successfully"}


# ── Classrooms CRUD ───────────────────────────────────────────────────────────

@router.get("/classrooms", response_model=List[ClassroomSchema], summary="List all classrooms")
def list_classrooms(db: Session = Depends(get_db)):
    return db.query(Classroom).all()


@router.post("/classrooms", response_model=ClassroomSchema, status_code=status.HTTP_201_CREATED, summary="Create a classroom")
def create_classroom(payload: ClassroomSchema, db: Session = Depends(get_db)):
    if db.query(Classroom).filter(Classroom.room_name == payload.room_name).first():
        raise HTTPException(status_code=400, detail="Classroom already exists")
    room = Classroom(
        room_name=payload.room_name,
        building=payload.building,
        capacity=payload.capacity,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/classrooms/{classroom_id}", response_model=ClassroomSchema, summary="Update a classroom")
def update_classroom(classroom_id: int, payload: ClassroomSchema, db: Session = Depends(get_db)):
    room = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Classroom not found")
    room.room_name = payload.room_name
    room.building = payload.building
    room.capacity = payload.capacity
    db.commit()
    db.refresh(room)
    return room


@router.delete("/classrooms/{classroom_id}", summary="Delete a classroom")
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    room = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Classroom not found")
    db.delete(room)
    db.commit()
    return {"message": "Classroom deleted successfully"}


# ── BLE Beacons CRUD ──────────────────────────────────────────────────────────

@router.get("/beacons", response_model=List[BeaconSchema], summary="List all BLE beacons")
def list_beacons(db: Session = Depends(get_db)):
    return db.query(BleBeacon).all()


@router.post("/beacons", response_model=BeaconSchema, status_code=status.HTTP_201_CREATED, summary="Register a BLE beacon")
def create_beacon(payload: BeaconSchema, db: Session = Depends(get_db)):
    if db.query(BleBeacon).filter(BleBeacon.uuid == payload.uuid).first():
        raise HTTPException(status_code=400, detail="Beacon with this UUID already exists")
    beacon = BleBeacon(
        classroom_id=payload.classroom_id,
        uuid=payload.uuid,
        device_name=payload.device_name,
        rssi_threshold=payload.rssi_threshold,
        is_active=payload.is_active,
    )
    db.add(beacon)
    db.commit()
    db.refresh(beacon)
    return beacon


@router.put("/beacons/{beacon_id}", response_model=BeaconSchema, summary="Update a beacon")
def update_beacon(beacon_id: int, payload: BeaconSchema, db: Session = Depends(get_db)):
    beacon = db.query(BleBeacon).filter(BleBeacon.id == beacon_id).first()
    if not beacon:
        raise HTTPException(status_code=404, detail="Beacon not found")
    beacon.uuid = payload.uuid
    beacon.device_name = payload.device_name
    beacon.rssi_threshold = payload.rssi_threshold
    beacon.is_active = payload.is_active
    db.commit()
    db.refresh(beacon)
    return beacon


@router.delete("/beacons/{beacon_id}", summary="Delete a beacon")
def delete_beacon(beacon_id: int, db: Session = Depends(get_db)):
    beacon = db.query(BleBeacon).filter(BleBeacon.id == beacon_id).first()
    if not beacon:
        raise HTTPException(status_code=404, detail="Beacon not found")
    db.delete(beacon)
    db.commit()
    return {"message": "Beacon deleted successfully"}


# ── Analytics Dashboard ───────────────────────────────────────────────────────

@router.get("/analytics", response_model=AnalyticsResponse, summary="System-wide analytics")
def get_analytics(db: Session = Depends(get_db)):
    students_count = db.query(Student).count()
    faculty_count = db.query(Faculty).count()
    classrooms_count = db.query(Classroom).count()
    active_sessions = db.query(AttendanceSession).filter(AttendanceSession.is_active == True).count()

    total_records = db.query(Attendance).count()
    present_records = db.query(Attendance).filter(Attendance.attendance_status == "present").count()
    rate = round(float(present_records / total_records) * 100.0, 2) if total_records > 0 else 0.0

    face_reg_count = db.query(Student).filter(Student.is_face_registered == True).count()

    return AnalyticsResponse(
        total_students=students_count,
        total_faculty=faculty_count,
        total_classrooms=classrooms_count,
        active_sessions=active_sessions,
        total_attendance_records=total_records,
        attendance_rate=rate,
        face_registered_count=face_reg_count,
    )
