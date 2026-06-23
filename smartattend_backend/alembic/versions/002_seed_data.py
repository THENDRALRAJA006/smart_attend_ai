"""seed_data

Revision ID: 002
Revises: 001
Create Date: 2026-06-23 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import bcrypt
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def upgrade() -> None:
    faculty_hash = hash_password("Faculty@123")
    student_hash = hash_password("Student@123")

    # 1. Insert default Faculty
    op.execute(
        sa.text(
            f"INSERT INTO faculty (name, employee_id, email, password_hash) VALUES "
            f"('Dr. Sarah Connor', 'FAC-CS-101', 'faculty@smartattend.ai', '{faculty_hash}')"
        )
    )

    # 2. Insert default Student
    op.execute(
        sa.text(
            f"INSERT INTO students (full_name, roll_number, department, year, section, email, password_hash, face_embeddings) VALUES "
            f"('John Doe', 'CS-2026-101', 'Computer Science', 3, 'A', 'student@smartattend.ai', '{student_hash}', '[]')"
        )
    )

    # 3. Insert default Classroom
    op.execute(
        sa.text(
            "INSERT INTO classrooms (room_name, building, capacity) VALUES "
            "('ROOM101', 'Science Block', 60)"
        )
    )

    # 4. Insert default BLE Beacon (linked to ROOM101)
    op.execute(
        sa.text(
            "INSERT INTO ble_beacons (classroom_id, uuid, device_name, rssi_threshold, is_active) VALUES "
            "((SELECT id FROM classrooms WHERE room_name = 'ROOM101' LIMIT 1), "
            "'FDA5EDD4-C2EF-47F1-8FF5-3D3271F3637F', 'ESP32-ROOM101', -75, true)"
        )
    )

    # 5. Insert default Active Session
    # Set start_time to now (UTC) and end_time to +3 hours for convenience
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=3)
    
    start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

    op.execute(
        sa.text(
            f"INSERT INTO sessions (faculty_id, subject_name, classroom, session_code, start_time, end_time) VALUES "
            f"((SELECT id FROM faculty LIMIT 1), 'Artificial Intelligence', 'ROOM101', 'SESS-AI-301', '{start_str}', '{end_str}')"
        )
    )

def downgrade() -> None:
    op.execute(sa.text("DELETE FROM ble_beacons"))
    op.execute(sa.text("DELETE FROM classrooms"))
    op.execute(sa.text("DELETE FROM sessions"))
    op.execute(sa.text("DELETE FROM students"))
    op.execute(sa.text("DELETE FROM faculty"))

