"""
SmartAttend AI — Authentication Router

Endpoints:
  POST /auth/student/register  → create student account
  POST /auth/student/login     → student JWT
  POST /auth/faculty/login     → faculty JWT
  POST /auth/admin/login       → admin JWT
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Student, Faculty, Admin
from app.schemas.schemas import (
    StudentRegister, LoginRequest, LoginResponse,
    TokenSchema, UserProfileSchema,
)
from app.utils.jwt_utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])


# ── Student Registration ──────────────────────────────────────────────────────

@router.post(
    "/student/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
def register_student(payload: StudentRegister, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    roll = payload.roll_number
    if db.query(Student).filter(Student.roll_no == roll).first():
        raise HTTPException(status_code=400, detail="Roll number already registered")

    new_student = Student(
        name=payload.full_name,
        roll_no=roll,
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


# ── Student Login ─────────────────────────────────────────────────────────────

@router.post(
    "/student/login",
    response_model=LoginResponse,
    summary="Student login — returns JWT",
)
@router.post("/login/student", response_model=LoginResponse, include_in_schema=False)
def login_student(payload: LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == str(payload.email)).first()
    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token_str = create_access_token({"sub": student.id}, role="student")
    return LoginResponse(
        token=TokenSchema(access_token=token_str, token_type="bearer", role="student"),
        user=UserProfileSchema(id=student.id, name=student.name, email=student.email),
    )


# ── Faculty Login ─────────────────────────────────────────────────────────────

@router.post(
    "/faculty/login",
    response_model=LoginResponse,
    summary="Faculty login — returns JWT",
)
@router.post("/login/faculty", response_model=LoginResponse, include_in_schema=False)
def login_faculty(payload: LoginRequest, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.email == str(payload.email)).first()
    if not faculty or not verify_password(payload.password, faculty.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token_str = create_access_token({"sub": faculty.id}, role="faculty")
    return LoginResponse(
        token=TokenSchema(access_token=token_str, token_type="bearer", role="faculty"),
        user=UserProfileSchema(id=faculty.id, name=faculty.name or "Faculty", email=faculty.email),
    )


# ── Admin Login ───────────────────────────────────────────────────────────────

@router.post(
    "/admin/login",
    response_model=LoginResponse,
    summary="Admin login — returns JWT (8 h expiry)",
)
@router.post("/login/admin", response_model=LoginResponse, include_in_schema=False)
def login_admin(payload: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == str(payload.email)).first()

    # Seed-admin fallback (no DB record required for first deploy)
    if not admin:
        if (
            str(payload.email) == "admin@smartattend.ai"
            and payload.password == "Admin@2026"
        ):
            token_str = create_access_token({"sub": 0}, role="admin")
            return LoginResponse(
                token=TokenSchema(access_token=token_str, token_type="bearer", role="admin"),
                user=UserProfileSchema(id=0, name="System Admin", email="admin@smartattend.ai"),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token_str = create_access_token({"sub": admin.id}, role="admin")
    return LoginResponse(
        token=TokenSchema(access_token=token_str, token_type="bearer", role="admin"),
        user=UserProfileSchema(
            id=admin.id,
            name=admin.name or "Admin",
            email=admin.email,
        ),
    )
