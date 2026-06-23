from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    roll_number = Column(String(50), unique=True, nullable=False)
    department = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    section = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attendances = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    face_embeddings = relationship("FaceEmbedding", back_populates="student", cascade="all, delete-orphan")
    liveness_tokens = relationship("LivenessToken", back_populates="student", cascade="all, delete-orphan")

class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Relationships
    sessions = relationship("AttendanceSession", back_populates="faculty", cascade="all, delete-orphan")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_name = Column(String(50), unique=True, nullable=False)
    building = Column(String(50), nullable=True)
    capacity = Column(Integer, nullable=True)

    # Relationships
    beacons = relationship("BleBeacon", back_populates="classroom", cascade="all, delete-orphan")

class BleBeacon(Base):
    __tablename__ = "ble_beacons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    uuid = Column(String(100), unique=True, nullable=False)
    device_name = Column(String(100), nullable=True)
    rssi_threshold = Column(Integer, default=-70)
    is_active = Column(Boolean, default=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="beacons")

class AttendanceSession(Base):
    __tablename__ = "sessions"  # keep table name as 'sessions' to preserve existing migration mapping

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    subject_name = Column(String(100), nullable=False)
    classroom = Column(String(50), nullable=False)
    session_code = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Relationships
    faculty = relationship("Faculty", back_populates="sessions")
    attendances = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    __tablename__ = "attendance"  # keep table name as 'attendance' to preserve existing migration mapping

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="present")  # present, manual_review, rejected
    verification_method = Column(String(50), nullable=False)  # face, qr, manual
    similarity_score = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="attendances")
    session = relationship("AttendanceSession", back_populates="attendances")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    embedding = Column(JSON, nullable=False)  # Stored as JSON list of 512 floats
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="face_embeddings")

class LivenessToken(Base):
    __tablename__ = "liveness_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    challenge = Column(String(50), nullable=False)  # blink, smile, turn_left, turn_right
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="liveness_tokens")

# Backwards compatibility aliases
Session = AttendanceSession
Attendance = AttendanceRecord
