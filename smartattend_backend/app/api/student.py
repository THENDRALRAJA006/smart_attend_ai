from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.models import Student, AttendanceSession
from app.schemas.schemas import StudentSchema, StudentRegister, SessionResponse, LoginResponse, TokenSchema, UserProfileSchema
from app.dependencies import get_current_student
from app.utils.jwt_utils import hash_password, create_access_token

router = APIRouter(prefix="/students", tags=["students"])

# Keep backwards compatibility aliases by supporting the old prefixes
old_router = APIRouter(prefix="/student", tags=["student"])

@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@old_router.post("/register/student", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)  # Alias
def register_student(payload: StudentRegister, db: Session = Depends(get_db)):
    email_check = db.query(Student).filter(Student.email == payload.email).first()
    if email_check:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    roll_check = db.query(Student).filter(Student.roll_number == payload.roll_number).first()
    if roll_check:
        raise HTTPException(status_code=400, detail="Roll number already registered")
        
    new_student = Student(
        full_name=payload.full_name,
        roll_number=payload.roll_number,
        department=payload.department,
        year=payload.year,
        section=payload.section,
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    token_str = create_access_token({"sub": new_student.id}, role="student")
    return LoginResponse(
        token=TokenSchema(access_token=token_str, token_type="bearer", role="student"),
        user=UserProfileSchema(id=new_student.id, name=new_student.full_name, email=new_student.email)
    )

@router.get("", response_model=List[StudentSchema])
def list_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return [
        StudentSchema(
            id=s.id,
            name=s.full_name,
            roll_no=s.roll_number,
            department=s.department,
            year=s.year,
            section=s.section,
            email=s.email,
            is_face_registered=s.face_embeddings is not None and len(s.face_embeddings) > 0
        )
        for s in students
    ]

@router.get("/{id}", response_model=StudentSchema)
def get_student_by_id(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentSchema(
        id=student.id,
        name=student.full_name,
        roll_no=student.roll_number,
        department=student.department,
        year=student.year,
        section=student.section,
        email=student.email,
        is_face_registered=student.face_embeddings is not None and len(student.face_embeddings) > 0
    )

@router.put("/{id}", response_model=StudentSchema)
def update_student(id: int, payload: StudentSchema, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update fields
    student.full_name = payload.name
    student.roll_number = payload.roll_no
    student.department = payload.department
    student.year = payload.year
    student.section = payload.section
    student.email = payload.email
    
    db.commit()
    db.refresh(student)
    return StudentSchema(
        id=student.id,
        name=student.full_name,
        roll_no=student.roll_number,
        department=student.department,
        year=student.year,
        section=student.section,
        email=student.email,
        is_face_registered=student.face_embeddings is not None and len(student.face_embeddings) > 0
    )

@router.delete("/{id}")
def delete_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}

# --- Profile Endpoints (Preserved Functionality) ---
@old_router.get("/profile", response_model=StudentSchema)
def get_student_profile(current_student: Student = Depends(get_current_student)):
    return StudentSchema(
        id=current_student.id,
        name=current_student.full_name,
        roll_no=current_student.roll_number,
        department=current_student.department,
        year=current_student.year,
        section=current_student.section,
        email=current_student.email,
        is_face_registered=current_student.face_embeddings is not None and len(current_student.face_embeddings) > 0
    )

@old_router.get("/classes", response_model=List[SessionResponse])
def get_student_classes(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    sessions = db.query(AttendanceSession).all()
    return sessions
