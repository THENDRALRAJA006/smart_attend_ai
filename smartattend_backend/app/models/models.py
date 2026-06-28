"""
SmartAttend AI — SQLAlchemy ORM Models (PostgreSQL / Supabase)

Master-embedding architecture:
  - Each student stores ONE 512-dim ArcFace master embedding (pgvector).
  - No images or multi-row embedding galleries are stored.
  - Similarity search uses pgvector's native cosine distance operator.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time,
    Float, ForeignKey, Enum, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector


from app.database.database import Base


# ── Students ─────────────────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    roll_no = Column(String(20), unique=True, nullable=False)
    department = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    section = Column(String(10), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_face_registered = Column(Boolean, default=False)

    # ── Biometric Master Embedding ────────────────────────────────────────────
    master_embedding = Column(Vector(512), nullable=True)
    embedding_version = Column(String(20), nullable=True)
    embedding_quality_score = Column(Float, nullable=True)
    embedding_updated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attendances = relationship(
        "Attendance", back_populates="student",
        cascade="all, delete-orphan"
    )
    liveness_tokens = relationship(
        "LivenessToken", back_populates="student",
        cascade="all, delete-orphan"
    )


# ── Faculty ──────────────────────────────────────────────────────────────────
class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship(
        "AttendanceSession", back_populates="faculty",
        cascade="all, delete-orphan"
    )


# ── Admins ───────────────────────────────────────────────────────────────────
class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)


# ── Subjects ─────────────────────────────────────────────────────────────────
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_name = Column(String(100), nullable=True)
    subject_code = Column(String(20), unique=True, nullable=True)
    department = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)


# ── Classrooms ───────────────────────────────────────────────────────────────
class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_name = Column(String(50), unique=True, nullable=False)
    building = Column(String(50), nullable=True)
    capacity = Column(Integer, nullable=True)

    # Relationships
    beacons = relationship(
        "BleBeacon", back_populates="classroom",
        cascade="all, delete-orphan"
    )
    sessions = relationship(
        "AttendanceSession", back_populates="classroom_rel"
    )


# ── BLE Beacons ──────────────────────────────────────────────────────────────
class BleBeacon(Base):
    __tablename__ = "ble_beacons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    classroom_id = Column(
        Integer, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False
    )
    uuid = Column(String(100), unique=True, nullable=False)
    device_name = Column(String(100), nullable=True)
    rssi_threshold = Column(Integer, default=-70)
    is_active = Column(Boolean, default=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="beacons")


# ── Attendance Sessions ───────────────────────────────────────────────────────
class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(
        Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    classroom_id = Column(
        Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True
    )
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    qr_token = Column(String(255), nullable=True)
    qr_expires_at = Column(DateTime, nullable=True)

    # Legacy fields for backwards compatibility
    subject_name = Column(String(100), nullable=True)
    classroom = Column(String(50), nullable=True)
    session_code = Column(String(50), unique=True, nullable=True)

    # Relationships
    faculty = relationship("Faculty", back_populates="sessions")
    subject_rel = relationship("Subject")
    classroom_rel = relationship("Classroom", back_populates="sessions", foreign_keys=[classroom_id])
    attendances = relationship(
        "Attendance", back_populates="session",
        cascade="all, delete-orphan"
    )


# ── Attendance Records ────────────────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    session_id = Column(
        Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False
    )
    classroom_id = Column(
        Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    similarity_score = Column(Float, nullable=True)
    attendance_status = Column(
        Enum("present", "manual_review", "rejected", name="attendance_status_enum"),
        default="present"
    )
    liveness_verified = Column(Boolean, default=False)
    marked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="attendances")
    session = relationship("AttendanceSession", back_populates="attendances")

    __table_args__ = (
        UniqueConstraint("student_id", "session_id", name="no_duplicate_attendance"),
    )


# ── Liveness Tokens ──────────────────────────────────────────────────────────
class LivenessToken(Base):
    __tablename__ = "liveness_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(255), unique=True, nullable=False)
    challenge = Column(
        Enum("blink", "smile", "turn_left", "turn_right", name="liveness_challenge_enum"),
        nullable=False
    )
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="liveness_tokens")


# ── Backwards-compatibility aliases ──────────────────────────────────────────
AttendanceRecord = Attendance
Session = AttendanceSession
