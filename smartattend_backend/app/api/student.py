"""
SmartAttend AI — Student Router

Endpoints:
  POST /students/register          → create student account
  GET  /students                   → list all students
  GET  /students/{id}              → get student profile
  PUT  /students/{id}              → update student profile
  DELETE /students/{id}            → delete student
  GET  /student/profile            → authenticated student's own profile
  GET  /student/classes            → list all active sessions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.models import Student, AttendanceSession
from app.schemas.schemas import (
    StudentSchema, StudentRegister, SessionResponse,
    LoginResponse, TokenSchema, UserProfileSchema,
)
from app.dependencies import get_current_student
from app.utils.jwt_utils import hash_password, create_access_token

router = APIRouter(prefix="/students", tags=["students"])
old_router = APIRouter(prefix="/student", tags=["student"])


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student",
)
@old_router.post("/register/student", response_model=LoginResponse, status_code=201, include_in_schema=False)
def register_student(payload: StudentRegister, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == str(payload.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(Student).filter(Student.roll_no == payload.roll_number).first():
        raise HTTPException(status_code=400, detail="Roll number already registered")

    new_student = Student(
        name=payload.full_name,
        roll_no=payload.roll_number,
        department=payload.department,
        year=payload.year,
        section=payload.section,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        is_face_registered=False,
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    token_str = create_access_token({"sub": new_student.id}, role="student")
    return LoginResponse(
        token=TokenSchema(access_token=token_str, token_type="bearer", role="student"),
        user=UserProfileSchema(id=new_student.id, name=new_student.name, email=new_student.email),
    )


@router.get("", response_model=List[StudentSchema])
def list_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return [
        StudentSchema(
            id=s.id, name=s.name, roll_no=s.roll_no,
            department=s.department, year=s.year, section=s.section,
            email=s.email, is_face_registered=s.is_face_registered,
        )
        for s in students
    ]


@router.get("/{student_id}", response_model=StudentSchema)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentSchema(
        id=student.id, name=student.name, roll_no=student.roll_no,
        department=student.department, year=student.year, section=student.section,
        email=student.email, is_face_registered=student.is_face_registered,
    )


@router.put("/{student_id}", response_model=StudentSchema)
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
    db.refresh(student)
    return StudentSchema(
        id=student.id, name=student.name, roll_no=student.roll_no,
        department=student.department, year=student.year, section=student.section,
        email=student.email, is_face_registered=student.is_face_registered,
    )


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}


# ── Authenticated student's own profile and session list ─────────────────────

@old_router.get("/profile", response_model=StudentSchema)
def get_student_profile(current_student: Student = Depends(get_current_student)):
    return StudentSchema(
        id=current_student.id, name=current_student.name, roll_no=current_student.roll_no,
        department=current_student.department, year=current_student.year,
        section=current_student.section, email=current_student.email,
        is_face_registered=current_student.is_face_registered,
    )


@old_router.get("/classes", response_model=List[SessionResponse])
def get_student_classes(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    sessions = db.query(AttendanceSession).filter(AttendanceSession.is_active == True).all()
    return sessions
