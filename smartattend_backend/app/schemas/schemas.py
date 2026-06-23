from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional

# --- Authentication & Profiles ---
class StudentRegister(BaseModel):
    full_name: str = Field(..., max_length=100)
    roll_number: str = Field(..., max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    section: Optional[str] = Field(None, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)

class FacultyRegister(BaseModel):
    name: str = Field(..., max_length=100)
    employee_id: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

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
    email: EmailStr

class LoginResponse(BaseModel):
    token: TokenSchema
    user: UserProfileSchema

# --- Face Status ---
class FaceStatusResponse(BaseModel):
    is_face_registered: bool
    embedding_count: int

# --- Face SDK API Payloads ---
class FaceRegisterPayload(BaseModel):
    student_id: int
    embedding: List[float]

class FaceVerifyPayload(BaseModel):
    student_id: int
    session_id: int
    embedding: List[float]
    verification_method: str = "face"

class FaceVerifyResponse(BaseModel):
    verified: bool
    similarity_score: float
    message: str
    attendance_record: Optional[dict] = None

# --- Liveness Challenges ---
class LivenessChallengeResponse(BaseModel):
    token: str
    challenge: str
    expires_at: datetime

class LivenessVerifyResponse(BaseModel):
    verified: bool
    liveness_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str

# --- Sessions ---
class SessionCreate(BaseModel):
    subject_name: str = Field(..., max_length=100)
    classroom: str = Field(..., max_length=50)
    session_code: str = Field(..., max_length=50)
    start_time: datetime
    end_time: datetime

class SessionResponse(BaseModel):
    id: int
    faculty_id: int
    subject_name: str
    classroom: str
    session_code: str
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True

# --- Attendance ---
class AttendanceMark(BaseModel):
    student_id: int
    session_id: int
    status: str = Field("present", description="present, manual_review, or rejected")
    verification_method: str = Field(..., description="face, qr, or manual")

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    session_id: int
    status: str
    verification_method: str
    similarity_score: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Admin & Metadata ---
class StudentSchema(BaseModel):
    id: Optional[int] = None
    name: str
    roll_no: str
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    email: EmailStr
    is_face_registered: Optional[bool] = False

    class Config:
        from_attributes = True

class FacultySchema(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr
    department: Optional[str] = None

    class Config:
        from_attributes = True

class ClassroomSchema(BaseModel):
    id: Optional[int] = None
    room_name: str
    building: Optional[str] = None
    capacity: Optional[int] = None

    class Config:
        from_attributes = True

class BeaconSchema(BaseModel):
    id: Optional[int] = None
    classroom_id: int
    uuid: str
    device_name: Optional[str] = None
    rssi_threshold: int = -70
    is_active: bool = True

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    total_students: int
    total_faculty: int
    total_classrooms: int
    active_sessions: int
    attendance_rate: float
