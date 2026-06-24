"""
SmartAttend AI — Pydantic Schemas (Request / Response models)
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, time
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Auth & Profiles
# ─────────────────────────────────────────────────────────────────────────────

class StudentRegister(BaseModel):
    full_name: str = Field(..., max_length=100, alias="name")
    roll_number: str = Field(..., max_length=20, alias="roll_no")
    department: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = None
    section: Optional[str] = Field(None, max_length=10)
    email: EmailStr
    password: str = Field(..., min_length=6)

    model_config = {"populate_by_name": True}


class FacultyRegister(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    department: Optional[str] = Field(None, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    role: str


class UserProfileSchema(BaseModel):
    id: int
    name: str
    email: str


class LoginResponse(BaseModel):
    token: TokenSchema
    user: UserProfileSchema


# ─────────────────────────────────────────────────────────────────────────────
# Face Registration & Status
# ─────────────────────────────────────────────────────────────────────────────

class FaceStatusResponse(BaseModel):
    is_face_registered: bool
    embedding_count: int


class FaceRegisterPayload(BaseModel):
    """SDK path: pre-computed embedding from a client-side model."""
    student_id: int
    embedding: List[float]
    pose_name: Optional[str] = None


class FaceVerifyPayload(BaseModel):
    """SDK path: pre-computed embedding for verification."""
    student_id: int
    session_id: int
    embedding: List[float]
    verification_method: str = "face"


class FaceVerifyResponse(BaseModel):
    verified: bool
    similarity_score: float
    message: str
    attendance_record: Optional[dict] = None


# ─────────────────────────────────────────────────────────────────────────────
# Liveness
# ─────────────────────────────────────────────────────────────────────────────

class LivenessChallengeResponse(BaseModel):
    token: str
    challenge: str
    expires_at: datetime


class LivenessVerifyResponse(BaseModel):
    verified: bool
    liveness_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    subject_name: Optional[str] = Field(None, max_length=100)
    classroom: Optional[str] = Field(None, max_length=50)
    session_code: Optional[str] = Field(None, max_length=50)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    subject_id: Optional[int] = None
    classroom_id: Optional[int] = None


class SessionResponse(BaseModel):
    id: int
    faculty_id: int
    subject_name: Optional[str] = None
    classroom: Optional[str] = None
    session_code: Optional[str] = None
    is_active: bool = True
    start_time: datetime
    end_time: Optional[datetime] = None
    qr_token: Optional[str] = None
    qr_expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Attendance
# ─────────────────────────────────────────────────────────────────────────────

class AttendanceMark(BaseModel):
    student_id: int
    session_id: int
    status: str = Field("present", description="present | manual_review | rejected")
    verification_method: str = Field(..., description="face | qr | manual")


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    session_id: int
    attendance_status: str
    liveness_verified: bool = False
    similarity_score: Optional[float] = None
    marked_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Admin / Metadata
# ─────────────────────────────────────────────────────────────────────────────

class StudentSchema(BaseModel):
    id: Optional[int] = None
    name: str
    roll_no: str
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    email: EmailStr
    is_face_registered: Optional[bool] = False

    model_config = {"from_attributes": True}


class FacultySchema(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr
    department: Optional[str] = None

    model_config = {"from_attributes": True}


class SubjectSchema(BaseModel):
    id: Optional[int] = None
    subject_name: str
    subject_code: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None

    model_config = {"from_attributes": True}


class ClassroomSchema(BaseModel):
    id: Optional[int] = None
    room_name: str
    building: Optional[str] = None
    capacity: Optional[int] = None

    model_config = {"from_attributes": True}


class BeaconSchema(BaseModel):
    id: Optional[int] = None
    classroom_id: int
    uuid: str
    device_name: Optional[str] = None
    rssi_threshold: int = -70
    is_active: bool = True

    model_config = {"from_attributes": True}


class AnalyticsResponse(BaseModel):
    total_students: int
    total_faculty: int
    total_classrooms: int
    active_sessions: int
    total_attendance_records: int
    attendance_rate: float
    face_registered_count: int
