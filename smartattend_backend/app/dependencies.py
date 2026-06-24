from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.utils.jwt_utils import decode_access_token
from app.models.models import Student, Faculty, Admin

security = HTTPBearer()


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate Bearer token and return decoded payload."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing",
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )
    return payload


def get_current_student(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Student:
    """Dependency that returns the authenticated Student record."""
    if payload.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Students only",
        )
    student_id = payload.get("sub")
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return student


def get_current_faculty(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Faculty:
    """Dependency that returns the authenticated Faculty record."""
    if payload.get("role") != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Faculty only",
        )
    faculty_id = payload.get("sub")
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty member not found",
        )
    return faculty


def get_current_admin(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Admin:
    """Dependency that returns the authenticated Admin record."""
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admins only",
        )
    admin_id = payload.get("sub")
    # sub == 0 is the seed admin (created via fallback in auth.py)
    if admin_id == 0:
        return Admin(id=0, email="admin@smartattend.ai", name="System Admin")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    return admin
